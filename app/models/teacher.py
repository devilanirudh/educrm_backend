"""
Teacher-related database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Date, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base




# Association table for teacher-subject relationships
teacher_subject_associations = Table(
    'teacher_subject_associations',
    Base.metadata,
    Column('teacher_id', Integer, ForeignKey('teachers.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

# Association table for teacher-class relationships
teacher_class_associations = Table(
    'teacher_class_associations',
    Base.metadata,
    Column('teacher_id', Integer, ForeignKey('teachers.id'), primary_key=True),
    Column('class_id', Integer, ForeignKey('classes.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), nullable=True),
    Column('is_class_teacher', Boolean, default=False),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)


class Teacher(Base):
    """Teacher profile and professional information"""
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Professional Information
    qualifications = Column(String(200), nullable=True)
    specialization = Column(String(200), nullable=True)
    experience = Column(Integer, nullable=True)
    hire_date = Column(Date, nullable=False)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)  # Principal, Vice Principal, Head Teacher, etc.
    
    # Employment Details
    employment_type = Column(String(50), nullable=False)  # permanent, contract, part_time, substitute
    salary = Column(Float, nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    bank_name = Column(String(100), nullable=True)
    bank_ifsc = Column(String(20), nullable=True)
    
    # Contact and Emergency
    alternative_phone = Column(String(20), nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)
    
    # Professional Development
    last_appraisal_date = Column(Date, nullable=True)
    next_appraisal_date = Column(Date, nullable=True)
    performance_rating = Column(Float, nullable=True)  # Out of 5
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    resignation_date = Column(Date, nullable=True)
    resignation_reason = Column(Text, nullable=True)
    
    # Additional Information
    teaching_philosophy = Column(Text, nullable=True)
    awards_recognitions = Column(Text, nullable=True)
    publications = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Dynamic data for form builder
    dynamic_data = Column(JSON, nullable=True)

    # Permissions
    can_create_class = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="teachers")
    subjects = relationship("Subject", secondary="teacher_subject_associations", back_populates="teachers")
    classes = relationship("Class", secondary="teacher_class_associations", back_populates="teachers")
    
    # Teaching relationships
    assignments_created = relationship("Assignment", back_populates="teacher", cascade="all, delete-orphan")
    exams_created = relationship("Exam", back_populates="teacher", cascade="all, delete-orphan")
    
    # Attendance and schedule
    attendance_records = relationship("TeacherAttendance", back_populates="teacher", cascade="all, delete-orphan")
    timetable_slots = relationship("TimetableSlot", back_populates="teacher", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Teacher(id={self.id}, employee_id='{self.employee_id}', user_id={self.user_id})>"
    
    @property
    def full_name(self):
        return self.user.full_name if self.user else "Unknown"


class TeacherAttendance(Base):
    """Teacher attendance tracking"""
    __tablename__ = "teacher_attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False)  # present, absent, half_day, leave
    leave_type = Column(String(50), nullable=True)  # sick, casual, maternity, etc.
    reason = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    hours_worked = Column(Float, nullable=True)
    overtime_hours = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    teacher = relationship("Teacher", back_populates="attendance_records")
    approver = relationship("User")
    
    def __repr__(self):
        return f"<TeacherAttendance(teacher_id={self.teacher_id}, date={self.date}, status='{self.status}')>"


class TeacherLeave(Base):
    """Teacher leave applications and management"""
    __tablename__ = "teacher_leaves"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    leave_type = Column(String(50), nullable=False)  # sick, casual, maternity, study, etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected, cancelled
    applied_date = Column(Date, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_date = Column(Date, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    substitute_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    document_path = Column(String(500), nullable=True)  # Medical certificate, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    teacher = relationship("Teacher", foreign_keys=[teacher_id])
    approver = relationship("User")
    substitute_teacher = relationship("Teacher", foreign_keys=[substitute_teacher_id])
    
    def __repr__(self):
        return f"<TeacherLeave(id={self.id}, teacher_id={self.teacher_id}, type='{self.leave_type}')>"


class TeacherQualification(Base):
    """Teacher qualifications and certifications"""
    __tablename__ = "teacher_qualifications"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    qualification_type = Column(String(100), nullable=False)  # degree, diploma, certificate
    qualification_name = Column(String(200), nullable=False)
    institution = Column(String(200), nullable=False)
    year_completed = Column(Integer, nullable=True)
    grade_percentage = Column(Float, nullable=True)
    certificate_number = Column(String(100), nullable=True)
    certificate_path = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    teacher = relationship("Teacher")
    verifier = relationship("User")
    
    def __repr__(self):
        return f"<TeacherQualification(id={self.id}, teacher_id={self.teacher_id}, name='{self.qualification_name}')>"


class TeacherTraining(Base):
    """Teacher training and professional development records"""
    __tablename__ = "teacher_trainings"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    training_name = Column(String(200), nullable=False)
    training_type = Column(String(100), nullable=False)  # workshop, seminar, course, conference
    provider = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    duration_hours = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    certificate_obtained = Column(Boolean, default=False, nullable=False)
    certificate_path = Column(String(500), nullable=True)
    feedback_rating = Column(Float, nullable=True)  # Out of 5
    feedback_comments = Column(Text, nullable=True)
    is_mandatory = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), nullable=False, default="registered")  # registered, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    teacher = relationship("Teacher")
    
    def __repr__(self):
        return f"<TeacherTraining(id={self.id}, teacher_id={self.teacher_id}, name='{self.training_name}')>"


class TeacherPerformance(Base):
    """Teacher performance evaluations and appraisals"""
    __tablename__ = "teacher_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    evaluation_period = Column(String(20), nullable=False)  # e.g., "2024-Q1", "2024-Annual"
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Performance metrics (out of 5)
    teaching_effectiveness = Column(Float, nullable=True)
    student_engagement = Column(Float, nullable=True)
    subject_knowledge = Column(Float, nullable=True)
    classroom_management = Column(Float, nullable=True)
    punctuality = Column(Float, nullable=True)
    communication_skills = Column(Float, nullable=True)
    professional_development = Column(Float, nullable=True)
    innovation = Column(Float, nullable=True)
    
    # Overall rating
    overall_rating = Column(Float, nullable=False)
    grade = Column(String(5), nullable=True)  # A, B, C, D, E
    
    # Comments and feedback
    strengths = Column(Text, nullable=True)
    areas_of_improvement = Column(Text, nullable=True)
    goals_next_period = Column(Text, nullable=True)
    evaluator_comments = Column(Text, nullable=True)
    teacher_comments = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="draft")  # draft, completed, acknowledged
    evaluation_date = Column(Date, nullable=False)
    acknowledgment_date = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    teacher = relationship("Teacher")
    evaluator = relationship("User")
    
    def __repr__(self):
        return f"<TeacherPerformance(id={self.id}, teacher_id={self.teacher_id}, rating={self.overall_rating})>"


class TeacherDocument(Base):
    """Teacher documents and certificates storage"""
    __tablename__ = "teacher_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    document_type = Column(String(100), nullable=False)  # resume, certificate, id_proof, etc.
    document_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    teacher = relationship("Teacher")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    verifier = relationship("User", foreign_keys=[verified_by])
    
    def __repr__(self):
        return f"<TeacherDocument(id={self.id}, teacher_id={self.teacher_id}, type='{self.document_type}')>"
