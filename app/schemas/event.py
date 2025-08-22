"""Pydantic schemas for events."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.event import EventAudience

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    audience: EventAudience

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    pass

class EventResponse(EventBase):
    id: int

    class Config:
        orm_mode = True