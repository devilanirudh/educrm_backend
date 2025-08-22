"""
Exam and Date-sheet related database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Date, Time, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class ExamTerm(Base):
    """Exam Terms, e.g., Term 1, Mid-Term, Final Term"""
    __tablename__ = "exam_terms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    academic_year = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    datesheets = relationship("DateSheet", back_populates="term")

    def __repr__(self):
        return f"<ExamTerm(id={self.id}, name='{self.name}', academic_year='{self.academic_year}')>"


class DateSheet(Base):
    """Date-sheet for a specific class and term"""
    __tablename__ = "datesheets"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    term_id = Column(Integer, ForeignKey("exam_terms.id"), nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # draft, published, archived
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    class_info = relationship("Class")
    term = relationship("ExamTerm", back_populates="datesheets")
    entries = relationship("DateSheetEntry", back_populates="datesheet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DateSheet(id={self.id}, class_id={self.class_id}, term_id={self.term_id})>"


class DateSheetEntry(Base):
    """Individual entry in a date-sheet"""
    __tablename__ = "datesheet_entries"

    id = Column(Integer, primary_key=True, index=True)
    datesheet_id = Column(Integer, ForeignKey("datesheets.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    exam_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    room_number = Column(String(50), nullable=True)
    max_marks = Column(Integer, nullable=False)
    exam_type = Column(String(50), nullable=False, default="Theory") # Theory, Practical

    # Relationships
    datesheet = relationship("DateSheet", back_populates="entries")
    subject = relationship("Subject")

    def __repr__(self):
        return f"<DateSheetEntry(id={self.id}, subject_id={self.subject_id}, date='{self.exam_date}')>"