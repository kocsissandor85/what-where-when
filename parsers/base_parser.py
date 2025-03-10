from abc import ABC, abstractmethod
from datetime import datetime
import traceback
from database.models import ParserHealth, Tag, ParserTag
from utils.logger import logger


class BaseParser(ABC):
    # Add display_name class variable with default value
    display_name = "Generic Parser"

    # Add automatic_tags class variable for venue-specific tags
    automatic_tags = []  # List of tag names to automatically apply to all events

    @classmethod
    def get_automatic_tags(cls):
        """Get the list of automatic tags for this parser."""
        return cls.automatic_tags

    @classmethod
    def get_parser_name(cls):
        """Get the name of the parser class."""
        return cls.__name__

    @abstractmethod
    def fetch_data(self):
        """Fetch all data from the target source."""
        pass

    @abstractmethod
    def parse_event(self, item):
        """Parse a single event item and return a structured object."""
        pass

    def apply_automatic_tags(self, event, db_session):
        """Apply automatic venue tags to the event."""
        if not self.automatic_tags:
            return

        for tag_name in self.automatic_tags:
            # Get or create the tag
            tag = db_session.query(Tag).filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db_session.add(tag)
                db_session.flush()  # Flush to get the tag ID

                # Associate tag with parser for future reference
                parser_tag = ParserTag(parser_name=self.get_parser_name(), tag_id=tag.id)
                db_session.add(parser_tag)

            # Add tag to the event if not already present
            if tag not in event.tags:
                event.tags.append(tag)

    def run_with_error_handling(self, db_session):
        """
        Run the parser with error handling and health logging.

        Args:
            db_session: Database session to use for logging health status

        Returns:
            List of parsed events or empty list on failure
        """
        parser_name = self.__class__.__name__
        events = []
        success = True
        error_message = None

        try:
            logger.info(f"Running parser: {parser_name}")
            events = self.fetch_data()

            # Apply automatic tags to all events
            for event in events:
                self.apply_automatic_tags(event, db_session)

            logger.info(f"Parser {parser_name} completed successfully. Found {len(events)} events.")
        except Exception as e:
            success = False
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Parser {parser_name} failed with error: {e}")
            logger.error(f"Stack trace: {stack_trace}")

        # Log parser health
        health_record = ParserHealth(
            parser_name=parser_name,
            display_name=self.display_name,  # Add display_name to the health record
            last_run=datetime.now(),
            success=success,
            events_parsed=len(events),
            error_message=error_message
        )

        try:
            db_session.add(health_record)
            db_session.commit()
        except Exception as e:
            logger.error(f"Failed to log parser health: {e}")
            db_session.rollback()

        return events