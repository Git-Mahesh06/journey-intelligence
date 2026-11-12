
from sqlalchemy import text, bindparam

from app.db.database import engine



def validate_primary_keys(connection):
    """Validate complete primary-key combinations, including composite keys."""

    issues = []

    tables = connection.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
    """)).scalars().all()

    for table in tables:
        primary_keys = connection.execute(
            text("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = 'public'
                  AND tc.table_name = :table_name
                  AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position
            """),
            {"table_name": table},
        ).scalars().all()

        if not primary_keys:
            continue

        columns = ", ".join(f'"{column}"' for column in primary_keys)

        null_condition = " OR ".join(
            f'"{column}" IS NULL' for column in primary_keys
        )

        null_count = connection.execute(text(f"""
            SELECT COUNT(*)
            FROM "{table}"
            WHERE {null_condition}
        """)).scalar_one()

        duplicate_count = connection.execute(text(f"""
            SELECT COUNT(*)
            FROM (
                SELECT {columns}
                FROM "{table}"
                GROUP BY {columns}
                HAVING COUNT(*) > 1
            ) duplicates
        """)).scalar_one()

        if duplicate_count or null_count:
            issues.append({
                "table": table,
                "primary_key_columns": primary_keys,
                "duplicate_count": duplicate_count,
                "null_count": null_count,
            })

    return issues



def validate_foreign_keys(connection):
    """Check all declared foreign-key relationships."""

    violations = []

    foreign_keys = connection.execute(text("""
        SELECT
            tc.table_name AS child_table,
            kcu.column_name AS child_column,
            ccu.table_name AS parent_table,
            ccu.column_name AS parent_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
    """)).mappings().all()

    for fk in foreign_keys:
        child = fk["child_table"]
        child_col = fk["child_column"]
        parent = fk["parent_table"]
        parent_col = fk["parent_column"]

        orphan_count = connection.execute(text(f"""
            SELECT COUNT(*)
            FROM "{child}" c
            LEFT JOIN "{parent}" p
              ON c."{child_col}" = p."{parent_col}"
            WHERE c."{child_col}" IS NOT NULL
              AND p."{parent_col}" IS NULL
        """)).scalar_one()

        if orphan_count:
            violations.append({
                "child_table": child,
                "child_column": child_col,
                "parent_table": parent,
                "orphan_count": orphan_count,
            })

    return violations

def validate_timestamps(connection):
    """Check timestamp ordering and session/event consistency."""

    checks = {
        "session_end_before_start": """
            SELECT COUNT(*) FROM sessions
            WHERE ended_at IS NOT NULL
              AND ended_at < started_at
        """,
        "event_ingested_before_occurrence": """
            SELECT COUNT(*) FROM journey_events
            WHERE ingestion_timestamp < event_timestamp
        """,
        "event_before_session_start": """
            SELECT COUNT(*)
            FROM journey_events e
            JOIN sessions s ON e.session_id = s.session_id
            WHERE e.event_timestamp < s.started_at
        """,
        "event_after_session_end": """
            SELECT COUNT(*)
            FROM journey_events e
            JOIN sessions s ON e.session_id = s.session_id
            WHERE s.ended_at IS NOT NULL
              AND e.event_timestamp > s.ended_at
        """,
        "identity_link_end_before_start": """
            SELECT COUNT(*) FROM identity_links
            WHERE valid_to IS NOT NULL
              AND valid_to < valid_from
        """,
        "support_resolution_before_creation": """
            SELECT COUNT(*) FROM support_tickets
            WHERE resolved_at IS NOT NULL
              AND resolved_at < created_at
        """,
    }

    issues = []

    for check_name, query in checks.items():
        count = connection.execute(text(query)).scalar_one()

        if count > 0:
            issues.append({
                "check": check_name,
                "invalid_records": count,
            })

    return issues


