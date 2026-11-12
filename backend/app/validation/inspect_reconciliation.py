
from sqlalchemy import text
from app.db.database import engine

query = text("""
    SELECT
        a.anomaly_id,
        a.session_id,
        s.anonymous_id AS session_anonymous_id,
        i.link_id,
        i.anonymous_id AS link_anonymous_id,
        i.customer_id,
        i.consent_status,
        i.link_status,
        i.decision_reason
    FROM anomaly_records a
    JOIN sessions s
        ON s.session_id = a.session_id
    LEFT JOIN identity_links i
        ON i.anonymous_id = s.anonymous_id
    WHERE a.issue_type = 'unauthorized_identity_link'
    ORDER BY a.session_id
""")

with engine.connect() as connection:
    rows = connection.execute(query).mappings().all()

    for row in rows:
        print(dict(row))

    print(f"\nTotal matching records: {len(rows)}")
