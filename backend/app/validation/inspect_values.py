
from sqlalchemy import text
from app.db.database import engine

tables = {
    "sessions": ["channel", "device_type", "lifecycle_state"],
    "journey_events": ["event_type", "channel"],
    "customers": ["consent_status"],
    "identity_links": ["consent_status", "link_status"],
    "journey_outcomes": ["outcome_type", "funnel_stage_reached"],
    "anomaly_records": ["issue_type", "severity", "resolution_status"],
}

with engine.connect() as connection:
    for table, columns in tables.items():
        print(f"\n{table}")

        for column in columns:
            query = text(
                f"""
                SELECT DISTINCT "{column}"
                FROM "{table}"
                ORDER BY "{column}" NULLS FIRST
                """
            )

            values = connection.execute(query).scalars().all()

            print(f"  {column}: {values}")
