
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path

from sqlalchemy import inspect, text

from app.db.database import engine


# Export destination: backend/exports/
EXPORT_DIR = Path(__file__).resolve().parents[2] / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

BATCH_SIZE = 5000


def export_table_csv(connection, table):
    output_file = EXPORT_DIR / f"{table}.csv"

    result = connection.execute(text(f'SELECT * FROM "{table}"'))
    columns = list(result.keys())

    with output_file.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        while True:
            rows = result.mappings().fetchmany(BATCH_SIZE)
            if not rows:
                break

            writer.writerows([dict(row) for row in rows])

    return output_file


def export_table_json(connection, table):
    output_file = EXPORT_DIR / f"{table}.json"

    result = connection.execute(text(f'SELECT * FROM "{table}"'))

    with output_file.open("w", encoding="utf-8") as file:
        file.write("[\n")
        first_row = True

        while True:
            rows = result.mappings().fetchmany(BATCH_SIZE)
            if not rows:
                break

            for row in rows:
                if not first_row:
                    file.write(",\n")

                json.dump(dict(row), file, default=str, ensure_ascii=False)
                first_row = False

        file.write("\n]\n")

    return output_file


def export_sql():
    pg_dump = shutil.which("pg_dump")

    if not pg_dump:
        print("WARNING: pg_dump not found. SQL export skipped.")
        return False

    url = engine.url

    environment = os.environ.copy()

    if url.password:
        environment["PGPASSWORD"] = url.password

    command = [
        pg_dump,
        "--host", url.host or "localhost",
        "--port", str(url.port or 5432),
        "--username", url.username or "",
        "--dbname", url.database or "",
        "--format=plain",
        "--no-owner",
        "--no-privileges",
        "--file", str(EXPORT_DIR / "journey_intelligence.sql"),
    ]

    result = subprocess.run(
        command,
        env=environment,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("SQL export failed:")
        print(result.stderr)
        return False

    print("SQL database dump created.")
    return True


def main():
    print("\nStarting Journey Intelligence export...\n")

    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())

    manifest = {
        "database": engine.url.database,
        "tables": {},
        "total_rows": 0,
        "export_formats": ["CSV", "JSON"],
    }

    with engine.connect() as connection:

        for table in tables:
            print(f"Exporting: {table}")

            count = connection.execute(
                text(f'SELECT COUNT(*) FROM "{table}"')
            ).scalar_one()

            export_table_csv(connection, table)
            export_table_json(connection, table)

            manifest["tables"][table] = {
                "row_count": count,
                "csv_file": f"{table}.csv",
                "json_file": f"{table}.json",
            }

            manifest["total_rows"] += count

    sql_success = export_sql()

    if sql_success:
        manifest["export_formats"].append("SQL")

    manifest["sql_export_success"] = sql_success

    with (EXPORT_DIR / "manifest.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(manifest, file, indent=4)

    print("\n========== EXPORT COMPLETED ==========")
    print("Tables exported:", len(tables))
    print("Total rows:", manifest["total_rows"])
    print("Output directory:", EXPORT_DIR)
    print("SQL export:", "SUCCESS" if sql_success else "NOT COMPLETED")


if __name__ == "__main__":
    main()
