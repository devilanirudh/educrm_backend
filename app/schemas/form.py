"""
Pydantic schemas for the Form Builder feature.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from app.models.form import FieldType


# Schema for FormFieldOption
class FormFieldOptionBase(BaseModel):
    label: str = Field(..., max_length=255)
    value: str = Field(..., max_length=255)
    order: int = 0


class FormFieldOptionCreate(FormFieldOptionBase):
    pass


class FormFieldOptionUpdate(FormFieldOptionBase):
    id: Optional[int] = None


class FormFieldOption(FormFieldOptionBase):
    id: int

    class Config:
        orm_mode = True


# Schema for FormField
class FormFieldBase(BaseModel):
    label: str = Field(..., max_length=255)
    field_name: str = Field(..., max_length=100)
    field_type: FieldType
    placeholder: Optional[str] = Field(None, max_length=255)
    default_value: Optional[str] = None
    is_required: bool = False
    is_filterable: bool = False
    is_visible_in_listing: bool = False
    validation_rules: Optional[dict] = None
    config: Optional[dict] = None
    order: int = 0


class FormFieldCreate(FormFieldBase):
    options: Optional[List[FormFieldOptionCreate]] = []


class FormFieldUpdate(FormFieldBase):
    id: Optional[int] = None
    options: Optional[List[FormFieldOptionUpdate]] = []


class FormField(FormFieldBase):
    id: int
    options: List[FormFieldOption] = []

    class Config:
        orm_mode = True


# Schema for Form
class FormBase(BaseModel):
    name: str = Field(..., max_length=100)
    key: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class FormCreate(FormBase):
    fields: Optional[List[FormFieldCreate]] = []


class FormUpdate(FormBase):
    fields: Optional[List[FormFieldUpdate]] = []


class Form(FormBase):
    id: int
    created_at: datetime
    updated_at: datetime
    fields: List[FormField] = []

    class Config:
        orm_mode = True


# Schema for listing forms
class FormSummary(BaseModel):
    id: int
    name: str
    key: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Schema for FormSubmission
class FormSubmissionBase(BaseModel):
    data: dict

class FormSubmissionCreate(FormSubmissionBase):
    pass

class FormSubmissionResponse(FormSubmissionBase):
    id: int
    form_id: int
    user_id: int
    submitted_at: datetime

    class Config:
        orm_mode = True