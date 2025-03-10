# Event Parser

**Note: This is an LLM-managed codebase created for learning purposes only. Not intended for production use.**

This application scrapes and aggregates event data from various venue websites, processes the information, and stores it in a database.

## Overview

The application consists of:
- A parser framework for scraping venue websites
- A database model for storing event information
- A management system to run parsers and store results

## Requirements

See `requirements.txt` for dependencies. Main requirements include:
- beautifulsoup4
- sqlalchemy
- python-dotenv
- requests
- selenium (for some parsers)

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with:
   ```
   DATABASE_URL=sqlite:///events.db
   ```

## Running the Application

To run all parsers:
```bash
python main.py
```

To run specific parsers:
```bash
python main.py --parser frascati richiel
```

## Project Structure

```
├── database/
│   ├── db_manager.py     # Database operations
│   ├── models.py         # SQLAlchemy data models
├── parsers/
│   ├── base_parser.py    # Abstract base class for parsers
│   ├── parser_manager.py # Manages and runs parsers
│   ├── frascati.py       # Frascati venue parser
│   ├── richiel.py        # Richel venue parser
│   └── deprecated/       # Old parsers
├── utils/
│   ├── config.py         # Configuration management
│   ├── logger.py         # Logging setup
├── main.py               # Application entry point
└── requirements.txt      # Dependencies
```

## Creating a New Parser

To create a new parser for a venue website:

1. Create a new Python file in the `parsers` directory (e.g., `parsers/new_venue.py`)
2. Implement a class that inherits from `BaseParser`:

```python
from database.models import Event, EventDate
from parsers.base_parser import BaseParser

class NewVenueParser(BaseParser):
    BASE_URL = "https://example-venue.com/agenda/"
    
    def __init__(self):
        # Initialize any necessary components
        pass
        
    def fetch_data(self):
        """Fetch event data from the website"""
        # Implementation to fetch data
        # ...
        return events  # List of Event objects
        
    def parse_event(self, item):
        """Parse a single event"""
        # Extract event details
        # ...
        
        # Create Event object
        event = Event(
            title=title,
            description=description,
            location=location,
            url=url,
            media_url=image_url
        )
        
        # Add date information
        event.dates = [EventDate(
            date=start_date,
            end_date=end_date,  # Optional
            time=start_time,    # Optional
            end_time=end_time   # Optional
        )]
        
        return event
```

3. The parser will be automatically registered by the `ParserManager` the next time you run the application.

## Database Schema

The database consists of two main tables:
- `events`: Stores event information (title, description, etc.)
- `event_dates`: Stores date information associated with events

Events can have multiple dates, handled through a one-to-many relationship.

## Features

- Dynamic parser registration
- Automatic archiving of past events
- Duplicate event detection
- Supports multiple date formats and patterns
- Logging of parsing operations

## Development Notes

- Add Selenium WebDriver for your browser if using the Richiel parser
- Dutch locale is required for date parsing in some parsers
- Parser output is logged to `parsers/parser.log`