from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from database.models import Event, EventDate, Tag
from parsers.base_parser import BaseParser
from database.db_manager import DBManager
from utils.config import DATABASE_URL
import locale

class RichelParser(BaseParser):
    BASE_URL = "https://theaterderichel.nl/agenda/"

    # Add human-readable display name
    display_name = "Theater de Richel"

    # Set automatic tags for all events from this venue
    automatic_tags = ["Amsterdam"]

    def __init__(self):
        # Set up Selenium WebDriver
        self.driver = webdriver.Chrome()  # Use the appropriate driver for your browser
        self.driver.maximize_window()
        self.db_manager = DBManager(DATABASE_URL)

    def fetch_data(self):
        """Fetch all event data by handling scrolling and lazy loading."""
        self.driver.get(self.BASE_URL)
        wait = WebDriverWait(self.driver, 10)

        while True:
            try:
                # Wait until spinner becomes visible
                wait.until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "jet-listing-grid__loader"))
                )

                # Wait until spinner becomes invisible
                wait.until(
                    EC.invisibility_of_element_located((By.CLASS_NAME, "jet-listing-grid__loader"))
                )
            except Exception as e:
                print(f"Error waiting for spinner visibility toggle: {e}")
                break

            # Scroll to the bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Check if spinner reappears, if not, assume no more content
            try:
                wait.until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "jet-listing-grid__loader"))
                )
            except Exception as e:
                print("No more spinner visibility detected. Stopping scrolling.")
                break

        # Get the final rendered HTML
        html = self.driver.page_source
        self.driver.quit()

        # Hand over to BeautifulSoup for parsing
        return self.parse_events(html)

    def parse_events(self, html):
        """Parse events from the loaded HTML."""
        soup = BeautifulSoup(html, "html.parser")
        event_items = soup.find_all("div", class_="jet-listing-grid__item")  # Adjust class as per the site structure

        events = []
        for item in event_items:
            try:
                event = self.parse_event(item)
                if event:
                    # Check if the event already exists
                    if self.db_manager.check_event_exists(event.title):
                        print(f"Event already exists: {event.title}.")
                        continue

                    events.append(event)
            except Exception as e:
                print(f"Error parsing event: {e}")

        return events

    def parse_event(self, item):
        """Parse a single event item and return an Event object."""
        try:
            # Extract the title
            title_element = item.find("h2", class_="jet-listing-dynamic-field__content")
            title = title_element.get_text(strip=True) if title_element else "Unknown Event"

            # Extract the description (optional)
            # This is not explicitly available in the example; we can leave it empty or a placeholder.
            description = "No description available."

            # Extract the date and time
            date_element = item.find("div", class_="jet-listing-dynamic-field__content")
            if date_element:
                date_text = date_element.get_text(strip=True)
                date_time = self.parse_date_time(date_text)
            else:
                date_time = None

            # Extract the URL
            url_element = item.find("a", class_="jet-engine-listing-overlay-link")
            url = url_element["href"] if url_element else None

            # Extract the image URL
            image_element = item.find("img", class_="jet-listing-dynamic-image__img")
            image_url = image_element["src"] if image_element else None

            # Static location
            location = "Theater de Richel"

            # Create Event object
            event = Event(
                title=title,
                description=description,
                location=location,
                url=url,
                media_url=image_url
            )

            # Create EventDate and add it to event if date_time is available
            if date_time:
                event.dates = [EventDate(date=date_time)]

            # Extract tags (but don't add them yet - we'll let the BaseParser handle this)
            event_tags = self.extract_tags(item)
            if event_tags:
                # Store tag names as an attribute on the event for later processing
                # This avoids session conflicts by not creating Tag objects here
                event._tag_names = event_tags

            return event
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None

    def extract_tags(self, item):
        """Extract tags from the event item."""
        tags = []
        try:
            # Find the tag container
            tag_container = item.find("div", class_="jet-listing-dynamic-terms")

            if tag_container:
                # Find all tag links - these contain the tag names
                tag_links = tag_container.find_all("span", class_="jet-listing-dynamic-terms__link")

                # Extract the text from each tag link
                for tag_link in tag_links:
                    tag_name = tag_link.get_text(strip=True)
                    if tag_name:
                        tags.append(tag_name)

            return tags
        except Exception as e:
            print(f"Error extracting tags: {e}")
            return []

    def parse_date_time(self, date_text):
        """
        Parse Dutch date text into a Python datetime object.
        Supports formats like 'vr 6 jun' and 'vrijdag 6 juni'.
        """
        # Set locale to Dutch to handle month names
        try:
            locale.setlocale(locale.LC_TIME, "nl_NL.UTF-8")
        except locale.Error:
            print("Locale 'nl_NL.UTF-8' not available. Using default locale.")

        # Define possible date formats
        date_formats = [
            "%a %d %b",  # Short format, e.g., "vr 6 jun"
            "%A %d %b",  # Long format, e.g., "vrijdag 6 jun"
        ]

        # Current year (assume year is not in the date text)
        current_year = datetime.now().year

        # Try parsing the date with each format
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date_text, date_format)
                return parsed_date.replace(year=current_year)  # Add the current year
            except ValueError:
                continue

        # If parsing fails
        print(f"Could not parse date: {date_text}")
        return None