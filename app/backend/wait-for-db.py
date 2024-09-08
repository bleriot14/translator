import time
import psycopg2
from sqlalchemy import create_engine
import os

def wait_for_db(url, max_retries=5, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            engine = create_engine(url)
            connection = engine.connect()
            connection.close()
            print("Database is ready!")
            return True
        except psycopg2.OperationalError:
            retries += 1
            print(f"Database not ready. Retrying in {delay} seconds...")
            time.sleep(delay)
    print("Max retries reached. Could not connect to the database.")
    return False

if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL environment variable is not set.")
        exit(1)
    
    if wait_for_db(database_url):
        print("Starting the application...")
    else:
        print("Exiting due to database connection failure.")
        exit(1)