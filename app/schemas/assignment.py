"""Assignment-related Pydantic schemas"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

# Assignment Schemas

class AssignmentBase(BaseModel):
    """Base assignment schema"""
    title: str = Field(..., description="Assignment title")
    description: Optional[str] = Field(None, description="Assignment description")
    assignment_type: str = Field(..., description="Type of assignment")
    class_id: int = Field(..., description="ID of the class")
    subject_id: int = Field(..., description="ID of the subject")
    teacher_id: int = Field(..., description="ID of the teacher who created the assignment")
    assigned_date: datetime = Field(..., description="Date the assignment was assigned")
    due_date: datetime = Field(..., description="Due date for the assignment")
    attachment_paths: Optional[List[str]] = Field(None, description="List of file paths for assignment attachments")
    instructions: Optional[str] = Field(None, description="Instructions for the assignment")
    max_score: float = Field(100.0, description="Maximum score for the assignment")
    is_published: bool = Field(False, description="Whether the assignment is published to students")

class AssignmentCreate(AssignmentBase):
    """Schema for creating a new assignment"""
    pass

class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment"""
    title: Optional[str] = Field(None, description="Assignment title")
    description: Optional[str] = Field(None, description="Assignment description")
    due_date: Optional[datetime] = Field(None, description="Due date for the assignment")
    attachment_paths: Optional[List[str]] = Field(None, description="List of file paths for assignment attachments")
    instructions: Optional[str] = Field(None, description="Instructions for the assignment")
    max_score: Optional[float] = Field(None, description="Maximum score for the assignment")
    is_published: Optional[bool] = Field(None, description="Whether the assignment is published to students")

class AssignmentResponse(AssignmentBase):
    """Schema for assignment response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Assignment Submission Schemas

class AssignmentSubmissionBase(BaseModel):
    """Base assignment submission schema"""
    assignment_id: int = Field(..., description="ID of the assignment")
    student_id: int = Field(..., description="ID of the student submitting")
    submission_text: Optional[str] = Field(None, description="Text content of the submission")
    attachment_paths: Optional[List[str]] = Field(None, description="List of file paths for submission attachments")

class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    """Schema for creating a new assignment submission"""
    pass

class AssignmentSubmissionUpdate(BaseModel):
    """Schema for updating an assignment submission (grading)"""
    score: Optional[float] = Field(None, description="Score awarded for the submission")
    feedback: Optional[str] = Field(None, description="Feedback for the submission")
    status: Optional[str] = Field(None, description="Status of the submission (e.g., 'graded')")

class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    """Schema for assignment submission response"""
    id: int
    submitted_at: datetime
    status: str
    score: Optional[float]
    feedback: Optional[str]
    
    class Config:
        from_attributes = True