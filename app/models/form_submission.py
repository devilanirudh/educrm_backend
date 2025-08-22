"""
Database models for the Form Builder feature.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Enum,
    Text,
    ForeignKey,
    DateTime,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base
import enum


class FormSubmission(Base):
    """Model for dynamic forms."""

    __tablename__ = "form_submissions"

    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    data = Column(JSON, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    form = relationship("Form")

    def __repr__(self):
        return f"<FormSubmission(id={self.id}, form_id='{self.form_id}')>"