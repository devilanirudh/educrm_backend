"""Pydantic schemas for audit logs."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AuditLogBase(BaseModel):
    user_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True