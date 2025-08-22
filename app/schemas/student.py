"""
Student-related Pydantic schemas for request/response validation
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel

class StudentBase(BaseModel):
    """Base student schema with common fields"""
    student_id: str
    admission_date: date
    academic_year: str
    roll_number: Optional[str] = None
    section: Optional[str] = None
    blood_group: Optional[str] = None
    transportation_mode: Optional[str] = None
    is_hosteller: bool = False

class StudentCreate(StudentBase):
    """Schema for creating a new student"""
    user_id: int
    current_class_id: int

class StudentUpdate(BaseModel):
    """Schema for updating student information"""
    academic_year: Optional[str] = None
    roll_number: Optional[str] = None
    section: Optional[str] = None
    blood_group: Optional[str] = None
    transportation_mode: Optional[str] = None
    is_hosteller: Optional[bool] = None
    is_active: Optional[bool] = None

class StudentResponse(StudentBase):
    """Schema for student response"""
    id: int
    user: 'UserResponse'
    
    class Config:
        from_attributes = True
