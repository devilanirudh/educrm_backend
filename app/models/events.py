"""
Event management models
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Date, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base
from datetime import datetime

# Import models to ensure tables exist
from app.models.user import User
from app.models.student import Student
from app.models.academic import Class


class Event(Base):
    """Event model for school events"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=False)  # Dynamic input from user
    
    # Date and time
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    location = Column(String(200), nullable=True)
    
    # Targeting
    target_type = Column(String(20), nullable=False)  # 'school_wide', 'teachers', 'class_specific'
    target_class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    
    # Status and metadata
    status = Column(String(20), default="active")  # active, cancelled, completed
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    target_class = relationship("Class", foreign_keys=[target_class_id])
    assignments = relationship("EventAssignment", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', target_type='{self.target_type}')>"


class EventAssignment(Base):
    """Tracks which students are assigned to events"""
    __tablename__ = "event_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    event = relationship("Event", back_populates="assignments")
    student = relationship("Student")
    
    def __repr__(self):
        return f"<EventAssignment(event_id={self.event_id}, student_id={self.student_id})>"
