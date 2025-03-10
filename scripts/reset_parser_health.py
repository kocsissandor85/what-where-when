import os
import sys

# Add the parent directory to the Python path so we can import modules from there
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, MetaData
from database.models import Base, ParserHealth
from utils.config import DATABASE_URL

def reset_parser_health_table():
    # Connect to the database
    engine = create_engine(DATABASE_URL)

    # Create a metadata instance
    metadata = MetaData()

    # Reflect the table structure
    metadata.reflect(bind=engine, only=['parser_health'])

    # Drop the table if it exists
    if 'parser_health' in metadata.tables:
        print("Dropping existing parser_health table...")
        metadata.tables['parser_health'].drop(engine)
        print("Table dropped.")

    # Create the table with the correct schema
    print("Creating parser_health table with the correct schema...")
    ParserHealth.__table__.create(engine)
    print("Table created successfully.")

if __name__ == "__main__":
    reset_parser_health_table()