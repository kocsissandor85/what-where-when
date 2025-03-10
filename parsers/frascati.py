import requests
from bs4 import BeautifulSoup
from datetime import datetime
from database.models import Event, EventDate
from parsers.base_parser import BaseParser
from database.db_manager import DBManager
from utils.config import DATABASE_URL
import re


class FrascatiParser(BaseParser):
    BASE_URL = "https://www.frascatitheater.nl/nl/agenda"
    PAGINATION_PARAM = "?page="

    # Add human-readable display name
    display_name = "Frascati Theater"

    def __init__(self):
        self.db_manager = DBManager(DATABASE_URL)

    def fetch_data(self):
        """Fetch all event pages and parse event details."""
        page = 1
        events = []

        while True:
            print(f"Fetching page {page}...")
            url = f"{self.BASE_URL}{self.PAGINATION_PARAM}{page}"
            response = requests.get(url)

            if response.status_code != 200:
                print(f"Failed to fetch page {page}. Status code: {response.status_code}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            event_items = soup.find_all('li', class_='eventCard')

            if not event_items:
                print("No more events found. Stopping pagination.")
                break

            for item in event_items:
                event = self.parse_event(item)

                if event:
                    # Check if the event already exists
                    if self.db_manager.check_event_exists(event.title):
                        print(f"Event already exists: {event.title}. Stopping parser.")
                        return events  # Stop parsing further pages
                    events.append(event)

            page += 1

        return events

    def parse_event(self, item):
        """Parse a single event item."""
        try:
            title = item.find('h2', class_='title').get_text(strip=True)
            description = item.find('div', class_='tagline').get_text(strip=True) if item.find('div', class_='tagline') else None
            location = item.find('div', class_='location').get_text(strip=True) if item.find('div', class_='location') else "Frascati, Amsterdam"
            relative_url = item.find('a', class_='desc')['href']
            url = f"https://www.frascatitheater.nl{relative_url}"

            # Parse dates and times
            datetime_section = item.find('div', class_='datetime')
            event_dates = self._parse_dates(datetime_section)

            # Parse media (image or video)
            media_url = self._parse_media_url(item)

            # Create Event and associated EventDate objects
            event = Event(
                title=title,
                description=description,
                location=location,
                url=url,
                media_url=media_url
            )
            event.dates = event_dates  # Link parsed dates to the event

            return event
        except Exception as e:
            print(f"Failed to parse event: {e}")
            return None

    def _parse_dates(self, datetime_section):
        """Extract all dates and times from the datetime section."""
        dates = []
        try:
            # Start date
            start_date_raw = datetime_section.find('div', class_='start').get_text(strip=True)
            start_date = self._parse_date(start_date_raw)

            # Check for separator
            separator = datetime_section.find('div', class_='separator')
            if separator:
                separator_text = separator.get_text(strip=True)

                # Case 1: Multiple single dates (e.g., "do 21 nov '24 en vr 22 nov '24")
                if separator_text == "en":
                    end_date_raw = datetime_section.find('div', class_='end').get_text(strip=True)
                    end_date = self._parse_date(end_date_raw)

                    # Add each date as a separate EventDate
                    dates.append(EventDate(date=start_date))
                    dates.append(EventDate(date=end_date))

                # Case 2: Date interval (e.g., "di 2 apr '24 - vr 6 dec '24")
                elif separator_text == "-":
                    end_date_raw = datetime_section.find('div', class_='end').get_text(strip=True)
                    end_date = self._parse_date(end_date_raw)

                    # Add as a single EventDate with a start and end date
                    dates.append(EventDate(date=start_date, end_date=end_date))

            else:
                # Case 3: Single date with or without time
                time_section = datetime_section.find('span', class_='start')
                time = time_section.get_text(strip=True) if time_section else None
                dates.append(EventDate(date=start_date, time=time))

        except Exception as e:
            print(f"Failed to parse dates: {e}")
        return dates


    @staticmethod
    def _parse_date(date_raw):
        """Convert raw Dutch-style date string into a Python datetime object."""
        try:
            date_cleaned = date_raw.replace('’', "'")
            dutch_to_english = {
                "ma": "Mon", "di": "Tue", "wo": "Wed", "do": "Thu", "vr": "Fri", "za": "Sat", "zo": "Sun",
                "jan": "Jan", "feb": "Feb", "mrt": "Mar", "apr": "Apr", "mei": "May", "jun": "Jun",
                "jul": "Jul", "aug": "Aug", "sep": "Sep", "okt": "Oct", "nov": "Nov", "dec": "Dec"
            }
            for dutch, english in dutch_to_english.items():
                date_cleaned = date_cleaned.replace(dutch, english)
            return datetime.strptime(date_cleaned, "%a %d %b '%y")
        except Exception as e:
            print(f"Failed to parse date '{date_raw}': {e}")
            return None

    @staticmethod
    def _parse_media_url(item):
        """Extract the media URL from the event item."""
        try:
            # Check for the thumbnail
            thumb = item.find('div', class_='thumb')

            if thumb:
                style = item.find('style')
                style_text = style.get_text(strip=True)
                pattern_url = rf'\.thumb \.image.*?background-image: url\((.*?)\);'
                match_url = re.search(pattern_url, style_text, re.DOTALL)

                if match_url:
                    image_url = match_url.group(1).strip("'")
                    return image_url
        except Exception as e:
            print(f"Failed to extract media URL: {e}")
        return None
