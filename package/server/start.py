import os
import sys
import subprocess
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

from dotenv import load_dotenv

if not os.path.exists('./data'):
    os.mkdir('./data')
load_dotenv('./data/.env')
def main():
    print("Starting application initialization...")

    from railway import start
    start.create_database()

    # 1. Check environment variable DATABASE_URL
    database_url = os.environ.get("DB_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable is not set.")
        print("Please set DATABASE_URL (e.g., postgresql://user:password@host:5432/dbname)")
        sys.exit(1)

    is_db_exists = False
    # 2. Check connection and create DB if needed
    try:
        url = make_url(database_url)
        db_name = url.database

        # We need to connect to the 'postgres' database to check/create the target database
        # Create a copy of the URL but with 'postgres' as the database
        postgres_url = url.set(database='postgres')

        print(f"Connecting to database server at {url.host}...")

        # Connect to default 'postgres' database
        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")

        with engine.connect() as conn:
            print("Successfully connected to database server.")

            # Check if target database exists
            # Use text() for raw SQL
            query = text("SELECT 1 FROM pg_database WHERE datname = :name")
            result = conn.execute(query, {"name": db_name}).scalar()

            if not result:
                print(f"Database '{db_name}' does not exist. Creating...")
                # Cannot use parameters for database name in CREATE DATABASE
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"Database '{db_name}' created successfully.")
            else:
                is_db_exists = True
                print(f"Database '{db_name}' already exists.")

        engine.dispose()

        # 3. Connect to the target database to enable vector extension
        print(f"Connecting to target database '{db_name}'...")
        target_engine = create_engine(database_url, isolation_level="AUTOCOMMIT")
        with target_engine.connect() as conn:
             print("Enabling 'vector' extension if not exists...")
             conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
             print("'vector' extension enabled.")
        target_engine.dispose()

    except Exception as e:
        print(f"Error during database initialization: {e}")
        print("Ensure the database server is running and reachable.")
        sys.exit(1)
    if is_db_exists:
        # 4. Run Alembic migrations
        print("Running Alembic migrations...")
        try:
            subprocess.run(["alembic", "upgrade", "head"], check=True)
            print("Alembic migrations completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Alembic migration failed with exit code {e.returncode}")
        except FileNotFoundError:
            print("Error: 'alembic' command not found. Ensure it is installed and in PATH.")
            sys.exit(1)

    # 5. Start application
    print("Starting uvicorn...")
    # Using execvp to replace the current process with uvicorn
    # This ensures uvicorn receives signals (like SIGTERM) directly
    try:
        # Arguments must be passed as a list, starting with the program name
        sys.stdout.flush()
        os.execvp("uvicorn", ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])
    except OSError as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
