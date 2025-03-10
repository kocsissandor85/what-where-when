import os
import sys

# Add the parent directory to the Python path so we can import modules from there
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, MetaData
from database.models import Base
from utils.config import DATABASE_URL
from utils.logger import logger

def empty_database():
    """Remove all data from the database while preserving the schema."""
    try:
        # Connect to the database
        logger.info(f"Connecting to database: {DATABASE_URL}")
        engine = create_engine(DATABASE_URL)

        # Create a metadata instance
        metadata = MetaData()

        # Reflect the existing tables
        metadata.reflect(bind=engine)

        # Start a transaction
        connection = engine.connect()
        trans = connection.begin()

        # Delete all data from each table in reverse order to avoid foreign key constraints
        for table_name in reversed(metadata.sorted_tables):
            logger.info(f"Emptying table: {table_name}")
            connection.execute(table_name.delete())

        # Commit the transaction
        trans.commit()
        logger.info("Database emptied successfully")

    except Exception as e:
        logger.error(f"Error emptying database: {e}")
        if 'trans' in locals() and trans is not None:
            trans.rollback()
        raise
    finally:
        if 'connection' in locals() and connection is not None:
            connection.close()

def drop_and_recreate_database():
    """Drop all tables and recreate them from scratch."""
    try:
        # Connect to the database
        logger.info(f"Connecting to database: {DATABASE_URL}")
        engine = create_engine(DATABASE_URL)

        # Drop all tables
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(engine)

        # Recreate all tables
        logger.info("Recreating all tables...")
        Base.metadata.create_all(engine)

        logger.info("Database reset successfully")

    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Empty the database or drop and recreate all tables.")
    parser.add_argument('--reset', action='store_true', help='Drop and recreate all tables instead of just emptying them')

    args = parser.parse_args()

    if args.reset:
        print("WARNING: This will drop all tables and recreate them. All data will be lost.")
        confirmation = input("Are you sure you want to continue? (yes/no): ")

        if confirmation.lower() == 'yes':
            drop_and_recreate_database()
        else:
            print("Operation cancelled.")
    else:
        print("WARNING: This will empty all data from the database but keep the table structure.")
        confirmation = input("Are you sure you want to continue? (yes/no): ")

        if confirmation.lower() == 'yes':
            empty_database()
        else:
            print("Operation cancelled.")