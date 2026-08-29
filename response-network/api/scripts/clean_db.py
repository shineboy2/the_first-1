import sys
from sqlalchemy import create_engine, text

def main():
    """Clean up the alembic_version table and existing tables."""
    DATABASE_URL = "postgresql+psycopg://user:password@127.0.0.1:5432/response_db"
    
    # Create an engine
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        # Drop tables in correct order
        with connection.begin():
            connection.execute(text("DROP TABLE IF EXISTS requests CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        print("Successfully cleaned up the database.")

if __name__ == "__main__":
    main()