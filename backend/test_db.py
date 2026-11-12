
from app.db.database import test_connection

try:
    result = test_connection()
    print("PostgreSQL connection successful!")
    print("Database:", result[0])
    print("User:", result[1])
except Exception as error:
    print("Database connection failed!")
    print(error)
