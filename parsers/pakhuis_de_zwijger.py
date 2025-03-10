import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from database.models import Event, EventDate
from parsers.base_parser import BaseParser
from database.db_manager import DBManager
from utils.config import DATABASE_URL

import locale
locale.setlocale(locale.LC_TIME, "nl_NL.UTF-8")

class PakhuisDeZwijgerParser(BaseParser):
    BASE_URL = "https://dezwijger.nl/ajax/agenda/getItems"
    display_name = "Pakhuis de Zwijger"

    def __init__(self):
        self.db_manager = DBManager(DATABASE_URL)

    def fetch_data(self):
        """Fetch events using AJAX pagination."""
        today_str = datetime.today().strftime('%Y/%m/%d')
        page = 1
        events = []

        while True:
            print(f"Fetching page {page}...")
            response = requests.get(self.BASE_URL, params={"page": page, "prev_date": today_str})

            if response.status_code != 200:
                print(f"Failed to fetch page {page}. Status code: {response.status_code}")
                break

            data = response.json()
            total_pages = data.get("total_pages", 1)
            event_html = data.get("data", "")

            soup = BeautifulSoup(event_html, 'html.parser')
            event_items = soup.find_all('div', class_='program teaser')

            for item in event_items:
                event = self.parse_event(item)
                if event:
                    if self.db_manager.check_event_exists(event.title):
                        print(f"Event already exists: {event.title}. Skipping.")
                        continue
                    events.append(event)

            if page >= total_pages:
                break

            page += 1

        return events

    def parse_event(self, item):
        """Parse a single event item from HTML."""
        try:
            title = item.find('div', class_='title').get_text(strip=True)
            description = item.find('div', class_='subtitle').get_text(strip=True) if item.find('div', class_='subtitle') else ""
            date_time_raw = item.find('div', class_='date-time').get_text(strip=True)
            location = item.find('div', class_='location').get_text(strip=True) if item.find('div', class_='location') else "Pakhuis de Zwijger"
            link = item.find('a', class_='program-link')['href']

            image_tag = item.find('img')
            image_url = image_tag['src'] if image_tag and image_tag.has_attr('src') else None

            # Create event
            event = Event(
                title=title,
                description=description,
                location=location,
                url=f"https://dezwijger.nl{link}",
                media_url=image_url
            )

            # Parse date and add it to the event
            date_obj = self.parse_date(date_time_raw)
            # This will now always have a value or an exception will have been thrown
            event.dates = [EventDate(date=date_obj)]

            return event
        except Exception as e:
            print(f"Error parsing event: {e}")
            # Re-throw the exception so it's caught by the error handling in base_parser.py
            raise

    def parse_date(self, date_text):
        """Parse date and time from raw text, handling Dutch date formats."""
        try:
            # First, clean up the text
            date_text = date_text.replace(",", "").strip()

            # Extract parts: "vr 18 apr 09.30" -> day_of_week="vr", day="18", month="apr", time="09.30"
            parts = date_text.split()
            if len(parts) >= 3:
                # Handle format: [day_of_week] [day] [month] [time]
                # Check if first part is a day of week abbreviation (vr, za, etc.)
                day_of_week_prefixes = ['ma', 'di', 'wo', 'do', 'vr', 'za', 'zo']
                start_idx = 1 if parts[0].lower() in day_of_week_prefixes else 0

                # If we have enough parts after skipping day of week
                if len(parts) >= start_idx + 3:
                    day = parts[start_idx]
                    month = parts[start_idx + 1]
                    time_part = parts[start_idx + 2]

                    # Handle Dutch month abbreviations by mapping to standard ones
                    dutch_months = {
                        "jan": "jan", "feb": "feb", "mrt": "mar", "apr": "apr", "mei": "may", "jun": "jun",
                        "jul": "jul", "aug": "aug", "sep": "sep", "okt": "oct", "nov": "nov", "dec": "dec"
                    }

                    month_lower = month.lower()
                    if month_lower in dutch_months:
                        month = dutch_months[month_lower]

                    # Format the date string for parsing
                    # Use current year by default
                    current_year = datetime.now().year

                    # Check if event is likely in the next year
                    current_month = datetime.now().month

                    # Map month to number directly rather than trying to use strptime
                    month_num = {
                        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
                    }
                    target_month = month_num.get(month.lower(), 1)
                    if target_month < current_month and target_month < 4:  # If target month is earlier than current and in first quarter
                        current_year += 1

                    date_string = f"{day} {month} {current_year}"

                    # Parse date
                    try:
                        # Try abbreviated month format first
                        date_obj = datetime.strptime(date_string, "%d %b %Y")
                    except ValueError:
                        # If that fails, try full month format
                        try:
                            date_obj = datetime.strptime(date_string, "%d %B %Y")
                        except ValueError:
                            # Last resort - manually map month to number and parse
                            month_num = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                                         "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
                            month_int = month_num.get(month.lower(), 1)
                            date_obj = datetime(current_year, month_int, int(day))

                    # Handle time (convert "09.30" format to proper time)
                    if "." in time_part:
                        hour, minute = time_part.split(".")
                        date_obj = date_obj.replace(hour=int(hour), minute=int(minute))

                    return date_obj

            # Handle special cases like "vandaag" (today) or "morgen" (tomorrow)
            lower_text = date_text.lower()
            if "vandaag" in lower_text:
                today = datetime.today()
                # Try to extract time if available
                time_parts = [p for p in parts if "." in p]
                if time_parts:
                    hour, minute = time_parts[0].split(".")
                    today = today.replace(hour=int(hour), minute=int(minute))
                return today

            if "morgen" in lower_text:
                tomorrow = datetime.today() + timedelta(days=1)
                # Try to extract time if available
                time_parts = [p for p in parts if "." in p]
                if time_parts:
                    hour, minute = time_parts[0].split(".")
                    tomorrow = tomorrow.replace(hour=int(hour), minute=int(minute))
                return tomorrow

            # No valid date format found, throw an exception
            raise ValueError(f"Could not parse date format: {date_text}")

        except Exception as e:
            # Log and re-throw the exception
            print(f"Failed to parse date: {date_text}. Error: {e}")
            raise