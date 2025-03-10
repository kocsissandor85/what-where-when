import os
import json
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']


def setup_credentials():
    """Set up Google Calendar credentials."""
    credentials = None

    # Check if token file exists
    token_path = os.getenv('GOOGLE_TOKEN_PATH', 'token.json')
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')

    if os.path.exists(token_path):
        # Load credentials from token file
        try:
            credentials = Credentials.from_authorized_user_info(
                json.loads(open(token_path).read()),
                SCOPES
            )
        except Exception as e:
            print(f"Error loading token: {str(e)}")

    # If no valid credentials, get new ones
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            # Refresh expired credentials
            try:
                credentials.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {str(e)}")
                credentials = None

        # Get new credentials if needed
        if not credentials:
            try:
                # Check if credentials file exists
                if not os.path.exists(credentials_path):
                    print("No credentials.json file found.")
                    return None

                # Get new credentials
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                credentials = flow.run_local_server(port=0)

                # Save credentials for next run
                with open(token_path, 'w') as token:
                    token.write(credentials.to_json())
            except Exception as e:
                print(f"Error getting new credentials: {str(e)}")
                return None

    return credentials


def create_calendar_event(credentials, event_data):
    """Create a new event in Google Calendar."""
    try:
        # Build the service
        service = build('calendar', 'v3', credentials=credentials)

        # Get calendar ID
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')

        # Create the event
        event = service.events().insert(calendarId=calendar_id, body=event_data).execute()

        return event
    except Exception as e:
        print(f"Error creating calendar event: {str(e)}")
        return {'error': str(e)}
