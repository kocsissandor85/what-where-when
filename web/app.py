import os
import sys

# Add the parent directory to the Python path so we can import modules from there
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from sqlalchemy import create_engine, desc, or_
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from calendar_service import create_calendar_event, setup_credentials

from database.models import Event, EventDate
from database.db_manager import DBManager
from utils.config import DATABASE_URL

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Database connection
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# Routes
@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')


@app.route('/api/events')
def get_events():
    """Get all events with optional filtering."""
    session = Session()
    try:
        # Get query parameters
        filter_text = request.args.get('filter', '')
        sort_by = request.args.get('sort_by', 'title')
        sort_dir = request.args.get('sort_dir', 'asc')
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'

        # Base query
        query = session.query(Event)

        # Apply filters
        if filter_text:
            query = query.filter(
                or_(
                    Event.title.ilike(f'%{filter_text}%'),
                    Event.description.ilike(f'%{filter_text}%'),
                    Event.location.ilike(f'%{filter_text}%')
                )
            )

        if not include_archived:
            query = query.filter(Event.archived == False)

        # Apply sorting
        if sort_dir == 'desc':
            query = query.order_by(desc(getattr(Event, sort_by)))
        else:
            query = query.order_by(getattr(Event, sort_by))

        # Execute query and convert to list of dictionaries
        events = []
        for event in query.all():
            event_dict = {
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'location': event.location,
                'url': event.url,
                'media_url': event.media_url,
                'archived': event.archived,
                'dates': []
            }

            # Add dates
            for date in event.dates:
                date_dict = {
                    'id': date.id,
                    'date': date.date.isoformat() if date.date else None,
                    'time': date.time,
                    'end_date': date.end_date.isoformat() if date.end_date else None,
                    'end_time': date.end_time
                }
                event_dict['dates'].append(date_dict)

            events.append(event_dict)

        return jsonify(events)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()


@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete a single event by ID."""
    session = Session()
    try:
        event = session.query(Event).filter_by(id=event_id).first()
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        session.delete(event)
        session.commit()
        return jsonify({'success': True})

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()


@app.route('/api/events/bulk-delete', methods=['POST'])
def bulk_delete_events():
    """Delete multiple events by ID."""
    session = Session()
    try:
        event_ids = request.json.get('event_ids', [])
        if not event_ids:
            return jsonify({'error': 'No event IDs provided'}), 400

        # Delete events
        deleted_count = session.query(Event).filter(Event.id.in_(event_ids)).delete(synchronize_session='fetch')
        session.commit()

        return jsonify({'success': True, 'deleted_count': deleted_count})

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()


@app.route('/api/events/export-calendar', methods=['POST'])
def export_to_calendar():
    """Export selected events to Google Calendar."""
    session = Session()
    try:
        event_ids = request.json.get('event_ids', [])
        if not event_ids:
            return jsonify({'error': 'No event IDs provided'}), 400

        # Get the credentials
        credentials = setup_credentials()
        if not credentials:
            return jsonify({'error': 'Google Calendar credentials not set up'}), 500

        # Get events from database
        events = session.query(Event).filter(Event.id.in_(event_ids)).all()

        # Export to Google Calendar
        results = []
        for event in events:
            for date in event.dates:
                # Create calendar event
                calendar_event = {
                    'summary': event.title,
                    'location': event.location,
                    'description': event.description + f"\n\nOriginal URL: {event.url}",
                    'start': {
                        'dateTime': date.date.isoformat(),
                        'timeZone': 'Europe/Amsterdam',
                    },
                    'end': {
                        'dateTime': date.end_date.isoformat() if date.end_date else date.date.isoformat(),
                        'timeZone': 'Europe/Amsterdam',
                    },
                }

                # Add to Google Calendar
                result = create_calendar_event(credentials, calendar_event)
                results.append({
                    'event_id': event.id,
                    'title': event.title,
                    'calendar_event_id': result.get('id') if result else None,
                    'success': bool(result),
                    'error': str(result.get('error')) if not result else None
                })

        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()


if __name__ == '__main__':
    app.run(debug=True)
