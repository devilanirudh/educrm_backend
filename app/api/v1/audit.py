"""API endpoints for audit logs."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/logs/recent", response_model=List[AuditLogResponse])
async def get_recent_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the 10 most recent audit logs"""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    return logs