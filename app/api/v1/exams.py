"""
Exam management API endpoints
"""

from typing import Any, List, Optional
from datetime import date, datetime, time
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from app.database.session import get_db
from app.api.deps import get_current_user
from app.core.permissions import UserRole
from app.core.role_config import role_config
from app.models.user import User
from app.models.academic import Exam
from app.models.form import Form, FieldType
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def validate_dynamic_data(db: Session, dynamic_data: dict):
    """Validate dynamic data against the exam_form schema"""
    exam_form = db.query(Form).filter(Form.key == "exam_form").first()
    if not exam_form:
        raise HTTPException(status_code=404, detail="Exam form schema not found")

    errors = {}
    for field in exam_form.fields:
        if field.is_required and field.field_name not in dynamic_data:
            errors[field.field_name] = "This field is required"

        if field.field_name in dynamic_data:
            value = dynamic_data[field.field_name]
            if field.field_type == FieldType.NUMBER and not isinstance(value, (int, float)):
                errors[field.field_name] = "Must be a number"
            elif field.field_type == FieldType.DATE:
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    errors[field.field_name] = "Invalid date format. Use YYYY-MM-DD"

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors}
        )

# Pydantic schemas for Exam API
from pydantic import BaseModel, EmailStr

class ExamCreateRequest(BaseModel):
    """Schema for creating a new exam"""
    name: str
    description: Optional[str] = None
    class_id: int
    exam_date: date
    start_time: str
    end_time: str
    duration_minutes: int
    total_marks: float
    passing_marks: Optional[float] = None
    instructions: Optional[str] = None
    status: Optional[str] = "upcoming"
    dynamic_data: Optional[dict] = None

class ExamUpdateRequest(BaseModel):
    """Schema for updating exam information"""
    name: Optional[str] = None
    description: Optional[str] = None
    class_id: Optional[int] = None
    exam_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_marks: Optional[float] = None
    passing_marks: Optional[float] = None
    instructions: Optional[str] = None
    status: Optional[str] = None
    dynamic_data: Optional[dict] = None

class ExamDynamicCreateRequest(BaseModel):
    """Schema for creating an exam from dynamic form data"""
    dynamic_data: dict

