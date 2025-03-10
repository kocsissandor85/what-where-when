# Event Parser

**Note: This is an LLM-managed codebase created for learning purposes only. Not intended for production use.**

This application scrapes and aggregates event data from various venue websites, processes the information, and stores it in a database.

## Overview

The application consists of:
- A parser framework for scraping venue websites
- A database model for storing event information
- A management system to run parsers and store results
- A web interface for viewing, managing, and exporting events

## Requirements

See `requirements.txt` for dependencies. Main requirements include:
- beautifulsoup4
- sqlalchemy
- python-dotenv
- requests
- selenium (for some parsers)

Additional dependencies for the web interface:
- Flask
- Flask-CORS
- google-auth
- google-auth-oauthlib
- google-auth-httplib2
- google-api-python-client

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with:
   ```
   DATABASE_URL=sqlite:///events.db
   GOOGLE_CREDENTIALS_PATH=credentials.json
   GOOGLE_TOKEN_PATH=token.json
   GOOGLE_CALENDAR_ID=primary
   ```

## Google Calendar Integration Setup

For the web interface's Google Calendar export feature:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials:
   - Application type: Desktop application
   - Download the credentials JSON file and save it as `credentials.json` in the root directory

## Running the Application

### Parser Operations

To run all parsers:
```bash
python main.py
```

To run specific parsers:
```bash
python main.py --parser frascati richiel
```

### Web Interface

To start the web interface:
```bash
python web/app.py
```

Then navigate to `http://localhost:5000` in your browser.

## Web Interface Features

The web interface allows you to:
- View all events in a sortable and filterable table
- Filter events by text search
- Sort events by clicking on column headers
- Toggle between showing all events or just active (non-archived) events
- Delete individual events
- Bulk-delete multiple selected events
- Export selected events to Google Calendar

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
├── scripts/
│   └── __init__.py
├── web/                    # Web interface files
│   ├── app.py              # Flask application
│   ├── calendar_service.py # Google Calendar integration
│   ├── static/             # Static assets
│   │   ├── css/
│   │   │   └── custom.css  # Custom CSS
│   │   └── js/
│   │       └── main.js     # Frontend JavaScript
│   └── templates/          # HTML templates
│       └── index.html      # Main HTML template
├── main.py               # Parser application entry point
├── requirements.txt      # Dependencies
├── .env                  # Environment variables
└── README.md               # Project documentation
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

## API Endpoints

The web interface provides the following REST API endpoints:

- `GET /api/events` - Get all events with optional filtering and sorting
- `DELETE /api/events/:id` - Delete a single event by ID
- `POST /api/events/bulk-delete` - Delete multiple events by ID
- `POST /api/events/export-calendar` - Export selected events to Google Calendar

## Features

- Dynamic parser registration
- Automatic archiving of past events
- Duplicate event detection
- Supports multiple date formats and patterns
- Logging of parsing operations
- Web interface for event management
- Google Calendar integration

## Development Notes

- Add Selenium WebDriver for your browser if using the Richiel parser
- Dutch locale is required for date parsing in some parsers
- Parser output is logged to `parsers/parser.log`

## Security Notes

- This application is designed for local use only and doesn't include authentication
- Protect your Google API credentials and token files
- Never commit your `.env` file or `credentials.json` to version control