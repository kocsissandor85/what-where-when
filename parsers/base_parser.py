from abc import ABC, abstractmethod
from datetime import datetime
import traceback
from database.models import ParserHealth
from utils.logger import logger


class BaseParser(ABC):
    @abstractmethod
    def fetch_data(self):
        """Fetch all data from the target source."""
        pass

    @abstractmethod
    def parse_event(self, item):
        """Parse a single event item and return a structured object."""
        pass

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