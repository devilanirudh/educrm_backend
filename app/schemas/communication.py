"""Communication schemas"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    notification_type: str = Field(..., pattern="^(info|warning|error|success|reminder)$")
    action_url: Optional[str] = Field(None, max_length=500)
    action_text: Optional[str] = Field(None, max_length=100)
    data: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = Field(None)
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$")
    source_type: Optional[str] = Field(None, max_length=50)
    source_id: Optional[int] = None

class NotificationCreate(NotificationBase):
    user_id: int = Field(..., gt=0)

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    is_sent: bool
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class NotificationList(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class UnreadCountResponse(BaseModel):
    count: int

class MessageBase(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    message_type: str = Field(..., pattern="^(announcement|personal|group)$")
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$")
    scheduled_at: Optional[datetime] = None

class MessageCreate(MessageBase):
    recipient_ids: List[int] = Field(..., min_items=1)
    sender_id: Optional[int] = None

class MessageResponse(MessageBase):
    id: int
    sender_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageRecipientResponse(BaseModel):
    id: int
    message_id: int
    recipient_id: int
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EmailTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    variables: Optional[List[str]] = Field(None)
    is_active: bool = True

class EmailTemplateCreate(EmailTemplateBase):
    pass

class EmailTemplateResponse(EmailTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SMSTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=160)
    variables: Optional[List[str]] = Field(None)
    is_active: bool = True

class SMSTemplateCreate(SMSTemplateBase):
    pass

class SMSTemplateResponse(SMSTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
