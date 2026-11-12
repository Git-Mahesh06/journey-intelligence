
from sqlalchemy import text

from app.db.database import engine


# Map detected issue types to ground-truth scenario types.
SCENARIO_MAP = {
    "duplicate_conversion": "duplicate_conversion",
    "out_of_order_event": "out_of_order",
    "unauthorized_identity_link": "incorrect_identity_merge",
    "bot_traffic": "bot_traffic",
}


def save_anomalies(conn, anomalies):
    """
    Store anomalies in PostgreSQL.
    ON CONFLICT makes repeated runs safe.
    """

    if not anomalies:
        return

    query = text("""
        INSERT INTO anomaly_records (
            anomaly_id,
            session_id,
            event_id,
            issue_type,
            severity,
            detection_reason,
            detection_rule,
            resolution_status
        )
        VALUES (
            :anomaly_id,
            :session_id,
            :event_id,
            :issue_type,
            :severity,
            :detection_reason,
            :detection_rule,
            'open'
        )
        ON CONFLICT (anomaly_id)
        DO UPDATE SET
            detection_reason = EXCLUDED.detection_reason,
            severity = EXCLUDED.severity,
            detected_at = NOW()
    """)

    conn.execute(query, anomalies)


def detect_duplicate_conversions(conn):
    """
    Detect multiple payment_success events
    referencing the same order.
    """

    rows = conn.execute(text("""
        SELECT
            session_id,
            MAX(event_id) AS event_id,
            deduplication_key,
            COUNT(*) AS duplicate_count
        FROM journey_events
        WHERE event_type = 'payment_success'
          AND deduplication_key IS NOT NULL
        GROUP BY session_id, deduplication_key
        HAVING COUNT(*) > 1
    """)).mappings().all()

    anomalies = []

    for row in rows:
        anomalies.append({
            "anomaly_id": (
                f"ANOM-DUP-{row['session_id']}"
            ),
            "session_id": row["session_id"],
            "event_id": row["event_id"],
            "issue_type": "duplicate_conversion",
            "severity": "high",
            "detection_reason": (
                f"Found {row['duplicate_count']} payment events "
                f"with the same deduplication key: "
                f"{row['deduplication_key']}. "
                "The conversion should be counted only once."
            ),
            "detection_rule": "duplicate_payment_key_v1",
        })

    save_anomalies(conn, anomalies)

    return len(anomalies)


def detect_out_of_order_events(conn):
    """
    Detect events whose event timestamps do not
    follow chronological order when sorted by ingestion time.
    """

    rows = conn.execute(text("""
        WITH ordered_events AS (
            SELECT
                event_id,
                session_id,
                event_timestamp,
                ingestion_timestamp,

                LAG(event_timestamp) OVER (
                    PARTITION BY session_id
                    ORDER BY ingestion_timestamp, event_id
                ) AS previous_event_timestamp

            FROM journey_events
        )

        SELECT
            event_id,
            session_id,
            event_timestamp,
            ingestion_timestamp,
            previous_event_timestamp

        FROM ordered_events

        WHERE previous_event_timestamp IS NOT NULL
          AND event_timestamp < previous_event_timestamp
    """)).mappings().all()

    anomalies = []

    for row in rows:
        anomalies.append({
            "anomaly_id": (
                f"ANOM-ORDER-{row['session_id']}"
            ),
            "session_id": row["session_id"],
            "event_id": row["event_id"],
            "issue_type": "out_of_order_event",
            "severity": "medium",
            "detection_reason": (
                "Event timestamp is earlier than the preceding "
                "event when ordered by ingestion timestamp. "
                "Analytics should use event occurrence time."
            ),
            "detection_rule": "event_chronology_v1",
        })

    save_anomalies(conn, anomalies)

    return len(anomalies)