# Exam CRUD Operations
@router.get("", response_model=dict)
async def list_exams(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or title"),
    class_id: Optional[int] = Query(None, description="Filter by class"),
    status: Optional[str] = Query(None, description="Filter by status"),
    exam_date_from: Optional[date] = Query(None, description="Filter by exam date from"),
    exam_date_to: Optional[date] = Query(None, description="Filter by exam date to"),
    max_score_min: Optional[float] = Query(None, description="Filter by minimum max score"),
    max_score_max: Optional[float] = Query(None, description="Filter by maximum max score"),
    filters: Optional[str] = Query(None, description="Dynamic filters based on form schema"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all exams with filtering and pagination"""

    # Base query with joins
    query = db.query(Exam).options(
        joinedload(Exam.class_info)
    )

    # Apply static filters
    if search:
        search_filter = or_(
            Exam.title.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if class_id:
        query = query.filter(Exam.class_id == class_id)

    if status:
        query = query.filter(Exam.status == status)

    if exam_date_from:
        query = query.filter(Exam.exam_date >= exam_date_from)

    if exam_date_to:
        query = query.filter(Exam.exam_date <= exam_date_to)

    if max_score_min is not None:
        query = query.filter(Exam.max_score >= max_score_min)

    if max_score_max is not None:
        query = query.filter(Exam.max_score <= max_score_max)

    # Apply dynamic filters
    if filters:
        try:
            exam_form = db.query(Form).filter(Form.key == "exam_form").first()
            if exam_form:
                for field in exam_form.fields:
                    if field.is_filterable and field.field_name in filters:
                        value = filters[field.field_name]
                        if value:
                            query = query.filter(Exam.dynamic_data[field.field_name].astext == str(value))
        except Exception as e:
            logger.error(f"Error applying dynamic filters: {e}")

    # Get total count
    total = query.count()

    # Apply pagination
    exams = query.offset(skip).limit(limit).all()

    # Format response
    exam_list = []
    for exam in exams:
        exam_data = {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "exam_date": exam.exam_date,
            "start_time": exam.start_time,
            "end_time": exam.end_time,
            "duration_minutes": exam.duration_minutes,
            "max_score": exam.max_score,
            "passing_score": exam.passing_score,
            "instructions": exam.instructions,
            "status": exam.status,
            "created_at": exam.created_at,
            "class": {
                "id": exam.class_info.id,
                "name": exam.class_info.name,
                "section": exam.class_info.section,
            } if exam.class_info else None,
            "dynamic_data": exam.dynamic_data
        }
        exam_list.append(exam_data)

    return {
        "exams": exam_list,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
        "has_next": skip + limit < total,
        "has_prev": skip > 0
    }

@router.post("", response_model=dict)
async def create_exam(
    exam_data: ExamCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new exam"""

    # Check if current user has permission to access exams module
    if not role_config.can_access_module(current_user.role.value, "exams"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and staff can create exams"
        )

    try:
        # Validate dynamic data
        if exam_data.dynamic_data:
            validate_dynamic_data(db, exam_data.dynamic_data)

        # Check if exam with same title already exists
        existing_exam = db.query(Exam).filter(Exam.title == exam_data.name).first()
        if existing_exam:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exam with this title already exists"
            )

        # Create exam record
        exam = Exam(
            title=exam_data.name,
            description=exam_data.description,
            class_id=exam_data.class_id,
            subject_id=1,  # Default subject ID
            teacher_id=1,  # Default teacher ID
            exam_type='unit_test',  # Default exam type
            exam_date=exam_data.exam_date,
            start_time=exam_data.start_time,
            end_time=exam_data.end_time,
            duration_minutes=exam_data.duration_minutes,
            max_score=exam_data.total_marks,
            passing_score=exam_data.passing_marks,
            instructions=exam_data.instructions,
            status=exam_data.status,
            dynamic_data=exam_data.dynamic_data
        )

        db.add(exam)
        db.commit()
        db.refresh(exam)

        logger.info(f"Exam '{exam.title}' created by {current_user.email}")

        return {
            "message": "Exam created successfully",
            "exam_id": exam.id,
            "exam_name": exam.title
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exam"
        )

@router.post("/dynamic", response_model=dict)
async def create_exam_from_dynamic_form(
    exam_data: ExamDynamicCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new exam from dynamic form data"""

    # Log the incoming data for debugging
    logger.info(f"Creating exam from dynamic form with data: {exam_data.dynamic_data}")

    # Check if current user has permission to access exams module
    if not role_config.can_access_module(current_user.role.value, "exams"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and staff can create exams"
        )

    try:
        # Extract required fields from dynamic data
        name = exam_data.dynamic_data.get('name')
        exam_id = exam_data.dynamic_data.get('exam_id')
        class_id = exam_data.dynamic_data.get('class_id')
        exam_date_str = exam_data.dynamic_data.get('exam_date')
        start_time = exam_data.dynamic_data.get('start_time')
        end_time = exam_data.dynamic_data.get('end_time')
        duration_minutes = exam_data.dynamic_data.get('duration_minutes')
        total_marks = exam_data.dynamic_data.get('total_marks')
        exam_status = exam_data.dynamic_data.get('status', 'upcoming')

        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exam name is required"
            )

        if not exam_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exam ID is required"
            )

        if not class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class ID is required"
            )

        if not exam_date_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exam date is required"
            )

        if not start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time is required"
            )

        if not end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time is required"
            )

        if not duration_minutes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration is required"
            )

        if not total_marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total marks is required"
            )

        # Parse exam date
        try:
            exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid exam date format. Use YYYY-MM-DD"
            )

        # Parse start and end times
        try:
            start_time_obj = datetime.strptime(start_time, "%H:%M").time() if start_time else None
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start time format. Use HH:MM"
            )

        try:
            end_time_obj = datetime.strptime(end_time, "%H:%M").time() if end_time else None
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end time format. Use HH:MM"
            )

        # Check if exam with same title already exists
        existing_exam = db.query(Exam).filter(Exam.title == name).first()
        if existing_exam:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exam with this title already exists"
            )

        # Create exam record
        exam = Exam(
            title=name,  # Use title instead of name
            description=exam_data.dynamic_data.get('description'),
            class_id=class_id,
            subject_id=exam_data.dynamic_data.get('subject_id', 1),  # Default subject ID
            teacher_id=exam_data.dynamic_data.get('teacher_id', 1),  # Default teacher ID
            exam_type=exam_data.dynamic_data.get('exam_type', 'unit_test'),  # Default exam type
            duration_minutes=int(duration_minutes),
            max_score=float(total_marks),  # Use max_score instead of total_marks
            passing_score=float(exam_data.dynamic_data.get('passing_marks', 50)) if exam_data.dynamic_data.get('passing_marks') else None,
            exam_date=exam_date,
            start_time=start_time_obj,
            end_time=end_time_obj,
            instructions=exam_data.dynamic_data.get('instructions'),
            status=exam_status,  # Use exam_status instead of status to avoid conflict
            dynamic_data=exam_data.dynamic_data
        )

        db.add(exam)
        db.commit()
        db.refresh(exam)

        logger.info(f"Exam '{exam.title}' created from dynamic form by {current_user.email}")

        return {
            "message": "Exam created successfully",
            "exam": {
                "id": exam.id,
                "title": exam.title,
                "exam_date": exam.exam_date,
                "status": exam.status
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating exam from dynamic form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exam"
        )

@router.get("/{exam_id}", response_model=dict)
async def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get exam by ID with detailed information"""

    exam = db.query(Exam).options(
        joinedload(Exam.class_info)
    ).filter(Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    return {
        "id": exam.id,
        "title": exam.title,
        "description": exam.description,
        "exam_date": exam.exam_date,
        "start_time": exam.start_time,
        "end_time": exam.end_time,
        "duration_minutes": exam.duration_minutes,
        "max_score": exam.max_score,
        "passing_score": exam.passing_score,
        "instructions": exam.instructions,
        "status": exam.status,
        "created_at": exam.created_at,
        "updated_at": exam.updated_at,
        "class": {
            "id": exam.class_info.id,
            "name": exam.class_info.name,
            "section": exam.class_info.section,
        } if exam.class_info else None,
        "dynamic_data": exam.dynamic_data
    }

@router.put("/{exam_id}", response_model=dict)
async def update_exam(
    exam_id: int,
    exam_data: ExamUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update exam information"""

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Check permissions - admin or staff can update
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    try:
        # Validate dynamic data
        if exam_data.dynamic_data:
            validate_dynamic_data(db, exam_data.dynamic_data)

        # Update exam information
        if exam_data.name is not None:
            exam.name = exam_data.name
        if exam_data.description is not None:
            exam.description = exam_data.description
        if exam_data.exam_id is not None:
            exam.exam_id = exam_data.exam_id
        if exam_data.class_id is not None:
            exam.class_id = exam_data.class_id
        if exam_data.exam_date is not None:
            exam.exam_date = exam_data.exam_date
        if exam_data.start_time is not None:
            exam.start_time = exam_data.start_time
        if exam_data.end_time is not None:
            exam.end_time = exam_data.end_time
        if exam_data.duration_minutes is not None:
            exam.duration_minutes = exam_data.duration_minutes
        if exam_data.total_marks is not None:
            exam.total_marks = exam_data.total_marks
        if exam_data.passing_marks is not None:
            exam.passing_marks = exam_data.passing_marks
        if exam_data.instructions is not None:
            exam.instructions = exam_data.instructions
        if exam_data.status is not None:
            exam.status = exam_data.status
        if exam_data.dynamic_data is not None:
            exam.dynamic_data = exam_data.dynamic_data

        db.commit()

        logger.info(f"Exam '{exam.name}' ({exam.exam_id}) updated by {current_user.email}")

        return {"message": "Exam updated successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update exam"
        )

@router.delete("/{exam_id}", response_model=dict)
async def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Soft delete an exam (cancel)"""

    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and staff can delete exams"
        )

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    try:
        # Soft delete - cancel instead of removing
        exam.status = "cancelled"

        db.commit()

        logger.info(f"Exam '{exam.name}' ({exam.exam_id}) cancelled by {current_user.email}")

        return {"message": "Exam cancelled successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel exam"
        )