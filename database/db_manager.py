from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Event, ParserMetadata
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from utils.logger import logger


class DBManager:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create_tables(self):
        """Recreate all tables for fresh start."""
        # Base.metadata.drop_all(self.engine)  # Drop existing tables
        Base.metadata.create_all(self.engine)  # Create fresh schema

    def check_event_exists(self, title):
        """Check if an event with the same title and date exists in the database."""
        try:
            event = self.session.query(Event).filter_by(title=title).first()
            if event:
                return True
            return False
        except Exception as e:
            print(f"Failed to check event existence: {e}")
            return False

    def get_last_parsed_date(self, parser_name):
        """Retrieve the last parsed date for a parser."""
        metadata = self.session.query(ParserMetadata).filter_by(parser_name=parser_name).first()
        return metadata.last_parsed_date if metadata else None

    def update_last_parsed_date(self, parser_name, last_parsed_date):
        """Update the last parsed date for a parser."""
        metadata = self.session.query(ParserMetadata).filter_by(parser_name=parser_name).first()
        if not metadata:
            metadata = ParserMetadata(parser_name=parser_name, last_parsed_date=last_parsed_date)
            self.session.add(metadata)
        else:
            metadata.last_parsed_date = last_parsed_date
        self.session.commit()

    def add_event(self, event):
        """Add a new event to the database if no matching title."""
        if self.check_event_exists(event.title):
            print(f"Skipped duplicate event: {event.title}")
            return
        self.session.add(event)
        self.session.commit()
        logger.info(f"Added event: {event.title}")

    def archive_event(self, event_id):
        """Mark an event as archived."""
        try:
            event = self.session.query(Event).filter_by(id=event_id).first()
            if not event:
                print(f"Event with ID {event_id} not found.")
                return False
            event.archived = True
            self.session.commit()
            logger.info(f"Event with ID {event_id} marked as archived.")
            return True
        except Exception as e:
            print(f"Failed to archive event: {e}")
            self.session.rollback()
            return False

    def archive_events(self):
        """Archive events where all associated dates are in the past."""
        try:
            # Find events where all associated dates are in the past
            now = datetime.now()

            events_to_archive = (
                self.session.query(Event)
                .options(joinedload(Event.dates))
                .filter(Event.archived == False)
                .all()
            )

            count = 0
            for event in events_to_archive:
                # Check if all associated dates are in the past
                if all((event_date.end_date if event_date.end_date else event_date.date) < now for event_date in event.dates):
                    event.archived = True
                    count += 1

            self.session.commit()
            logger.info(f"{count} events archived.")
            return True
        except Exception as e:
            print(f"Failed to archive events: {e}")
            self.session.rollback()
            return False

    def get_all_events(self):
        """Retrieve all events from the database."""
        return self.session.query(Event).all()

    def get_active_events(self):
        """Retrieve all events that are not archived."""
        return self.session.query(Event).filter_by(archived=False).all()

    def close(self):
        """Close the database session."""
        self.session.close()