def validate_allowed_values(connection):
    """Validate categorical fields against supported domain values."""

    allowed_values = {
        "sessions": {
            "channel": ["web", "mobile_app"],
            "device_type": ["desktop", "mobile", "tablet"],
        },
        "journey_events": {
            "event_type": [
                "add_to_cart",
                "app_open",
                "cart_view",
                "checkout_started",
                "filter_applied",
                "page_view",
                "payment_failed",
                "payment_initiated",
                "payment_success",
                "product_view",
                "scroll",
                "search",
                "session_abandoned",
                "session_ended",
                "session_started",
                "support_contact",
            ],
            "channel": ["web", "mobile_app", "support", "purchase"],
        },
        "customers": {
            "consent_status": ["granted", "denied", "unknown"],
        },
        "identity_links": {
            "consent_status": ["granted", "denied", "unknown"],
        },
        "journey_outcomes": {
            "outcome_type": [
                "abandoned",
                "browse_only",
                "converted",
                "support_contact",
            ],
            "funnel_stage_reached": [
                "checkout",
                "product_discovery",
                "purchase",
                "support",
            ],
        },
        "anomaly_records": {
            "issue_type": [
                "bot_traffic",
                "duplicate_conversion",
                "out_of_order_event",
                "unauthorized_identity_link",
            ],
            "severity": ["high", "medium"],
        },
    }

    issues = []

    for table, columns in allowed_values.items():
        for column, allowed in columns.items():
            query = text(
                f'''
                SELECT COUNT(*)
                FROM "{table}"
                WHERE "{column}" IS NOT NULL
                  AND "{column}" NOT IN :allowed
                '''
            ).bindparams(
                bindparam("allowed", expanding=True)
            )

            invalid_count = connection.execute(
                query, {"allowed": allowed}
            ).scalar_one()

            if invalid_count > 0:
                issues.append({
                    "table": table,
                    "column": column,
                    "invalid_records": invalid_count,
                    "allowed_values": allowed,
                })

    return issues

def validate_business_rules(connection):
    """Validate consistency between journey outcomes and source records."""

    checks = {
        "converted_without_payment_success": """
            SELECT COUNT(*)
            FROM journey_outcomes o
            WHERE o.outcome_type = 'converted'
              AND NOT EXISTS (
                  SELECT 1
                  FROM journey_events e
                  WHERE e.session_id = o.session_id
                    AND e.event_type = 'payment_success'
              )
        """,

        "payment_success_without_converted_outcome": """
            SELECT COUNT(DISTINCT e.session_id)
            FROM journey_events e
            JOIN journey_outcomes o
              ON o.session_id = e.session_id
            WHERE e.event_type = 'payment_success'
              AND o.outcome_type != 'converted'
        """,

        "duplicate_conversion_without_duplicate_events": """
            SELECT COUNT(*)
            FROM anomaly_records a
            WHERE a.issue_type = 'duplicate_conversion'
              AND NOT EXISTS (
                  SELECT 1
                  FROM journey_events e
                  WHERE e.session_id = a.session_id
                    AND e.event_type = 'payment_success'
                  GROUP BY e.session_id
                  HAVING COUNT(*) > 1
              )
        """,

        "unauthorized_identity_without_rejected_link": """
            SELECT COUNT(*)
            FROM anomaly_records a
            JOIN sessions s
              ON s.session_id = a.session_id
            WHERE a.issue_type = 'unauthorized_identity_link'
              AND NOT EXISTS (
                  SELECT 1
                  FROM identity_links i
                  WHERE i.anonymous_id = s.anonymous_id
                    AND i.consent_status = 'denied'
                    AND i.link_status = 'rejected'
              )
        """,
    }

    issues = []

    for check_name, query in checks.items():
        invalid_count = connection.execute(
            text(query)
        ).scalar_one()

        if invalid_count > 0:
            issues.append({
                "check": check_name,
                "invalid_records": invalid_count,
            })

    return issues

def run_validation():
    """Run initial database integrity checks without modifying data."""
    
    with engine.connect() as connection:
        business_rule_issues = validate_business_rules(connection)
        allowed_value_issues = validate_allowed_values(connection)
        pk_issues = validate_primary_keys(connection)
        fk_issues = validate_foreign_keys(connection)
        timestamp_issues = validate_timestamps(connection)

        report = {
    "primary_key_issues": pk_issues,
    "foreign_key_violations": fk_issues,
    "timestamp_issues": timestamp_issues,
    "allowed_value_issues": allowed_value_issues,
    "business_rule_issues": business_rule_issues,
    "passed": not (
        pk_issues
        or fk_issues
        or timestamp_issues
        or allowed_value_issues
    ),
}

    return report


if __name__ == "__main__":
    import json

    print(json.dumps(run_validation(), indent=4))
