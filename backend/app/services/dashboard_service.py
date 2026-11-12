
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

    query = text("""
        WITH session_events AS (
            SELECT
                session_id,

                MIN(event_timestamp) FILTER (
                    WHERE event_type = 'session_started'
                ) AS started,

                MIN(event_timestamp) FILTER (
                    WHERE event_type = 'product_view'
                ) AS viewed,

                MIN(event_timestamp) FILTER (
                    WHERE event_type = 'add_to_cart'
                ) AS cart,

                MIN(event_timestamp) FILTER (
                    WHERE event_type = 'cart_view'
                ) AS cart_viewed,

                MIN(event_timestamp) FILTER (
                    WHERE event_type = 'checkout_started'
                ) AS checkout,

                MIN(event_timestamp) FILTER (
                    WHERE event_type = 'payment_initiated'
                ) AS payment,

                MIN(event_timestamp) FILTER (
                    WHERE event_type = 'payment_success'
                ) AS success

            FROM journey_events
            GROUP BY session_id
        ),

        valid_stages AS (
            SELECT
                session_id,

                started IS NOT NULL AS stage_1,

                (
                    started IS NOT NULL
                    AND viewed >= started
                ) AS stage_2,

                (
                    started IS NOT NULL
                    AND viewed >= started
                    AND cart >= viewed
                ) AS stage_3,

                (
                    started IS NOT NULL
                    AND viewed >= started
                    AND cart >= viewed
                    AND cart_viewed >= cart
                ) AS stage_4,

                (
                    started IS NOT NULL
                    AND viewed >= started
                    AND cart >= viewed
                    AND cart_viewed >= cart
                    AND checkout >= cart_viewed
                ) AS stage_5,

                (
                    started IS NOT NULL
                    AND viewed >= started
                    AND cart >= viewed
                    AND cart_viewed >= cart
                    AND checkout >= cart_viewed
                    AND payment >= checkout
                ) AS stage_6,

                (
                    started IS NOT NULL
                    AND viewed >= started
                    AND cart >= viewed
                    AND cart_viewed >= cart
                    AND checkout >= cart_viewed
                    AND payment >= checkout
                    AND success >= payment
                ) AS stage_7

            FROM session_events
        )

        SELECT
            COUNT(*) FILTER (WHERE stage_1) AS stage_1,
            COUNT(*) FILTER (WHERE stage_2) AS stage_2,
            COUNT(*) FILTER (WHERE stage_3) AS stage_3,
            COUNT(*) FILTER (WHERE stage_4) AS stage_4,
            COUNT(*) FILTER (WHERE stage_5) AS stage_5,
            COUNT(*) FILTER (WHERE stage_6) AS stage_6,
            COUNT(*) FILTER (WHERE stage_7) AS stage_7

        FROM valid_stages
    """)

    counts = conn.execute(query).mappings().one()

    definitions = [
        ("Session Started", "stage_1"),
        ("Product Viewed", "stage_2"),
        ("Added to Cart", "stage_3"),
        ("Cart Viewed", "stage_4"),
        ("Checkout Started", "stage_5"),
        ("Payment Initiated", "stage_6"),
        ("Payment Successful", "stage_7"),
    ]

    result = []
    previous_count = None
    total_sessions = counts["stage_1"]

    for index, (stage_name, key) in enumerate(definitions, start=1):

        current_count = counts[key]

        if previous_count is None:
            conversion_from_previous = 100.0
            dropoff_sessions = 0
            dropoff_percentage = 0.0

        else:
            conversion_from_previous = (
                round(current_count / previous_count * 100, 2)
                if previous_count else 0.0
            )

            dropoff_sessions = previous_count - current_count

            dropoff_percentage = (
                round(dropoff_sessions / previous_count * 100, 2)
                if previous_count else 0.0
            )

        overall_conversion = (
            round(current_count / total_sessions * 100, 2)
            if total_sessions else 0.0
        )

        result.append({
            "stage": stage_name,
            "stage_order": index,
            "sessions": current_count,
            "conversion_percentage": overall_conversion,
            "conversion_from_previous": conversion_from_previous,
            "dropoff_sessions": dropoff_sessions,
            "dropoff_percentage": dropoff_percentage,
        })

        previous_count = current_count

    return result

