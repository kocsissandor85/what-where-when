from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Event, ParserMetadata, Tag, ParserTag, TagMapping
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from utils.logger import logger


class DBManager:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create_tables(self):
        """Recreate all tables for fresh start."""
        # Base.metadata.drop_all(self.engine)  # Drop existing tables
        Base.metadata.create_all(self.engine)  # Create fresh schema

    def check_event_exists(self, title, event_date=None):
        """Check if an event with the same title and date exists in the database."""
        try:
            if event_date:
                # Check for events with the same title and date
                from sqlalchemy.orm import joinedload
                event = self.session.query(Event).filter_by(title=title).options(joinedload(Event.dates)).first()

                if event:
                    # Check if any of the dates match
                    for date in event.dates:
                        if date.date.date() == event_date.date():
                            return True
                return False
            else:
                # Fall back to title-only check if no date provided
                event = self.session.query(Event).filter_by(title=title).first()
                if event:
                    return True
                return False
        except Exception as e:
            print(f"Failed to check event existence: {e}")
            return False

    def get_last_parsed_date(self, parser_name):
        """Retrieve the last parsed date for a parser."""
        metadata = self.session.query(ParserMetadata).filter_by(parser_name=parser_name).first()
        return metadata.last_parsed_date if metadata else None

    def update_last_parsed_date(self, parser_name, last_parsed_date):
        """Update the last parsed date for a parser."""
        metadata = self.session.query(ParserMetadata).filter_by(parser_name=parser_name).first()
        if not metadata:
            metadata = ParserMetadata(parser_name=parser_name, last_parsed_date=last_parsed_date)
            self.session.add(metadata)
        else:
            metadata.last_parsed_date = last_parsed_date
        self.session.commit()

    def add_event(self, event):
        """Add a new event to the database if no matching title."""
        if self.check_event_exists(event.title):
            print(f"Skipped duplicate event: {event.title}")
            return
        self.session.add(event)
        self.session.commit()
        logger.info(f"Added event: {event.title}")

        # Log tags if any
        if event.tags:
            tag_names = [tag.name for tag in event.tags]
            logger.info(f"Event tags: {', '.join(tag_names)}")

    def archive_event(self, event_id):
        """Mark an event as archived."""
        try:
            event = self.session.query(Event).filter_by(id=event_id).first()
            if not event:
                print(f"Event with ID {event_id} not found.")
                return False
            event.archived = True
            self.session.commit()
            logger.info(f"Event with ID {event_id} marked as archived.")
            return True
        except Exception as e:
            print(f"Failed to archive event: {e}")
            self.session.rollback()
            return False

    def archive_events(self):
        """Archive events where all associated dates are in the past."""
        try:
            # Find events where all associated dates are in the past
            now = datetime.now()

            events_to_archive = (
                self.session.query(Event)
                .options(joinedload(Event.dates))
                .filter(Event.archived == False)
                .all()
            )

            count = 0
            for event in events_to_archive:
                # Check if all associated dates are in the past
                if all((event_date.end_date if event_date.end_date else event_date.date) < now for event_date in event.dates):
                    event.archived = True
                    count += 1

            self.session.commit()
            logger.info(f"{count} events archived.")
            return True
        except Exception as e:
            print(f"Failed to archive events: {e}")
            self.session.rollback()
            return False

    def get_all_events(self):
        """Retrieve all events from the database."""
        return self.session.query(Event).all()

    def get_active_events(self):
        """Retrieve all events that are not archived."""
        return self.session.query(Event).filter_by(archived=False).all()

    # Tag management methods
    def create_tag(self, tag_name):
        """Create a new tag if it doesn't exist."""
        tag = self.session.query(Tag).filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            self.session.add(tag)
            self.session.commit()
            logger.info(f"Created new tag: {tag_name}")
        return tag

    def get_tag(self, tag_name):
        """Get a tag by name."""
        return self.session.query(Tag).filter_by(name=tag_name).first()

    def get_or_create_tag(self, tag_name):
        """Get a tag by name or create it if it doesn't exist."""
        tag = self.get_tag(tag_name)
        if not tag:
            tag = self.create_tag(tag_name)
        return tag

    def get_all_tags(self):
        """Get all tags in the database."""
        return self.session.query(Tag).all()

    def get_parser_tags(self, parser_name):
        """Get all tags associated with a parser."""
        parser_tags = self.session.query(ParserTag).filter_by(parser_name=parser_name).all()
        tags = []
        for parser_tag in parser_tags:
            tag = self.session.query(Tag).filter_by(id=parser_tag.tag_id).first()
            if tag:
                tags.append(tag)
        return tags

    def set_parser_tags(self, parser_name, tag_names):
        """Set the automatic tags for a parser."""
        # Remove existing parser tags
        self.session.query(ParserTag).filter_by(parser_name=parser_name).delete()

        # Add new tags
        for tag_name in tag_names:
            tag = self.get_or_create_tag(tag_name)
            parser_tag = ParserTag(parser_name=parser_name, tag_id=tag.id)
            self.session.add(parser_tag)

        self.session.commit()
        logger.info(f"Set tags for parser {parser_name}: {', '.join(tag_names)}")

    def add_tag_to_event(self, event_id, tag_name):
        """Add a tag to an event."""
        event = self.session.query(Event).filter_by(id=event_id).first()
        if not event:
            logger.error(f"Event with ID {event_id} not found.")
            return False

        tag = self.get_or_create_tag(tag_name)
        if tag not in event.tags:
            event.tags.append(tag)
            self.session.commit()
            logger.info(f"Added tag '{tag_name}' to event '{event.title}'")
        return True

    def remove_tag_from_event(self, event_id, tag_name):
        """Remove a tag from an event."""
        event = self.session.query(Event).filter_by(id=event_id).first()
        if not event:
            logger.error(f"Event with ID {event_id} not found.")
            return False

        tag = self.get_tag(tag_name)
        if tag and tag in event.tags:
            event.tags.remove(tag)
            self.session.commit()
            logger.info(f"Removed tag '{tag_name}' from event '{event.title}'")
        return True

    def close(self):
        """Close the database session."""
        self.session.close()

    def get_tag_mappings(self):
        """Get all tag mappings."""
        return self.session.query(TagMapping).all()

    def get_mapping_for_tag(self, tag_name):
        """Get the display name for a given source tag."""
        mapping = self.session.query(TagMapping).filter_by(source_tag=tag_name).first()
        return mapping.display_tag if mapping else tag_name

    def set_tag_mapping(self, source_tag, display_tag):
        """Create or update a tag mapping."""
        mapping = self.session.query(TagMapping).filter_by(source_tag=source_tag).first()
        if not mapping:
            mapping = TagMapping(source_tag=source_tag, display_tag=display_tag)
            self.session.add(mapping)
        else:
            mapping.display_tag = display_tag
        self.session.commit()
        return mapping

    def remove_tag_mapping(self, source_tag):
        """Remove a tag mapping."""
        self.session.query(TagMapping).filter_by(source_tag=source_tag).delete()
        self.session.commit()