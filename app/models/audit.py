"""Database model for audit logging."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database.session import Base

class ActionType(enum.Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ROLE_SWITCH = "ROLE_SWITCH"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system actions
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    details = Column(String(500), nullable=True)  # Description of the action
    resource_type = Column(String(50), nullable=True)  # User, Student, Grade, etc.
    resource_id = Column(String(50), nullable=True)  # ID of the affected resource
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', details='{self.details}')>"