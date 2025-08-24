"""
Student-related database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Date, Table, JSON, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base
from app.models.financial import Invoice
from app.models.library import BookIssue, LibraryMember
from app.models.transport import Route
from app.models.hostel import HostelRoom
import enum
from datetime import time




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
    """Enhanced student attendance tracking"""
    __tablename__ = "attendance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("attendance_policies.id"), nullable=True)
    
    # Date and time information
    date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # present, absent, late, excused, half_day, sick_leave, personal_leave, emergency_leave
    attendance_type = Column(String(20), default='daily')  # daily, period_wise, subject_wise, activity_wise
    
    # Time tracking
    expected_check_in = Column(Time, nullable=True)
    expected_check_out = Column(Time, nullable=True)
    actual_check_in = Column(DateTime(timezone=True), nullable=True)
    actual_check_out = Column(DateTime(timezone=True), nullable=True)
    
    # Duration tracking
    total_hours = Column(Float, nullable=True)  # Actual hours attended
    expected_hours = Column(Float, nullable=True)  # Expected hours for the day
    
    # Location tracking (for future GPS integration)
    check_in_location = Column(JSON, nullable=True)  # {lat, lng, address}
    check_out_location = Column(JSON, nullable=True)
    
    # Device information
    check_in_device = Column(String(100), nullable=True)  # web, mobile, card, biometric
    check_out_device = Column(String(100), nullable=True)
    
    # Additional information
    reason = Column(Text, nullable=True)  # Reason for absence/lateness
    notes = Column(Text, nullable=True)  # Additional notes
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    marked_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    class_info = relationship("Class")
    policy = relationship("AttendancePolicy", back_populates="attendance_records")
    marker = relationship("User", foreign_keys=[marked_by])
    verifier = relationship("User", foreign_keys=[verified_by])
    
    def __repr__(self):
        return f"<AttendanceRecord(student_id={self.student_id}, date={self.date}, status='{self.status}')>"
    
    @property
    def is_late(self) -> bool:
        """Check if student was late"""
        if not self.actual_check_in or not self.expected_check_in:
            return False
        check_in_time = self.actual_check_in.time()
        return check_in_time > self.expected_check_in
    
    @property
    def late_minutes(self) -> int:
        """Calculate how many minutes late"""
        if not self.is_late:
            return 0
        check_in_time = self.actual_check_in.time()
        expected_time = self.expected_check_in
        return int((check_in_time.hour - expected_time.hour) * 60 + 
                   (check_in_time.minute - expected_time.minute))
    
    @property
    def attendance_percentage(self) -> float:
        """Calculate attendance percentage for the day"""
        if not self.expected_hours or self.expected_hours == 0:
            return 100.0 if self.status == 'present' else 0.0
        
        if not self.total_hours:
            return 0.0
        
        return min(100.0, (self.total_hours / self.expected_hours) * 100)


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


# Attendance System Models
class AttendancePolicy(Base):
    """Attendance policies and rules"""
    __tablename__ = "attendance_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Policy settings
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)  # NULL for global policies
    academic_year = Column(String(20), nullable=False)
    
    # Time settings
    school_start_time = Column(Time, nullable=False, default=time(8, 0))  # 8:00 AM
    school_end_time = Column(Time, nullable=False, default=time(15, 0))   # 3:00 PM
    late_threshold_minutes = Column(Integer, default=15)  # Minutes after start time
    early_departure_threshold_minutes = Column(Integer, default=30)  # Minutes before end time
    
    # Attendance requirements
    minimum_attendance_percentage = Column(Float, default=75.0)
    max_consecutive_absences = Column(Integer, default=5)
    max_total_absences = Column(Integer, default=30)
    
    # Notification settings
    notify_parents_on_absence = Column(Boolean, default=True)
    notify_parents_on_late = Column(Boolean, default=False)
    notify_after_consecutive_absences = Column(Integer, default=3)
    
    # Auto-marking settings
    auto_mark_absent_after_minutes = Column(Integer, nullable=True)  # NULL to disable
    allow_self_check_in = Column(Boolean, default=False)
    allow_self_check_out = Column(Boolean, default=False)
    
    # Advanced settings
    grace_period_minutes = Column(Integer, default=5)
    half_day_threshold_hours = Column(Float, default=4.0)
    working_days = Column(JSON, default=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    class_info = relationship("Class", foreign_keys=[class_id])
    creator = relationship("User", foreign_keys=[created_by])
    attendance_records = relationship("AttendanceRecord", back_populates="policy")
    
    def __repr__(self):
        return f"<AttendancePolicy(id={self.id}, name='{self.name}', class_id={self.class_id})>"


class AttendanceSession(Base):
    """Attendance sessions for period-wise tracking"""
    __tablename__ = "attendance_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    session_name = Column(String(100), nullable=False)  # e.g., "Morning Session", "Math Period"
    
    # Time settings
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    late_threshold_minutes = Column(Integer, default=5)
    
    # Session settings
    is_required = Column(Boolean, default=True)
    weight = Column(Float, default=1.0)  # Weight for attendance calculation
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    class_info = relationship("Class")
    subject = relationship("Subject")
    period_attendance = relationship("PeriodAttendance", back_populates="session")
    
    def __repr__(self):
        return f"<AttendanceSession(id={self.id}, name='{self.session_name}', class_id={self.class_id})>"


class PeriodAttendance(Base):
    """Period-wise attendance records"""
    __tablename__ = "period_attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    
    # Attendance details
    status = Column(String(20), nullable=False, default='absent')  # present, absent, late, excused
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    
    # Additional information
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    marked_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    session = relationship("AttendanceSession", back_populates="period_attendance")
    marker = relationship("User", foreign_keys=[marked_by])
    
    def __repr__(self):
        return f"<PeriodAttendance(student_id={self.student_id}, session_id={self.session_id}, date={self.date})>"


class AttendanceException(Base):
    """Attendance exceptions and overrides"""
    __tablename__ = "attendance_exceptions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    
    # Exception details
    exception_type = Column(String(50), nullable=False)  # holiday, event, emergency, etc.
    reason = Column(Text, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Effect
    mark_as_present = Column(Boolean, default=False)
    exclude_from_calculation = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<AttendanceException(student_id={self.student_id}, date={self.date}, type='{self.exception_type}')>"


class AttendanceNotification(Base):
    """Attendance notifications and alerts"""
    __tablename__ = "attendance_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # absence, late, consecutive_absence, etc.
    
    # Notification details
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    
    # Recipients
    sent_to_parents = Column(Boolean, default=False)
    sent_to_teachers = Column(Boolean, default=False)
    sent_to_admin = Column(Boolean, default=False)
    
    # Status
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    
    def __repr__(self):
        return f"<AttendanceNotification(student_id={self.student_id}, type='{self.notification_type}')>"
