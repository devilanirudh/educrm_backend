from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional, List, Any, Dict
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
    jitsi_participant_id: Optional[str] = None
    jitsi_join_token: Optional[str] = None
    connection_quality: Optional[str] = None
    device_info: Optional[Any] = None
    user: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Base schema for LiveClass
class LiveClassBase(BaseModel):
    topic: str
    start_time: datetime
    duration: int
    class_id: int
    description: Optional[str] = None
    max_participants: Optional[int] = 50
    is_password_protected: Optional[bool] = False
    meeting_password: Optional[str] = None
    allow_join_before_host: Optional[bool] = True
    mute_upon_entry: Optional[bool] = True
    video_off_upon_entry: Optional[bool] = False
    enable_chat: Optional[bool] = True
    enable_whiteboard: Optional[bool] = True
    enable_screen_sharing: Optional[bool] = True
    enable_recording: Optional[bool] = True
    enable_breakout_rooms: Optional[bool] = True
    enable_polls: Optional[bool] = True
    enable_reactions: Optional[bool] = True

    @validator('class_id', pre=True)
    def convert_class_id(cls, v):
        """Convert class_id to integer if it's a string"""
        if isinstance(v, str):
            return int(v)
        return v

# Schema for creating a new LiveClass
class LiveClassCreate(LiveClassBase):
    teacher_id: Optional[int] = None  # Will be set from current user

# Schema for updating a LiveClass
class LiveClassUpdate(BaseModel):
    topic: Optional[str] = None
    start_time: Optional[datetime] = None
    duration: Optional[int] = None
    status: Optional[LiveClassStatus] = None
    recording_url: Optional[str] = None
    description: Optional[str] = None
    max_participants: Optional[int] = None
    is_password_protected: Optional[bool] = None
    meeting_password: Optional[str] = None
    allow_join_before_host: Optional[bool] = None
    mute_upon_entry: Optional[bool] = None
    video_off_upon_entry: Optional[bool] = None
    enable_chat: Optional[bool] = None
    enable_whiteboard: Optional[bool] = None
    enable_screen_sharing: Optional[bool] = None
    enable_recording: Optional[bool] = None
    enable_breakout_rooms: Optional[bool] = None
    enable_polls: Optional[bool] = None
    enable_reactions: Optional[bool] = None

# Schema for reading a LiveClass record
class LiveClass(LiveClassBase):
    id: int
    teacher_id: int
    status: LiveClassStatus
    recording_url: Optional[str] = None
    jitsi_room_name: Optional[str] = None
    jitsi_meeting_url: Optional[str] = None
    jitsi_meeting_id: Optional[str] = None
    jitsi_settings: Optional[Any] = None
    jitsi_token: Optional[str] = None
    attendance: List[ClassAttendance] = []
    teacher: Optional[Dict[str, Any]] = None
    class_: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True