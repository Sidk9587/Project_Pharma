from sqlalchemy import text

from app.database.database import engine


try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.fetchone()

        print("DATABASE CONNECTION SUCCESSFUL")
        print(version[0])

except Exception as e:
    print("DATABASE CONNECTION FAILED")
    print(e)