def detect_unauthorized_identity_links(conn):
    """
    Detect identity-link attempts where consent
    was denied or unknown.
    """

    rows = conn.execute(text("""
        SELECT
            s.session_id,
            il.customer_id,
            il.anonymous_id,
            il.consent_status,
            il.link_status

        FROM identity_links il

        JOIN sessions s
            ON s.anonymous_id = il.anonymous_id

        WHERE il.consent_status <> 'granted'
    """)).mappings().all()

    anomalies = []

    for row in rows:
        anomalies.append({
            "anomaly_id": (
                f"ANOM-IDENTITY-{row['session_id']}"
            ),
            "session_id": row["session_id"],
            "event_id": None,
            "issue_type": "unauthorized_identity_link",
            "severity": "high",
            "detection_reason": (
                f"Identity-link attempt for customer "
                f"{row['customer_id']} has consent status "
                f"{row['consent_status']} and link status "
                f"{row['link_status']}. "
                "Identity must not be linked without granted consent."
            ),
            "detection_rule": "identity_consent_v1",
        })

    save_anomalies(conn, anomalies)

    return len(anomalies)


def detect_bot_traffic(conn):
    """
    Detect sessions marked as bot candidates.
    """

    rows = conn.execute(text("""
        SELECT
            s.session_id,

            (
                SELECT e.event_id
                FROM journey_events e
                WHERE e.session_id = s.session_id
                ORDER BY e.event_timestamp, e.event_id
                LIMIT 1
            ) AS event_id

        FROM sessions s

        WHERE s.is_bot_candidate = TRUE
    """)).mappings().all()

    anomalies = []

    for row in rows:
        anomalies.append({
            "anomaly_id": (
                f"ANOM-BOT-{row['session_id']}"
            ),
            "session_id": row["session_id"],
            "event_id": row["event_id"],
            "issue_type": "bot_traffic",
            "severity": "medium",
            "detection_reason": (
                "Session contains a bot traffic signal. "
                "Exclude it from human customer journey metrics "
                "until reviewed."
            ),
            "detection_rule": "bot_signal_v1",
        })

    save_anomalies(conn, anomalies)

    return len(anomalies)


def detect_anomalies():
    """
    Run all four independent detection rules.
    """

    print("\nStarting anomaly detection...")

    with engine.begin() as conn:

        duplicate_count = detect_duplicate_conversions(conn)

        out_of_order_count = detect_out_of_order_events(conn)

        identity_count = detect_unauthorized_identity_links(conn)

        bot_count = detect_bot_traffic(conn)

    results = {
        "duplicate_conversion": duplicate_count,
        "out_of_order_event": out_of_order_count,
        "unauthorized_identity_link": identity_count,
        "bot_traffic": bot_count,
    }

    print("\nANOMALY DETECTION COMPLETE")
    print("--------------------------------")

    for issue, count in results.items():
        print(f"{issue}: {count}")

    print("--------------------------------")

    print(
        "Total anomalies detected:",
        sum(results.values())
    )

    return results


def evaluate_detection():
    """
    Compare detected anomalies against ground truth.

    Ground truth is used only for evaluation,
    never for anomaly detection.
    """

    print("\nEvaluating detection performance...")

    with engine.connect() as conn:

        truth_rows = conn.execute(text("""
            SELECT session_id, scenario_type
            FROM ground_truth
        """)).mappings().all()

        detected_rows = conn.execute(text("""
            SELECT session_id, issue_type
            FROM anomaly_records
        """)).mappings().all()

    expected = {
        (row["session_id"], row["scenario_type"])
        for row in truth_rows
    }

    detected = {
        (
            row["session_id"],
            SCENARIO_MAP[row["issue_type"]]
        )
        for row in detected_rows
        if row["issue_type"] in SCENARIO_MAP
    }

    true_positives = len(expected & detected)
    false_positives = len(detected - expected)
    false_negatives = len(expected - detected)

    precision = (
        true_positives / len(detected)
        if detected else 0
    )

    recall = (
        true_positives / len(expected)
        if expected else 0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    print("\nDETECTION EVALUATION")
    print("--------------------------------")
    print(f"Expected anomalies : {len(expected)}")
    print(f"Detected anomalies : {len(detected)}")
    print(f"True positives     : {true_positives}")
    print(f"False positives    : {false_positives}")
    print(f"False negatives    : {false_negatives}")
    print(f"Precision          : {precision:.2%}")
    print(f"Recall             : {recall:.2%}")
    print(f"F1 Score           : {f1_score:.2%}")
    print("--------------------------------")

    return {
        "expected": len(expected),
        "detected": len(detected),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
    }


if __name__ == "__main__":

    detect_anomalies()

    evaluate_detection()
