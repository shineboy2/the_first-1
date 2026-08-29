from sqlalchemy import create_engine, text

def main():
    # Connect to default postgres database
    engine = create_engine('postgresql://postgres:password@localhost:5433/postgres')
    
    # Drop and create database
    with engine.connect() as conn:
        # We need to close all connections to the database before dropping it
        conn.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'response_db';"))
        conn.execute(text("DROP DATABASE IF EXISTS response_db;"))
        conn.execute(text("CREATE DATABASE response_db;"))
        print("Database dropped and recreated successfully!")

if __name__ == "__main__":
    main()