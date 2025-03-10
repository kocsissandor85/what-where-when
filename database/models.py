from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ParserMetadata(Base):
    __tablename__ = 'parser_metadata'

    id = Column(Integer, primary_key=True, autoincrement=True)
    parser_name = Column(String(255), unique=True, nullable=False)
    last_parsed_date = Column(DateTime, nullable=True)


Base = declarative_base()


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
    last_run = Column(DateTime, nullable=False)
    success = Column(Boolean, default=True)
    events_parsed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
