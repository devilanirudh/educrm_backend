from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.live_class import LiveClassStatus

# Base schema for ClassAttendance
class ClassAttendanceBase(BaseModel):
    user_id: int
    live_class_id: int

# Schema for creating a new ClassAttendance record
class ClassAttendanceCreate(ClassAttendanceBase):
    join_time: datetime

# Schema for updating a ClassAttendance record
class ClassAttendanceUpdate(BaseModel):
    leave_time: Optional[datetime] = None

# Schema for reading a ClassAttendance record
class ClassAttendance(ClassAttendanceBase):
    id: int
    join_time: datetime
    leave_time: Optional[datetime] = None

    class Config:
        orm_mode = True

# Base schema for LiveClass
class LiveClassBase(BaseModel):
    topic: str
    start_time: datetime
    duration: int
    teacher_id: int
    class_id: int

# Schema for creating a new LiveClass
class LiveClassCreate(LiveClassBase):
    pass

# Schema for updating a LiveClass
class LiveClassUpdate(BaseModel):
    topic: Optional[str] = None
    start_time: Optional[datetime] = None
    duration: Optional[int] = None
    status: Optional[LiveClassStatus] = None
    recording_url: Optional[str] = None

# Schema for reading a LiveClass record
class LiveClass(LiveClassBase):
    id: int
    status: LiveClassStatus
    recording_url: Optional[str] = None
    attendance: List[ClassAttendance] = []

    class Config:
        orm_mode = True