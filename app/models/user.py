"""
User-related database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base
from app.core.permissions import UserRole
import enum


class User(Base):
    """Base user model for all user types"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Profile information
    profile_picture = Column(String(500), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Emergency contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)
    
    # Additional fields
    notes = Column(Text, nullable=True)
    language_preference = Column(String(5), default="en", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Relationships
    students = relationship("Student", back_populates="user", cascade="all, delete-orphan")
    library_member = relationship("LibraryMember", back_populates="user", uselist=False, cascade="all, delete-orphan")
    hosted_classes = relationship("LiveClass", back_populates="teacher", cascade="all, delete-orphan")
    teachers = relationship("Teacher", back_populates="user", cascade="all, delete-orphan")
    parent_profiles = relationship("Parent", back_populates="user", cascade="all, delete-orphan")
    
    # Communication
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    # Live Classes
    hosted_classes = relationship("LiveClass", back_populates="teacher")
    live_class_attendance = relationship("ClassAttendance", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self):
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    
    @property
    def is_teacher(self):
        return self.role == UserRole.TEACHER
    
    @property
    def is_student(self):
        return self.role == UserRole.STUDENT
    
    @property
    def is_parent(self):
        return self.role == UserRole.PARENT


class UserSession(Base):
    """User session tracking for security and analytics"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    location = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class UserPreference(Base):
    """User preferences and settings"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, key='{self.preference_key}')>"


class Parent(Base):
    """Parent profile extending user information"""
    __tablename__ = "parents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    occupation = Column(String(100), nullable=True)
    workplace = Column(String(200), nullable=True)
    work_phone = Column(String(20), nullable=True)
    relationship_to_student = Column(String(50), nullable=True)  # father, mother, guardian, etc.
    is_primary_contact = Column(Boolean, default=True, nullable=False)
    can_pickup_student = Column(Boolean, default=True, nullable=False)
    receives_notifications = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="parent_profiles")
    children = relationship("Student", secondary="parent_student_relationships", back_populates="parents")
    
    def __repr__(self):
        return f"<Parent(id={self.id}, user_id={self.user_id})>"





class SystemNotification(Base):
    """System-wide notifications and announcements"""
    __tablename__ = "system_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # info, warning, error, success
    target_roles = Column(Text, nullable=True)  # JSON array of target roles
    is_active = Column(Boolean, default=True, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("User")
    
    def __repr__(self):
        return f"<SystemNotification(id={self.id}, title='{self.title}')>"
