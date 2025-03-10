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
        """Parse a single event item into an Event object."""
        # Extract basic event details
        title_element = item.find('h2', class_='title')
        if not title_element:
            raise ValueError("Missing title element")

        title = title_element.get_text(strip=True)

        description = item.find('div', class_='tagline')
        description_text = description.get_text(strip=True) if description else None

        location = item.find('div', class_='location')
        location_text = location.get_text(strip=True) if location else "Frascati, Amsterdam"

        url_element = item.find('a', class_='desc')
        if not url_element or 'href' not in url_element.attrs:
            raise ValueError(f"Missing URL for event: {title}")

        relative_url = url_element['href']
        url = f"https://www.frascatitheater.nl{relative_url}"

        # Parse dates and times
        datetime_section = item.find('div', class_='datetime')
        if not datetime_section:
            raise ValueError(f"Missing datetime section for event: {title}")

        event_dates = self._parse_dates(datetime_section)
        if not event_dates:
            raise ValueError(f"No valid dates found for event: {title}")

        # Parse media (image) URL
        media_url = self._parse_media_url(item)

        # Create the event object
        event = Event(
            title=title,
            description=description_text,
            location=location_text,
            url=url,
            media_url=media_url
        )

        # Link dates to the event
        event.dates = event_dates

        return event

    def _parse_dates(self, datetime_section):
        """Extract all dates and times from the datetime section."""
        dates = []

        # Get start date
        start_element = datetime_section.find('div', class_='start')
        if not start_element:
            raise ValueError("Missing start date element")

        start_date_raw = start_element.get_text(strip=True)
        start_date = self._parse_date(start_date_raw)

        # Check for separator (indicating multiple dates or a date range)
        separator = datetime_section.find('div', class_='separator')
        if separator:
            separator_text = separator.get_text(strip=True)
            end_element = datetime_section.find('div', class_='end')

            if not end_element:
                raise ValueError("Missing end date element in a multi-date event")

            end_date_raw = end_element.get_text(strip=True)
            end_date = self._parse_date(end_date_raw)

            # Handle multiple single dates (separated by "en")
            if separator_text == "en":
                dates.append(EventDate(date=start_date))
                dates.append(EventDate(date=end_date))

            # Handle date range (separated by "-")
            elif separator_text == "-":
                dates.append(EventDate(date=start_date, end_date=end_date))

            else:
                raise ValueError(f"Unknown separator type: {separator_text}")
        else:
            # Handle single date (possibly with time)
            time_element = datetime_section.find('span', class_='start')
            time = time_element.get_text(strip=True) if time_element else None
            dates.append(EventDate(date=start_date, time=time))

        return dates

    def _parse_date(self, date_str):
        """Parse Dutch date format into a Python datetime object."""
        if not date_str:
            raise ValueError("Empty date string")

        # Translate Dutch abbreviations to English
        date_str = date_str.replace('’', "'")  # Normalize apostrophes

        translations = {
            "ma": "Mon", "di": "Tue", "wo": "Wed", "do": "Thu", "vr": "Fri", "za": "Sat", "zo": "Sun",
            "jan": "Jan", "feb": "Feb", "mrt": "Mar", "apr": "Apr", "mei": "May", "jun": "Jun",
            "jul": "Jul", "aug": "Aug", "sep": "Sep", "okt": "Oct", "nov": "Nov", "dec": "Dec"
        }

        translated = date_str
        for dutch, english in translations.items():
            translated = translated.replace(dutch, english)

        # Fix the format string to match the actual date format
        try:
            # Try with two digit year: e.g., "Mon 11 Mar '25"
            return datetime.strptime(translated, "%a %d %b '%y")
        except ValueError:
            try:
                # Try without apostrophe: e.g., "Mon 11 Mar 25"
                return datetime.strptime(translated, "%a %d %b %y")
            except ValueError:
                # Try with four digit year: e.g., "Mon 11 Mar 2025"
                try:
                    return datetime.strptime(translated, "%a %d %b %Y")
                except ValueError:
                    # If all formats fail, raise an error
                    raise ValueError(f"Could not parse date: '{date_str}' (translated to '{translated}')")

    def _parse_media_url(self, item):
        """Extract media URL from event item."""
        # Look for the thumbnail image
        thumb = item.find('div', class_='thumb')
        if not thumb:
            return None

        # Extract URL from inline style
        style = item.find('style')
        if not style:
            return None

        style_text = style.get_text(strip=True)
        pattern_url = r'\.thumb \.image.*?background-image: url\((.*?)\);'
        match_url = re.search(pattern_url, style_text, re.DOTALL)

        if match_url:
            return match_url.group(1).strip("'")

        return None