"""
Assignment management API endpoints
"""

from typing import Any, List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from app.database.session import get_db
from app.api.deps import get_current_user
from app.core.permissions import UserRole
from app.core.role_config import role_config
from app.models.user import User
from app.models.academic import Assignment
from app.models.form import Form, FieldType
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def validate_dynamic_data(db: Session, dynamic_data: dict):
    """Validate dynamic data against the assignment_form schema"""
    assignment_form = db.query(Form).filter(Form.key == "assignment_form").first()
    if not assignment_form:
        raise HTTPException(status_code=404, detail="Assignment form schema not found")

    errors = {}
    for field in assignment_form.fields:
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

# Pydantic schemas for Assignment API
from pydantic import BaseModel, EmailStr

class AssignmentCreateRequest(BaseModel):
    """Schema for creating a new assignment"""
    title: str
    description: Optional[str] = None
    class_id: int
    subject_id: int
    teacher_id: int
    due_date: date
    instructions: Optional[str] = None
    max_score: Optional[float] = None
    is_published: Optional[bool] = False
    dynamic_data: Optional[dict] = None

class AssignmentUpdateRequest(BaseModel):
    """Schema for updating assignment information"""
    title: Optional[str] = None
    description: Optional[str] = None
    class_id: Optional[int] = None
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    due_date: Optional[date] = None
    instructions: Optional[str] = None
    max_score: Optional[float] = None
    is_published: Optional[bool] = None
    dynamic_data: Optional[dict] = None

class AssignmentDynamicCreateRequest(BaseModel):
    """Schema for creating an assignment from dynamic form data"""
    dynamic_data: dict

