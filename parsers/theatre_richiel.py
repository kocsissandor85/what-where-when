from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from database.models import Event, EventDate
from parsers.base_parser import BaseParser
import locale

class RichelParser(BaseParser):
    BASE_URL = "https://theaterderichel.nl/agenda/"

    def __init__(self):
        # Set up Selenium WebDriver
        self.driver = webdriver.Chrome()  # Use the appropriate driver for your browser
        self.driver.maximize_window()

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

            # Create Event object without date_time, instead using EventDate for date handling
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

            return event
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None

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