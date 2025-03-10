import os
import sys
from datetime import datetime

# Add the parent directory to the Python path so we can import modules from there
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from sqlalchemy import create_engine, desc, or_, and_
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
        date_start = request.args.get('date_start')
        date_end = request.args.get('date_end')

        # Base query with joins
        query = session.query(Event).outerjoin(Event.dates)

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

        # Apply date range filter if provided
        if date_start and date_end:
            try:
                start_date = datetime.strptime(date_start, '%Y-%m-%d')
                end_date = datetime.strptime(date_end, '%Y-%m-%d')

                # Filter events where:
                # - An event starts within the range (date >= start_date AND date <= end_date)
                # - OR an event ends within the range (end_date >= start_date AND end_date <= end_date)
                # - OR an event spans the entire range (date <= start_date AND end_date >= end_date)
                query = query.filter(
                    or_(
                        and_(EventDate.date >= start_date, EventDate.date <= end_date),
                        and_(EventDate.end_date >= start_date, EventDate.end_date <= end_date),
                        and_(EventDate.date <= start_date, EventDate.end_date >= end_date)
                    )
                )
            except (ValueError, TypeError):
                # If date parsing fails, ignore the date filter
                pass

        # Apply sorting (except for date which is handled client-side)
        if sort_by != 'date':
            if sort_dir == 'desc':
                query = query.order_by(desc(getattr(Event, sort_by)))
            else:
                query = query.order_by(getattr(Event, sort_by))

        # Get unique events (due to the join with dates)
        event_ids = [event.id for event in query.distinct(Event.id)]

        # Fetch complete events with their dates
        events = []
        for event_id in event_ids:
            event = session.query(Event).filter(Event.id == event_id).first()
            if event:
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


@app.route('/api/events/<int:event_id>/archive', methods=['PUT'])
def archive_event(event_id):
    """Archive a single event by ID."""
    session = Session()
    try:
        event = session.query(Event).filter_by(id=event_id).first()
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        event.archived = True
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


@app.route('/api/events/bulk-archive', methods=['POST'])
def bulk_archive_events():
    """Archive multiple events by ID."""
    session = Session()
    try:
        event_ids = request.json.get('event_ids', [])
        if not event_ids:
            return jsonify({'error': 'No event IDs provided'}), 400

        # Archive events
        events = session.query(Event).filter(Event.id.in_(event_ids)).all()
        archived_count = 0

        for event in events:
            event.archived = True
            archived_count += 1

        session.commit()

        return jsonify({'success': True, 'archived_count': archived_count})

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