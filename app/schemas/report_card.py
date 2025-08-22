"""
Pydantic schemas for the Report Card Builder feature.
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


# Report Card Template Schemas
class ReportCardTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    fields: Dict[str, Any]


class ReportCardTemplateCreate(ReportCardTemplateBase):
    pass


class ReportCardTemplateUpdate(ReportCardTemplateBase):
    pass


class ReportCardTemplate(ReportCardTemplateBase):
    id: int
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Report Card Schemas
class ReportCardBase(BaseModel):
    template_id: int
    student_id: int
    class_id: int
    term_id: int
    data: Dict[str, Any]


class ReportCardCreate(ReportCardBase):
    pass


class ReportCardUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class ReportCard(ReportCardBase):
    id: int
    status: str
    submitted_by_id: Optional[int] = None
    approved_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# API Specific Schemas
class ReportCardPublish(BaseModel):
    template_id: int
    class_ids: List[int]
    term_id: int


class ReportCardSubmit(BaseModel):
    report_card_id: int
    data: Dict[str, Any]


class ReportCardGeneratePDF(BaseModel):
    report_card_id: int