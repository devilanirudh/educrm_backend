"""Database model for events."""

import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.database.session import Base

class EventAudience(enum.Enum):
    ALL = "all"
    STUDENTS = "students"
    TEACHERS = "teachers"

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    audience = Column(Enum(EventAudience), nullable=False, default=EventAudience.ALL)