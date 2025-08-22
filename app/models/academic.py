"""
Academic-related database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Date, Time, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Subject(Base):
    """Academic subjects"""
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    department = Column(String(100), nullable=True)
    category = Column(String(50), nullable=True)  # core, elective, extra_curricular
    credits = Column(Integer, nullable=True)
    theory_hours = Column(Integer, nullable=True)
    practical_hours = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    teachers = relationship("Teacher", secondary="teacher_subject_associations", back_populates="subjects")
    classes = relationship("ClassSubject", back_populates="subject")
    assignments = relationship("Assignment", back_populates="subject")
    exams = relationship("Exam", back_populates="subject")
    grades = relationship("Grade", back_populates="subject")
    timetable_slots = relationship("TimetableSlot", back_populates="subject")
    
    def __repr__(self):
        return f"<Subject(id={self.id}, name='{self.name}', code='{self.code}')>"


class Class(Base):
    """School classes/grades"""
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., "Grade 1", "Class X"
    section = Column(String(10), nullable=True)  # A, B, C, etc.
    stream = Column(String(100), nullable=True) # Science, Commerce, Arts
    grade_level = Column(Integer, nullable=False)  # 1, 2, 3, ..., 12
    academic_year = Column(String(20), nullable=False)  # e.g., "2024-2025"
    max_students = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    class_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    room_number = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    class_teacher = relationship("Teacher", foreign_keys=[class_teacher_id])
    teachers = relationship("Teacher", secondary="teacher_class_associations", back_populates="classes")
    students = relationship("Student", foreign_keys="Student.current_class_id", back_populates="current_class")
    subjects = relationship("ClassSubject", back_populates="class_info")
    timetable_slots = relationship("TimetableSlot", back_populates="class_info")
    assignments = relationship("Assignment", back_populates="class_info")
    exams = relationship("Exam", back_populates="class_info")
    live_classes = relationship("LiveClass", back_populates="class_")
    
    def __repr__(self):
        return f"<Class(id={self.id}, name='{self.name}', section='{self.section}')>"
    
    @property
    def full_name(self):
        if self.section:
            return f"{self.name} - {self.section}"
        return self.name


class ClassSubject(Base):
    """Subjects assigned to classes"""
    __tablename__ = "class_subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    weekly_hours = Column(Integer, nullable=True)
    is_optional = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    class_info = relationship("Class", back_populates="subjects")
    subject = relationship("Subject", back_populates="classes")
    teacher = relationship("Teacher")
    
    def __repr__(self):
        return f"<ClassSubject(class_id={self.class_id}, subject_id={self.subject_id})>"


class TimetableSlot(Base):
    """Timetable slots for classes"""
    __tablename__ = "timetable_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    room_number = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    class_info = relationship("Class", back_populates="timetable_slots")
    subject = relationship("Subject", back_populates="timetable_slots")
    teacher = relationship("Teacher", back_populates="timetable_slots")
    
    def __repr__(self):
        return f"<TimetableSlot(id={self.id}, class_id={self.class_id}, day={self.day_of_week})>"


class Assignment(Base):
    """Student assignments"""
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    
    # Assignment details
    assignment_type = Column(String(50), nullable=False)  # homework, project, quiz, etc.
    instructions = Column(Text, nullable=True)
    max_score = Column(Float, nullable=False, default=100.0)
    
    # Dates and deadlines
    assigned_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    late_submission_allowed = Column(Boolean, default=True, nullable=False)
    late_penalty_percentage = Column(Float, nullable=True)
    
    # File attachments
    attachment_paths = Column(JSON, nullable=True)  # List of file paths
    
    # Status
    is_published = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    class_info = relationship("Class", back_populates="assignments")
    subject = relationship("Subject", back_populates="assignments")
    teacher = relationship("Teacher", back_populates="assignments_created")
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Assignment(id={self.id}, title='{self.title}', class_id={self.class_id})>"


class AssignmentSubmission(Base):
    """Student assignment submissions"""
    __tablename__ = "assignment_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # Submission content
    submission_text = Column(Text, nullable=True)
    attachment_paths = Column(JSON, nullable=True)  # List of submitted file paths
    
    # Submission details
    submitted_at = Column(DateTime(timezone=True), nullable=False)
    is_late = Column(Boolean, default=False, nullable=False)
    attempt_number = Column(Integer, default=1, nullable=False)
    
    # Grading
    score = Column(Float, nullable=True)
    grade_letter = Column(String(5), nullable=True)
    feedback = Column(Text, nullable=True)
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="submitted")  # submitted, graded, returned
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="assignment_submissions")
    grader = relationship("User")
    
    def __repr__(self):
        return f"<AssignmentSubmission(id={self.id}, assignment_id={self.assignment_id}, student_id={self.student_id})>"


class Exam(Base):
    """Examinations and tests"""
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    
    # Exam details
    exam_type = Column(String(50), nullable=False)  # unit_test, mid_term, final, quiz
    duration_minutes = Column(Integer, nullable=False)
    max_score = Column(Float, nullable=False, default=100.0)
    passing_score = Column(Float, nullable=True)
    
    # Scheduling
    exam_date = Column(DateTime(timezone=True), nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    room_number = Column(String(20), nullable=True)
    
    # Online exam settings
    is_online = Column(Boolean, default=False, nullable=False)
    auto_submit = Column(Boolean, default=True, nullable=False)
    randomize_questions = Column(Boolean, default=False, nullable=False)
    show_results_immediately = Column(Boolean, default=False, nullable=False)
    
    # Instructions and rules
    instructions = Column(Text, nullable=True)
    exam_rules = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="draft")  # draft, published, active, completed, cancelled
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    class_info = relationship("Class", back_populates="exams")
    subject = relationship("Subject", back_populates="exams")
    teacher = relationship("Teacher", back_populates="exams_created")
    questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    results = relationship("ExamResult", back_populates="exam", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Exam(id={self.id}, title='{self.title}', class_id={self.class_id})>"


class ExamQuestion(Base):
    """Questions for exams"""
    __tablename__ = "exam_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # mcq, true_false, short_answer, essay
    options = Column(JSON, nullable=True)  # For MCQ questions
    correct_answer = Column(Text, nullable=True)
    points = Column(Float, nullable=False, default=1.0)
    order_number = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    exam = relationship("Exam", back_populates="questions")
    answers = relationship("ExamAnswer", back_populates="question", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExamQuestion(id={self.id}, exam_id={self.exam_id}, type='{self.question_type}')>"


class ExamResult(Base):
    """Student exam results"""
    __tablename__ = "exam_results"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # Result details
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    grade_letter = Column(String(5), nullable=True)
    rank = Column(Integer, nullable=True)
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    time_taken_minutes = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="completed")  # in_progress, completed, submitted
    is_passed = Column(Boolean, nullable=True)
    
    # Feedback
    teacher_comments = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    exam = relationship("Exam", back_populates="results")
    student = relationship("Student", back_populates="exam_results")
    answers = relationship("ExamAnswer", back_populates="result", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExamResult(id={self.id}, exam_id={self.exam_id}, student_id={self.student_id}, score={self.score})>"


class ExamAnswer(Base):
    """Student answers to exam questions"""
    __tablename__ = "exam_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("exam_results.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("exam_questions.id"), nullable=False)
    answer_text = Column(Text, nullable=True)
    selected_option = Column(String(10), nullable=True)  # For MCQ questions
    is_correct = Column(Boolean, nullable=True)
    points_earned = Column(Float, nullable=True)
    teacher_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    result = relationship("ExamResult", back_populates="answers")
    question = relationship("ExamQuestion", back_populates="answers")
    
    def __repr__(self):
        return f"<ExamAnswer(id={self.id}, result_id={self.result_id}, question_id={self.question_id})>"


