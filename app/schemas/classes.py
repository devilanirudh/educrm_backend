"""Class-related Pydantic schemas"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date


class ClassBase(BaseModel):
    """Base class schema"""
    name: str = Field(..., description="Class name (e.g., 'Grade 1', 'Class X')")
    section: Optional[str] = Field(None, description="Class section (e.g., 'A', 'B')")
    grade_level: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    academic_year: str = Field(..., description="Academic year (e.g., '2024-2025')")
    max_students: Optional[int] = Field(None, ge=1, description="Maximum number of students")
    description: Optional[str] = Field(None, description="Class description")
    room_number: Optional[str] = Field(None, description="Room number")
    is_active: bool = Field(True, description="Whether the class is active")


class ClassCreate(ClassBase):
    """Schema for creating a new class"""
    class_teacher_id: Optional[int] = Field(None, description="ID of the class teacher")


class ClassUpdate(BaseModel):
    """Schema for updating a class"""
    name: Optional[str] = Field(None, description="Class name")
    section: Optional[str] = Field(None, description="Class section")
    grade_level: Optional[int] = Field(None, ge=1, le=12, description="Grade level")
    academic_year: Optional[str] = Field(None, description="Academic year")
    max_students: Optional[int] = Field(None, ge=1, description="Maximum number of students")
    description: Optional[str] = Field(None, description="Class description")
    room_number: Optional[str] = Field(None, description="Room number")
    class_teacher_id: Optional[int] = Field(None, description="ID of the class teacher")
    is_active: Optional[bool] = Field(None, description="Whether the class is active")


class ClassResponse(ClassBase):
    """Schema for class response"""
    id: int
    class_teacher_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClassListResponse(BaseModel):
    """Schema for paginated class list response"""
    data: List[ClassResponse]
    total: int
    skip: int
    limit: int


class ClassSubjectBase(BaseModel):
    """Base class subject schema"""
    subject_id: int = Field(..., description="ID of the subject")
    teacher_id: Optional[int] = Field(None, description="ID of the teacher")
    weekly_hours: Optional[int] = Field(None, ge=1, description="Weekly hours for this subject")
    is_optional: bool = Field(False, description="Whether this subject is optional")


class ClassSubjectCreate(ClassSubjectBase):
    """Schema for creating a class subject"""
    pass


class ClassSubjectResponse(ClassSubjectBase):
    """Schema for class subject response"""
    id: int
    class_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ClassWithSubjects(ClassResponse):
    """Schema for class with subjects"""
    subjects: List[ClassSubjectResponse] = []


class ClassWithStudents(ClassResponse):
    """Schema for class with students"""
    student_count: int = 0


class ClassStats(BaseModel):
    """Schema for class statistics"""
    total_classes: int
    active_classes: int
    total_students: int
    grade_distribution: List[Dict[str, Any]]


class ClassTeacherInfo(BaseModel):
    """Schema for class teacher information"""
    id: int
    employee_id: str
    full_name: str
    specialization: Optional[str]
    department: Optional[str]


class ClassTeachersResponse(BaseModel):
    """Schema for class teachers response"""
    class_teacher: Optional[ClassTeacherInfo]
    subject_teachers: List[ClassTeacherInfo]
