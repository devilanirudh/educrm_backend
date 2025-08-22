"""
Student-related database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Date, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base
from app.models.financial import Invoice
from app.models.library import BookIssue, LibraryMember
import enum


# Association table for parent-student relationships
parent_student_relationships = Table(
    'parent_student_relationships',
    Base.metadata,
    Column('parent_id', Integer, ForeignKey('parents.id'), primary_key=True),
    Column('student_id', Integer, ForeignKey('students.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)


class Student(Base):
    """Student profile and academic information"""
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    student_id = Column(String(50), unique=True, index=True, nullable=False)  # School-assigned ID
    
    # Academic Information
    admission_date = Column(Date, nullable=False)
    current_class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    academic_year = Column(String(20), nullable=False)  # e.g., "2024-2025"
    roll_number = Column(String(20), nullable=True)
    section = Column(String(10), nullable=True)
    
    # Personal Information
    blood_group = Column(String(5), nullable=True)
    allergies = Column(Text, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    transportation_mode = Column(String(50), nullable=True)  # bus, car, walk, etc.
    bus_route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    
    # Hostel Information
    hostel_room_id = Column(Integer, ForeignKey("hostel_rooms.id"), nullable=True)
    is_hosteller = Column(Boolean, default=False, nullable=False)
    
    # Dynamic data from form builder
    dynamic_data = Column(JSON, nullable=True)

    # Academic Status
    is_active = Column(Boolean, default=True, nullable=False)
    graduation_date = Column(Date, nullable=True)
    dropout_date = Column(Date, nullable=True)
    dropout_reason = Column(Text, nullable=True)
    
    # Additional Information
    previous_school = Column(String(200), nullable=True)
    transfer_certificate_number = Column(String(100), nullable=True)
    hobbies = Column(Text, nullable=True)
    special_needs = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="students")
    current_class = relationship("Class", foreign_keys=[current_class_id])
    parents = relationship("Parent", secondary=parent_student_relationships, back_populates="children")
    
    # Academic relationships
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")
    assignment_submissions = relationship("AssignmentSubmission", back_populates="student", cascade="all, delete-orphan")
    exam_results = relationship("ExamResult", back_populates="student", cascade="all, delete-orphan")
    
    # Financial relationships
    fee_payments = relationship("Invoice", back_populates="student", cascade="all, delete-orphan")
    
    # Library relationships
    
    # Transport relationships
    bus_route = relationship("Route", foreign_keys=[bus_route_id])
    
    # Hostel relationships
    hostel_room = relationship("HostelRoom", foreign_keys=[hostel_room_id])
    
    def __repr__(self):
        return f"<Student(id={self.id}, student_id='{self.student_id}', user_id={self.user_id})>"
    
    @property
    def full_name(self):
        return self.user.full_name if self.user else "Unknown"
    
    @property
    def age(self):
        if self.user and self.user.date_of_birth:
            from datetime import date
            today = date.today()
            birth_date = self.user.date_of_birth.date()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return None


class AttendanceRecord(Base):
    """Student attendance tracking"""
    __tablename__ = "attendance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # present, absent, late, excused
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=True)  # Reason for absence/lateness
    marked_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    class_info = relationship("Class")
    marker = relationship("User")
    
    def __repr__(self):
        return f"<AttendanceRecord(student_id={self.student_id}, date={self.date}, status='{self.status}')>"


class Grade(Base):
    """Student grades and academic performance"""
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    assessment_type = Column(String(50), nullable=False)  # assignment, exam, quiz, project
    assessment_id = Column(Integer, nullable=True)  # ID of specific assignment/exam
    assessment_name = Column(String(200), nullable=False)
    
    # Grading information
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    grade_letter = Column(String(5), nullable=True)  # A, B, C, D, F
    grade_points = Column(Float, nullable=True)  # GPA points
    percentage = Column(Float, nullable=True)
    
    # Additional information
    term = Column(String(20), nullable=False)  # semester, quarter, etc.
    academic_year = Column(String(20), nullable=False)
    comments = Column(Text, nullable=True)
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    graded_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student", back_populates="grades")
    subject = relationship("Subject")
    grader = relationship("User")
    
    def __repr__(self):
        return f"<Grade(student_id={self.student_id}, subject_id={self.subject_id}, score={self.score}/{self.max_score})>"
    
    @property
    def percentage_score(self):
        if self.max_score > 0:
            return (self.score / self.max_score) * 100
        return 0


class StudentDocument(Base):
    """Student documents and certificates"""
    __tablename__ = "student_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    document_type = Column(String(100), nullable=False)  # birth_certificate, transfer_certificate, etc.
    document_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    verifier = relationship("User", foreign_keys=[verified_by])
    
    def __repr__(self):
        return f"<StudentDocument(id={self.id}, student_id={self.student_id}, type='{self.document_type}')>"


class StudentNote(Base):
    """Notes and observations about students"""
    __tablename__ = "student_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    note_type = Column(String(50), nullable=False)  # academic, behavioral, medical, general
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    is_confidential = Column(Boolean, default=False, nullable=False)
    is_visible_to_parents = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<StudentNote(id={self.id}, student_id={self.student_id}, type='{self.note_type}')>"


class StudentAchievement(Base):
    """Student achievements, awards, and recognitions"""
    __tablename__ = "student_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    achievement_type = Column(String(100), nullable=False)  # academic, sports, arts, behavior, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    date_achieved = Column(Date, nullable=False)
    level = Column(String(50), nullable=True)  # school, district, state, national, international
    certificate_path = Column(String(500), nullable=True)
    points = Column(Integer, nullable=True)  # Achievement points
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<StudentAchievement(id={self.id}, student_id={self.student_id}, title='{self.title}')>"
