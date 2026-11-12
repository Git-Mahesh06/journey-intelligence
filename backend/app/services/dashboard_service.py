
from sqlalchemy import text


def get_dashboard_summary(conn):

    result = conn.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM sessions) AS total_sessions,

            (SELECT COUNT(*) FROM journey_events) AS total_events,

            (
                SELECT COUNT(*)
                FROM journey_outcomes
                WHERE outcome_type = 'converted'
            ) AS total_conversions,

            (
                SELECT COUNT(*)
                FROM anomaly_records
            ) AS total_anomalies,

            (
                SELECT COUNT(*)
                FROM anomaly_records
                WHERE resolution_status = 'open'
            ) AS open_anomalies,

            (
                SELECT COALESCE(SUM(total_amount), 0)
                FROM orders
                WHERE payment_status = 'success'
            ) AS total_revenue
    """)).mappings().one()

    sessions = result["total_sessions"]

    conversion_rate = (
        result["total_conversions"] / sessions * 100
        if sessions else 0
    )

    return {
        "total_sessions": sessions,
        "total_events": result["total_events"],
        "total_conversions": result["total_conversions"],
        "conversion_rate": round(conversion_rate, 2),
        "total_anomalies": result["total_anomalies"],
        "open_anomalies": result["open_anomalies"],
        "total_revenue": float(result["total_revenue"]),
    }


def get_anomalies(conn, issue_type=None, limit=100):

    query = """
        SELECT
            anomaly_id,
            session_id,
            event_id,
            issue_type,
            severity,
            detection_reason,
            detection_rule,
            resolution_status
        FROM anomaly_records
        WHERE (:issue_type IS NULL OR issue_type = :issue_type)
        ORDER BY detected_at DESC
        LIMIT :limit
    """

    rows = conn.execute(
        text(query),
        {
            "issue_type": issue_type,
            "limit": limit,
        }
    ).mappings().all()

    return [dict(row) for row in rows]


def get_funnel(conn):

    rows = conn.execute(text("""
        SELECT outcome_type, COUNT(*) AS session_count
        FROM journey_outcomes
        GROUP BY outcome_type
    """)).mappings().all()

    counts = {
        row["outcome_type"]: row["session_count"]
        for row in rows
    }

    total = sum(counts.values())

    stages = [
        ("browse_only", counts.get("browse_only", 0)),
        ("abandoned", counts.get("abandoned", 0)),
        ("support_contact", counts.get("support_contact", 0)),
        ("converted", counts.get("converted", 0)),
    ]

    return [
        {
            "stage": stage,
            "sessions": count,
            "conversion_percentage": round(
                count / total * 100, 2
            ) if total else 0,
        }
        for stage, count in stages
    ]
