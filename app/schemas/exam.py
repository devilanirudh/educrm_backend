"""Exam and Date-sheet related Pydantic schemas"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, time, datetime

# ExamTerm Schemas

class ExamTermBase(BaseModel):
    """Base exam term schema"""
    name: str = Field(..., description="Exam term name")
    academic_year: str = Field(..., description="Academic year")
    start_date: Optional[date] = Field(None, description="Start date of the term")
    end_date: Optional[date] = Field(None, description="End date of the term")
    is_active: bool = Field(True, description="Whether the term is active")

class ExamTermCreate(ExamTermBase):
    """Schema for creating a new exam term"""
    pass

class ExamTermUpdate(BaseModel):
    """Schema for updating an exam term"""
    name: Optional[str] = Field(None, description="Exam term name")
    academic_year: Optional[str] = Field(None, description="Academic year")
    start_date: Optional[date] = Field(None, description="Start date of the term")
    end_date: Optional[date] = Field(None, description="End date of the term")
    is_active: Optional[bool] = Field(None, description="Whether the term is active")

class ExamTermResponse(ExamTermBase):
    """Schema for exam term response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# DateSheetEntry Schemas

class DateSheetEntryBase(BaseModel):
    """Base date-sheet entry schema"""
    subject_id: int = Field(..., description="ID of the subject")
    exam_date: date = Field(..., description="Date of the exam")
    start_time: time = Field(..., description="Start time of the exam")
    end_time: time = Field(..., description="End time of the exam")
    room_number: Optional[str] = Field(None, description="Room number for the exam")
    max_marks: int = Field(..., description="Maximum marks for the exam")
    exam_type: str = Field("Theory", description="Type of the exam (e.g., Theory, Practical)")

class DateSheetEntryCreate(DateSheetEntryBase):
    """Schema for creating a new date-sheet entry"""
    pass

class DateSheetEntryUpdate(DateSheetEntryBase):
    """Schema for updating a date-sheet entry"""
    pass

class DateSheetEntryResponse(DateSheetEntryBase):
    """Schema for date-sheet entry response"""
    id: int

    class Config:
        from_attributes = True

# DateSheet Schemas

class DateSheetBase(BaseModel):
    """Base date-sheet schema"""
    class_id: int = Field(..., description="ID of the class")
    term_id: int = Field(..., description="ID of the exam term")
    status: str = Field("draft", description="Status of the date-sheet (draft, published, archived)")

class DateSheetCreate(DateSheetBase):
    """Schema for creating a new date-sheet"""
    entries: List[DateSheetEntryCreate] = Field(..., description="List of date-sheet entries")

class DateSheetUpdate(BaseModel):
    """Schema for updating a date-sheet"""
    status: Optional[str] = Field(None, description="Status of the date-sheet")
    entries: Optional[List[DateSheetEntryUpdate]] = Field(None, description="List of date-sheet entries")

class DateSheetResponse(DateSheetBase):
    """Schema for date-sheet response"""
    id: int
    entries: List[DateSheetEntryResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True