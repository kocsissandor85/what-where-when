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

from database.models import Event, EventDate, ParserHealth
from database.models import Tag, event_tags
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
        tag_filter = request.args.get('tag')  # Get tag filter parameter

        # Base query with joins
        query = session.query(Event).outerjoin(Event.dates)

        # Apply tag filter if provided
        if tag_filter:
            query = query.join(event_tags, Event.id == event_tags.c.event_id) \
                .join(Tag, Tag.id == event_tags.c.tag_id) \
                .filter(Tag.name == tag_filter)

        # Apply other filters
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

        # Fetch complete events with their dates and tags
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
                    'dates': [],
                    'tags': []  # Add tags to event data
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

                # Add tags
                for tag in event.tags:
                    event_dict['tags'].append({
                        'id': tag.id,
                        'name': tag.name
                    })

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


@app.route('/api/parser-health')
def get_parser_health():
    """Get the health status of all parsers."""
    session = Session()
    try:
        # Simpler query that just gets the latest record for each parser
        parser_records = {}

        # Get all records
        all_records = session.query(ParserHealth).order_by(ParserHealth.last_run.desc()).all()

        # Keep only the latest record for each parser
        for record in all_records:
            if record.parser_name not in parser_records:
                parser_records[record.parser_name] = record

        # Convert to dictionary for JSON response
        health_data = []
        for parser_name, record in parser_records.items():
            health_data.append({
                'parser_name': record.parser_name,
                'display_name': record.display_name or record.parser_name,  # Use display_name if available
                'last_run': record.last_run.isoformat() if record.last_run else None,
                'success': record.success,
                'events_parsed': record.events_parsed,
                'error_message': record.error_message
            })

        return jsonify({'parser_health': health_data})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()


@app.route('/api/parser-health/error-details/<string:parser_name>')
def get_parser_error_details(parser_name):
    """Get the detailed error message for a parser."""
    session = Session()
    try:
        # Get the latest record for the specified parser
        record = session.query(ParserHealth).filter_by(parser_name=parser_name) \
            .order_by(ParserHealth.last_run.desc()).first()

        if not record:
            return jsonify({'error': 'Parser record not found'}), 404

        return jsonify({
            'parser_name': record.parser_name,
            'display_name': record.display_name or record.parser_name,
            'last_run': record.last_run.isoformat() if record.last_run else None,
            'error_message': record.error_message or 'No error information available'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()


@app.route('/api/tags')
def get_tags():
    """Get all available tags."""
    session = Session()
    try:
        tags = session.query(Tag).order_by(Tag.name).all()
        tag_list = [{'id': tag.id, 'name': tag.name} for tag in tags]
        return jsonify(tag_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


if __name__ == '__main__':
    app.run(debug=True)