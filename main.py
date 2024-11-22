import argparse
from parsers.parser_manager import ParserManager
from database.db_manager import DBManager
from utils.config import DATABASE_URL
from utils.logger import logger


def main():
    # CLI Argument Parsing
    parser = argparse.ArgumentParser(description="Run parsers to fetch events.")
    parser.add_argument("--parser", nargs="+", help="Specific parsers to run. Leave empty to run all.")
    args = parser.parse_args()

    # Initialize database manager
    db_manager = DBManager(DATABASE_URL)
    db_manager.create_tables()

    # Archive events older than today
    db_manager.archive_events()

    # Initialize parser manager
    parser_manager = ParserManager()
    parser_manager.auto_register_parsers()

    if args.parser:
        # Run specific parsers
        all_events = []
        for parser_name in args.parser:
            specific_parser = parser_manager.get_parser(parser_name)
            if specific_parser:
                logger.info(f"Running specific parser: {parser_name}")
                events = specific_parser.fetch_data()
                all_events.extend(events)
            else:
                logger.warning(f"Parser '{parser_name}' not found.")

    else:
        # Run all parsers
        logger.info("Running all parsers...")
        all_events = parser_manager.run_all_parsers()

    # Insert events into the database
    for event in all_events:
        db_manager.add_event(event)

    logger.info(f"Inserted {len(all_events)} events into the database.")
    db_manager.close()


if __name__ == "__main__":
    main()
