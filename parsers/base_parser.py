from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def fetch_data(self):
        """Fetch all data from the target source."""
        pass

    @abstractmethod
    def parse_event(self, item):
        """Parse a single event item and return a structured object."""
        pass
