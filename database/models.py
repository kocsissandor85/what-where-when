from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Association table for many-to-many relationship between events and tags
event_tags = Table(
    'event_tags',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('events.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class ParserMetadata(Base):
    __tablename__ = 'parser_metadata'

    id = Column(Integer, primary_key=True, autoincrement=True)
    parser_name = Column(String(255), unique=True, nullable=False)
    last_parsed_date = Column(DateTime, nullable=True)


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    location = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    media_url = Column(String(500), nullable=True)
    archived = Column(Boolean, default=False)

    # Relationship to event dates
    dates = relationship('EventDate', back_populates='event', cascade="all, delete-orphan")

    # Relationship to tags (many-to-many)
    tags = relationship('Tag', secondary=event_tags, back_populates='events')


class EventDate(Base):
    __tablename__ = 'event_dates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id', ondelete='CASCADE'))
    date = Column(DateTime, nullable=False)  # Exact date or start of interval
    time = Column(String(20), nullable=True)  # Optional time for the date
    end_date = Column(DateTime, nullable=True)  # For intervals
    end_time = Column(String(20), nullable=True)  # Optional end time for intervals

    event = relationship('Event', back_populates='dates')


class ParserHealth(Base):
    __tablename__ = 'parser_health'

    id = Column(Integer, primary_key=True, autoincrement=True)
    parser_name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)  # Added display_name column
    last_run = Column(DateTime, nullable=False)
    success = Column(Boolean, default=True)
    events_parsed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)  # Unique tag names

    # Relationship to events (many-to-many)
    events = relationship('Event', secondary=event_tags, back_populates='tags')

    # Relationship to parsers (many-to-many)
    parsers = relationship('ParserTag', back_populates='tag')


class ParserTag(Base):
    __tablename__ = 'parser_tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    parser_name = Column(String(255), nullable=False)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'))

    # Relationship to tags
    tag = relationship('Tag', back_populates='parsers')

    # Unique constraint to ensure a tag is only assigned once to a parser
    __table_args__ = (
        # Note: SQLite doesn't enforce this constraint, but other DBs will
        # This serves more as documentation for now
    )


class TagMapping(Base):
    __tablename__ = 'tag_mappings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_tag = Column(String(100), nullable=False, unique=True)  # Original tag name from parser
    display_tag = Column(String(100), nullable=False)  # Consolidated display name