# Assignment CRUD Operations
@router.get("", response_model=dict)
async def list_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by title or description"),
    class_id: Optional[int] = Query(None, description="Filter by class"),
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    teacher_id: Optional[int] = Query(None, description="Filter by teacher"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    due_date_from: Optional[date] = Query(None, description="Filter by due date from"),
    due_date_to: Optional[date] = Query(None, description="Filter by due date to"),
    max_score_min: Optional[float] = Query(None, description="Filter by minimum max score"),
    max_score_max: Optional[float] = Query(None, description="Filter by maximum max score"),
    filters: Optional[str] = Query(None, description="Dynamic filters based on form schema"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all assignments with filtering and pagination"""

    # Base query with joins
    query = db.query(Assignment).options(
        joinedload(Assignment.class_info),
        joinedload(Assignment.subject),
        joinedload(Assignment.teacher)
    )

    # Apply static filters
    if search:
        search_filter = or_(
            Assignment.title.ilike(f"%{search}%"),
            Assignment.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if class_id:
        query = query.filter(Assignment.class_id == class_id)

    if subject_id:
        query = query.filter(Assignment.subject_id == subject_id)

    if teacher_id:
        query = query.filter(Assignment.teacher_id == teacher_id)

    if is_published is not None:
        query = query.filter(Assignment.is_published == is_published)

    if due_date_from:
        query = query.filter(Assignment.due_date >= due_date_from)

    if due_date_to:
        query = query.filter(Assignment.due_date <= due_date_to)

    if max_score_min is not None:
        query = query.filter(Assignment.max_score >= max_score_min)

    if max_score_max is not None:
        query = query.filter(Assignment.max_score <= max_score_max)

    # Apply dynamic filters
    if filters:
        try:
            assignment_form = db.query(Form).filter(Form.key == "assignment_form").first()
            if assignment_form:
                for field in assignment_form.fields:
                    if field.is_filterable and field.field_name in filters:
                        value = filters[field.field_name]
                        if value:
                            query = query.filter(Assignment.dynamic_data[field.field_name].astext == str(value))
        except Exception as e:
            logger.error(f"Error applying dynamic filters: {e}")

    # Get total count
    total = query.count()

    # Apply pagination
    assignments = query.offset(skip).limit(limit).all()

    # Format response
    assignment_list = []
    for assignment in assignments:
        assignment_data = {
            "id": assignment.id,
            "title": assignment.title,
            "description": assignment.description,
            "due_date": assignment.due_date,
            "instructions": assignment.instructions,
            "max_score": assignment.max_score,
            "is_published": assignment.is_published,
            "created_at": assignment.created_at,
            "class": {
                "id": assignment.class_info.id,
                "name": assignment.class_info.name,
                "section": assignment.class_info.section,
            } if assignment.class_info else None,
            "subject": {
                "id": assignment.subject.id,
                "name": assignment.subject.name,
                "code": assignment.subject.code,
            } if assignment.subject else None,
            "teacher": {
                "id": assignment.teacher.id,
                "first_name": assignment.teacher.user.first_name,
                "last_name": assignment.teacher.user.last_name,
            } if assignment.teacher and assignment.teacher.user else None,
            "dynamic_data": assignment.dynamic_data
        }
        assignment_list.append(assignment_data)

    return {
        "assignments": assignment_list,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
        "has_next": skip + limit < total,
        "has_prev": skip > 0
    }

@router.post("", response_model=dict)
async def create_assignment(
    assignment_data: AssignmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new assignment"""

    # Check if current user has permission to access assignments module
    if not role_config.can_access_module(current_user.role.value, "assignments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators, staff, and teachers can create assignments"
        )

    try:
        # Validate dynamic data
        if assignment_data.dynamic_data:
            validate_dynamic_data(db, assignment_data.dynamic_data)

        # Create assignment record
        assignment = Assignment(
            title=assignment_data.title,
            description=assignment_data.description,
            class_id=assignment_data.class_id,
            subject_id=assignment_data.subject_id,
            teacher_id=assignment_data.teacher_id,
            due_date=assignment_data.due_date,
            instructions=assignment_data.instructions,
            max_score=assignment_data.max_score,
            is_published=assignment_data.is_published,
            dynamic_data=assignment_data.dynamic_data
        )

        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        logger.info(f"Assignment '{assignment.title}' created by {current_user.email}")

        return {
            "message": "Assignment created successfully",
            "assignment_id": assignment.id,
            "assignment_title": assignment.title
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create assignment"
        )

@router.post("/dynamic", response_model=dict)
async def create_assignment_from_dynamic_form(
    assignment_data: AssignmentDynamicCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new assignment from dynamic form data"""

    # Log the incoming data for debugging
    logger.info(f"Creating assignment from dynamic form with data: {assignment_data.dynamic_data}")

    # Check if current user has permission to access assignments module
    if not role_config.can_access_module(current_user.role.value, "assignments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators, staff, and teachers can create assignments"
        )

    try:
        # Extract required fields from dynamic data
        title = assignment_data.dynamic_data.get('title')
        class_id = assignment_data.dynamic_data.get('class_id')
        subject_id = assignment_data.dynamic_data.get('subject_id')
        teacher_id = assignment_data.dynamic_data.get('teacher_id')
        due_date_str = assignment_data.dynamic_data.get('due_date')

        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment title is required"
            )

        if not class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class ID is required"
            )

        if not subject_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject ID is required"
            )

        if not teacher_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher ID is required"
            )

        if not due_date_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date is required"
            )

        # Parse due date
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid due date format. Use YYYY-MM-DD"
            )

        # Create assignment record
        assignment = Assignment(
            title=title,
            description=assignment_data.dynamic_data.get('description'),
            class_id=class_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            assignment_type=assignment_data.dynamic_data.get('assignment_type', 'homework'),  # Default to homework
            due_date=due_date,
            assigned_date=datetime.now().date(),  # Set to current date
            instructions=assignment_data.dynamic_data.get('instructions'),
            max_score=float(assignment_data.dynamic_data.get('max_score', 100)),  # Default to 100
            is_published=assignment_data.dynamic_data.get('is_published', False),
            dynamic_data=assignment_data.dynamic_data
        )

        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        logger.info(f"Assignment '{assignment.title}' created from dynamic form by {current_user.email}")

        return {
            "message": "Assignment created successfully",
            "assignment": {
                "id": assignment.id,
                "title": assignment.title,
                "due_date": assignment.due_date,
                "is_published": assignment.is_published
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating assignment from dynamic form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create assignment"
        )

@router.get("/{assignment_id}", response_model=dict)
async def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get assignment by ID with detailed information"""

    assignment = db.query(Assignment).options(
        joinedload(Assignment.class_info),
        joinedload(Assignment.subject),
        joinedload(Assignment.teacher)
    ).filter(Assignment.id == assignment_id).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    return {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "due_date": assignment.due_date,
        "instructions": assignment.instructions,
        "max_score": assignment.max_score,
        "is_published": assignment.is_published,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
        "class": {
            "id": assignment.class_info.id,
            "name": assignment.class_info.name,
            "section": assignment.class_info.section,
        } if assignment.class_info else None,
        "subject": {
            "id": assignment.subject.id,
            "name": assignment.subject.name,
            "code": assignment.subject.code,
        } if assignment.subject else None,
        "teacher": {
            "id": assignment.teacher.id,
            "first_name": assignment.teacher.user.first_name,
            "last_name": assignment.teacher.user.last_name,
        } if assignment.teacher and assignment.teacher.user else None,
        "dynamic_data": assignment.dynamic_data
    }

@router.put("/{assignment_id}", response_model=dict)
async def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update assignment information"""

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    # Check permissions - admin, staff, or the teacher who created it
    if (current_user.role not in [UserRole.ADMIN, UserRole.STAFF] and
        current_user.id != assignment.teacher_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    try:
        # Validate dynamic data
        if assignment_data.dynamic_data:
            validate_dynamic_data(db, assignment_data.dynamic_data)

        # Update assignment information
        if assignment_data.title is not None:
            assignment.title = assignment_data.title
        if assignment_data.description is not None:
            assignment.description = assignment_data.description
        if assignment_data.class_id is not None:
            assignment.class_id = assignment_data.class_id
        if assignment_data.subject_id is not None:
            assignment.subject_id = assignment_data.subject_id
        if assignment_data.due_date is not None:
            assignment.due_date = assignment_data.due_date
        if assignment_data.instructions is not None:
            assignment.instructions = assignment_data.instructions
        if assignment_data.max_score is not None:
            assignment.max_score = assignment_data.max_score
        if assignment_data.is_published is not None:
            assignment.is_published = assignment_data.is_published
        if assignment_data.dynamic_data is not None:
            assignment.dynamic_data = assignment_data.dynamic_data

        db.commit()

        logger.info(f"Assignment '{assignment.title}' updated by {current_user.email}")

        return {"message": "Assignment updated successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update assignment"
        )

@router.delete("/{assignment_id}", response_model=dict)
async def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Soft delete an assignment (unpublish)"""

    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and staff can delete assignments"
        )

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    try:
        # Soft delete - unpublish instead of removing
        assignment.is_published = False

        db.commit()

        logger.info(f"Assignment '{assignment.title}' unpublished by {current_user.email}")

        return {"message": "Assignment unpublished successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error unpublishing assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unpublish assignment"
        )