
from app.db.database import test_connection as check_database_connection


def test_postgres_connection():
    result = check_database_connection()

    assert result is not None
    assert result[0] == "journey_intelligence"
    assert result[1] == "logistics_user"

    print("PostgreSQL connection successful!")
