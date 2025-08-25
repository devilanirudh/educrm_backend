from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
import enum

# Import Class model to ensure it's available for relationships
from app.models.academic import Class

class LiveClassStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"

class LiveClass(Base):
    __tablename__ = "live_classes"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    start_time = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)  # in minutes
    status = Column(Enum(LiveClassStatus), default=LiveClassStatus.SCHEDULED)
    recording_url = Column(String, nullable=True)

    # Jitsi Meet specific fields
    jitsi_room_name = Column(String(255), unique=True, index=True, nullable=True)
    jitsi_meeting_url = Column(String(500), nullable=True)
    jitsi_meeting_id = Column(String(255), nullable=True)
    jitsi_settings = Column(JSON, nullable=True)  # Store Jitsi meeting settings
    jitsi_token = Column(Text, nullable=True)  # JWT token for authentication
    
    # Additional fields
    description = Column(Text, nullable=True)
    max_participants = Column(Integer, default=50, nullable=False)
    is_password_protected = Column(Boolean, default=False, nullable=False)
    meeting_password = Column(String(100), nullable=True)
    allow_join_before_host = Column(Boolean, default=True, nullable=False)
    mute_upon_entry = Column(Boolean, default=True, nullable=False)
    video_off_upon_entry = Column(Boolean, default=False, nullable=False)
    
    # Host controls
    enable_chat = Column(Boolean, default=True, nullable=False)
    enable_whiteboard = Column(Boolean, default=True, nullable=False)
    enable_screen_sharing = Column(Boolean, default=True, nullable=False)
    enable_recording = Column(Boolean, default=True, nullable=False)
    enable_breakout_rooms = Column(Boolean, default=True, nullable=False)
    enable_polls = Column(Boolean, default=True, nullable=False)
    enable_reactions = Column(Boolean, default=True, nullable=False)

    teacher_id = Column(Integer, ForeignKey("users.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))

    teacher = relationship("User", back_populates="hosted_classes")
    class_ = relationship("Class", back_populates="live_classes")
    attendance = relationship("ClassAttendance", back_populates="live_class")

class ClassAttendance(Base):
    __tablename__ = "class_attendance"

    id = Column(Integer, primary_key=True, index=True)
    join_time = Column(DateTime, nullable=False)
    leave_time = Column(DateTime, nullable=True)
    
    # Jitsi specific attendance fields
    jitsi_participant_id = Column(String(255), nullable=True)
    jitsi_join_token = Column(Text, nullable=True)
    connection_quality = Column(String(50), nullable=True)  # good, poor, etc.
    device_info = Column(JSON, nullable=True)  # browser, OS, etc.

    live_class_id = Column(Integer, ForeignKey("live_classes.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    live_class = relationship("LiveClass", back_populates="attendance")
    user = relationship("User", back_populates="live_class_attendance")