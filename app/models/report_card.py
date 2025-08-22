"""
Database models for the Report Card Builder feature.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class ReportCardTemplate(Base):
    """Model for report card templates."""

    __tablename__ = "report_card_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    fields = Column(JSON, nullable=False)  # Stores the template structure
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    report_cards = relationship("ReportCard", back_populates="template")

    def __repr__(self):
        return f"<ReportCardTemplate(id={self.id}, name='{self.name}', version={self.version})>"


class ReportCard(Base):
    """Model for individual student report cards."""

    __tablename__ = "report_cards"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("report_card_templates.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    term_id = Column(Integer, ForeignKey("exam_terms.id"), nullable=False)
    data = Column(JSON, nullable=False)  # Stores the filled report card data
    status = Column(String(20), nullable=False, default="draft")  # draft, submitted, approved
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    template = relationship("ReportCardTemplate", back_populates="report_cards")
    student = relationship("Student")
    class_info = relationship("Class")
    term = relationship("ExamTerm")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    def __repr__(self):
        return f"<ReportCard(id={self.id}, student_id={self.student_id}, class_id={self.class_id})>"