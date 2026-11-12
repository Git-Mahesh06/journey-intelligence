
from app.db.database import engine
from sqlalchemy import inspect
import json

inspector = inspect(engine)

print("\n========== DATABASE SCHEMA INSPECTION ==========\n")

tables = sorted(inspector.get_table_names())

for table in tables:
    print(f"\n{'=' * 60}")
    print(f"TABLE: {table}")
    print("=" * 60)

    print("\nCOLUMNS:")
    for column in inspector.get_columns(table):
        print({
            "name": column["name"],
            "type": str(column["type"]),
            "nullable": column["nullable"],
            "default": str(column.get("default"))
        })

    print("\nPRIMARY KEY:")
    print(inspector.get_pk_constraint(table))

    print("\nFOREIGN KEYS:")
    print(json.dumps(
        inspector.get_foreign_keys(table),
        indent=2,
        default=str
    ))

    print("\nUNIQUE CONSTRAINTS:")
    print(json.dumps(
        inspector.get_unique_constraints(table),
        indent=2,
        default=str
    ))

    print("\nINDEXES:")
    print(json.dumps(
        inspector.get_indexes(table),
        indent=2,
        default=str
    ))

print("\n========== INSPECTION COMPLETED ==========")
