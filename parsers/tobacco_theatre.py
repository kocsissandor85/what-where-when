import requests
from bs4 import BeautifulSoup
from datetime import datetime
from database.models import Event, EventDate
from parsers.base_parser import BaseParser
from database.db_manager import DBManager
from utils.config import DATABASE_URL
import json

class TobaccoTheatreParser(BaseParser):
    BASE_URL = "https://tobaccotheater.nl/tobacco-tickets-agenda/"

    def __init__(self):
        self.db_manager = DBManager(DATABASE_URL)

    def fetch_data(self):
        """Fetch all events"""
        events = []
        response = requests.get(self.BASE_URL)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            event_items = soup.find_all('div', class_='evo_event_schema')

            if not event_items:
                print("No events found.")
            else:
                for item in event_items:
                    event = self.parse_event(item)

                    if event:
                        # Check if the event already exists
                        if self.db_manager.check_event_exists(event.title):
                            print(f"Event already exists: {event.title}. Stopping parser.")
                            return events  # Stop parsing
                        events.append(event)

                return events
        else:
            print(f"Failed to fetch agenda page. Status code: {response.status_code}")

    def parse_event(self, item):
        """Parse event details from the given HTML."""
        try:
            # Extract primary fields from itemprop attributes
            url = item.find('a', itemprop='url')['href']
            json_ld_script = item.find('script', type='application/ld+json').get_text(strip=True).replace('\t', '').replace('\n', '').replace('\r', '')

            if json_ld_script:
                json_ld_data = json.loads(json_ld_script)

                title = json_ld_data.get('name')
                description = json_ld_data.get('description')
                start_date = self._parse_iso_datetime(json_ld_data.get('startDate'))
                end_date_json = json_ld_data.get('endDate')
                end_date = self._parse_iso_datetime(end_date_json)
                image_url = json_ld_data.get('image')
                location_name = json_ld_data.get('location', {}).get('name')
                address = json_ld_data.get('location', {}).get('address')

                event = Event(
                    title=title,
                    description=description.replace(title, '').strip(),
                    location=f"{location_name}, {address}",
                    url=url,
                    media_url=image_url
                )

                event.dates = [
                    EventDate(
                        date=start_date.date(),
                        end_date=end_date.date() if end_date.date() != start_date.date() else None,
                        time=start_date.time().strftime("%H:%M"),
                        end_time=end_date.time().strftime("%H:%M") if end_date.date() != start_date.date() else None
                    )
                ]

                return event
        except Exception as e:
            print(f"Failed to parse event: {e}")
            return None


    @staticmethod
    def _parse_iso_datetime(date_str):
        """Parse an ISO 8601 datetime string into date and time components."""
        try:
            format_str = "%Y-%m-%dT%f-%H-%M-%S"
            return datetime.strptime(date_str, format_str)
        except Exception:
            raise ValueError(f"Invalid date format: {date_str}")