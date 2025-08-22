"""
Pydantic schemas for the Form Builder feature.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


# Schema for FormSubmission
class FormSubmissionBase(BaseModel):
    form_id: int
    data: dict


class FormSubmissionCreate(FormSubmissionBase):
    pass


class FormSubmission(FormSubmissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True