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


class FieldType(enum.Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    MULTI_SELECT = "multi-select"
    FILE = "file"
    TOGGLE = "toggle"
    TEXTAREA = "textarea"
    PASSWORD = "password"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    IMAGE = "image"
    CHECKBOX = "checkbox"
    RADIO = "radio"


class Form(Base):
    """Model for dynamic forms."""

    __tablename__ = "forms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    key = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
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

    fields = relationship(
        "FormField", back_populates="form", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Form(id={self.id}, key='{self.key}')>"


class FormField(Base):
    """Model for fields within a dynamic form."""

    __tablename__ = "form_fields"

    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False)
    label = Column(String(255), nullable=False)
    field_name = Column(String(100), nullable=False)
    field_type = Column(Enum(FieldType), nullable=False)
    placeholder = Column(String(255), nullable=True)
    default_value = Column(Text, nullable=True)
    is_required = Column(Boolean, default=False, nullable=False)
    is_filterable = Column(Boolean, default=False, nullable=False)
    is_visible_in_listing = Column(Boolean, default=False, nullable=False)
    validation_rules = Column(JSON, nullable=True)  # e.g., min, max, pattern
    order = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    form = relationship("Form", back_populates="fields")
    options = relationship(
        "FormFieldOption", back_populates="field", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<FormField(id={self.id}, label='{self.label}', type='{self.field_type}')>"


class FormFieldOption(Base):
    """Model for options in select, multi-select, radio, etc., fields."""

    __tablename__ = "form_field_options"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("form_fields.id"), nullable=False)
    label = Column(String(255), nullable=False)
    value = Column(String(255), nullable=False)
    order = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    field = relationship("FormField", back_populates="options")

    def __repr__(self):
        return f"<FormFieldOption(id={self.id}, label='{self.label}', value='{self.value}')>"
