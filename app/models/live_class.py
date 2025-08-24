from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
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

    live_class_id = Column(Integer, ForeignKey("live_classes.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    live_class = relationship("LiveClass", back_populates="attendance")
    user = relationship("User", back_populates="live_class_attendance")