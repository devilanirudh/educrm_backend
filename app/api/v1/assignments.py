"""
Assignment management API endpoints
"""

from typing import Any, List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from app.database.session import get_db
from app.api.deps import get_current_user
from app.core.permissions import UserRole
from app.core.role_config import role_config
from app.models.user import User
from app.models.academic import Assignment, AssignmentSubmission
from app.models.form import Form, FieldType
import logging
import os
import uuid
from pathlib import Path
from app.core.config import settings

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

# Dropdown endpoints for assignment form
@router.get("/available-teachers", response_model=dict)
async def get_available_teachers_for_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get teachers who can create assignments (have class/subject assignments)"""
    
    # Check permissions - only admins and staff can view teachers
    if not role_config.can_access_module(current_user.role.value, "assignments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access assignments module"
        )
    
    # Get teachers who have class or subject assignments
    from app.models.teacher import Teacher
    from app.models.user import User
    
    # Query teachers who are either class teachers or have subject assignments
    teachers = db.query(Teacher).join(User).filter(
        Teacher.is_active == True,
        User.is_active == True
    ).distinct().all()
    
    teacher_options = []
    for teacher in teachers:
        teacher_options.append({
            "value": str(teacher.id),
            "label": f"{teacher.user.first_name} {teacher.user.last_name} ({teacher.employee_id})"
        })
    
    return {
        "teachers": teacher_options
    }


@router.get("/available-classes/{teacher_id}", response_model=dict)
async def get_available_classes_for_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get classes available for a specific teacher"""
    
    # Check permissions
    if not role_config.can_access_module(current_user.role.value, "assignments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access assignments module"
        )
    
    from app.models.academic import Class, ClassSubject
    from app.models.teacher import teacher_class_associations
    
    # Get classes where this teacher is assigned (either as class teacher or subject teacher)
    # First, try to get classes from teacher_class_associations
    try:
        classes = db.query(Class).join(
            teacher_class_associations,
            Class.id == teacher_class_associations.c.class_id
        ).filter(
            teacher_class_associations.c.teacher_id == teacher_id,
            Class.is_active == True
        ).distinct().all()
    except:
        # If join fails (e.g., no associations), start with empty list
        classes = []
    
    # Also include classes where teacher is the class teacher
    class_teacher_classes = db.query(Class).filter(
        Class.class_teacher_id == teacher_id,
        Class.is_active == True
    ).all()
    
    # Also include classes where teacher teaches subjects (from ClassSubject table)
    subject_teacher_classes = db.query(Class).join(ClassSubject).filter(
        ClassSubject.teacher_id == teacher_id,
        Class.is_active == True
    ).distinct().all()
    
    # Combine and remove duplicates
    all_classes = list(set(classes + class_teacher_classes + subject_teacher_classes))
    
    class_options = []
    for cls in all_classes:
        class_options.append({
            "value": str(cls.id),
            "label": f"{cls.name} - {cls.section}" if cls.section else cls.name
        })
    
    return {
        "classes": class_options
    }


@router.get("/available-subjects/{teacher_id}/{class_id}", response_model=dict)
async def get_available_subjects_for_teacher_class(
    teacher_id: int,
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get subjects available for a specific teacher-class combination"""
    
    # Check permissions
    if not role_config.can_access_module(current_user.role.value, "assignments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access assignments module"
        )
    
    from app.models.academic import Subject, ClassSubject
    from app.models.teacher import teacher_class_associations
    
    # Get subjects that this teacher teaches in this specific class
    subjects = db.query(Subject).join(ClassSubject).filter(
        ClassSubject.class_id == class_id,
        ClassSubject.teacher_id == teacher_id,
        Subject.is_active == True
    ).all()
    
    # Also check teacher_class_associations for this teacher-class-subject combination
    association_subjects = db.query(Subject).join(
        teacher_class_associations,
        Subject.id == teacher_class_associations.c.subject_id
    ).filter(
        teacher_class_associations.c.teacher_id == teacher_id,
        teacher_class_associations.c.class_id == class_id,
        Subject.is_active == True
    ).all()
    
    # Combine and remove duplicates
    all_subjects = list(set(subjects + association_subjects))
    
    subject_options = []
    for subject in all_subjects:
        subject_options.append({
            "value": str(subject.id),
            "label": f"{subject.name} ({subject.code})"
        })
    
    return {
        "subjects": subject_options
    }

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
    """List assignments with role-based filtering and pagination"""

    # Check permissions
    if not role_config.can_access_module(current_user.role.value, "assignments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access assignments module"
        )

    # Base query with joins
    query = db.query(Assignment).options(
        joinedload(Assignment.class_info),
        joinedload(Assignment.subject),
        joinedload(Assignment.teacher)
    )

    # Apply role-based filtering
    if current_user.role == UserRole.TEACHER:
        # Teachers see assignments they created or are assigned to teach
        from app.models.teacher import Teacher
        teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
        if teacher:
            query = query.filter(
                or_(
                    Assignment.teacher_id == teacher.id,  # Assignments they created
                    # Add more conditions if needed for assignments they're assigned to teach
                )
            )
        else:
            # If no teacher profile found, return empty list
            return {
                "assignments": [],
                "total": 0,
                "page": 1,
                "pages": 1,
                "has_next": False,
                "has_prev": False
            }
    
    elif current_user.role == UserRole.STUDENT:
        # Students see assignments for their current class
        from app.models.student import Student
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student and student.current_class_id:
            query = query.filter(Assignment.class_id == student.current_class_id)
            # Only show published assignments to students
            query = query.filter(Assignment.is_published == True)
        else:
            # If no student profile or no class assigned, return empty list
            return {
                "assignments": [],
                "total": 0,
                "page": 1,
                "pages": 1,
                "has_next": False,
                "has_prev": False
            }
    
    # Admins and staff can see all assignments (no additional filtering needed)

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

    # Order by created_at descending (newest first)
    query = query.order_by(Assignment.created_at.desc())

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
            "status": assignment.status,
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

# Student-specific endpoint to view their assignments
@router.get("/my-assignments", response_model=dict)
async def get_my_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by title or description"),
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get assignments for the current student"""
    
    # Check if user is a student
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    # Get student profile
    from app.models.student import Student
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    if not student.current_class_id:
        return {
            "assignments": [],
            "total": 0,
            "page": 1,
            "pages": 1,
            "has_next": False,
            "has_prev": False,
            "message": "No class assigned"
        }
    
    # Base query for student's assignments
    query = db.query(Assignment).options(
        joinedload(Assignment.class_info),
        joinedload(Assignment.subject),
        joinedload(Assignment.teacher)
    ).filter(
        Assignment.class_id == student.current_class_id,
        Assignment.is_published == True  # Only published assignments
    )
    
    # Apply filters
    if search:
        search_filter = or_(
            Assignment.title.ilike(f"%{search}%"),
            Assignment.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if subject_id:
        query = query.filter(Assignment.subject_id == subject_id)
    
    if status:
        query = query.filter(Assignment.status == status)
    
    # Order by due date (closest first)
    query = query.order_by(Assignment.due_date.asc())
    
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
            "status": assignment.status,
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

# Teacher-specific endpoint to view their assignments
@router.get("/my-created-assignments", response_model=dict)
async def get_my_created_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by title or description"),
    class_id: Optional[int] = Query(None, description="Filter by class"),
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get assignments created by the current teacher"""
    
    # Check if user is a teacher
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this endpoint"
        )
    
    # Get teacher profile
    from app.models.teacher import Teacher
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Base query for teacher's assignments
    query = db.query(Assignment).options(
        joinedload(Assignment.class_info),
        joinedload(Assignment.subject),
        joinedload(Assignment.teacher)
    ).filter(
        Assignment.teacher_id == teacher.id  # Only assignments created by this teacher
    )
    
    # Apply filters
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
    
    if is_published is not None:
        query = query.filter(Assignment.is_published == is_published)
    
    if status:
        query = query.filter(Assignment.status == status)
    
    # Order by created_at descending (newest first)
    query = query.order_by(Assignment.created_at.desc())
    
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
            "status": assignment.status,
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

        # Convert string IDs to integers
        try:
            class_id = int(class_id)
            subject_id = int(subject_id)
            teacher_id = int(teacher_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format. Class ID, Subject ID, and Teacher ID must be valid integers"
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
            status=assignment_data.dynamic_data.get('status', 'pending'),  # Default to pending
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

    # Check permissions - users need access to assignments module or be the teacher who created it
    if (not role_config.can_access_module(current_user.role.value, "assignments") and
        current_user.id != assignment.teacher_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access assignments module"
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
    """Delete an assignment"""

    # Check if current user has permission to access assignments module
    if not role_config.can_access_module(current_user.role.value, "assignments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access assignments module"
        )

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    try:
        db.delete(assignment)
        db.commit()
        
        logger.info(f"Assignment '{assignment.title}' deleted by {current_user.email}")
        
        return {"message": "Assignment deleted successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete assignment"
        )

@router.post("/upload-file", response_model=dict)
async def upload_assignment_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Upload a file for assignment"""
    
    # Allow students to upload files for submissions, teachers/admins for assignments
    if current_user.role not in [UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to upload files"
        )

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(allowed_types)}"
        )

    # Validate file size (5MB max)
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum size is 5MB"
        )

    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_extension = Path(file.filename).suffix if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename

        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Return file info
        file_url = f"/uploads/{unique_filename}"
        
        logger.info(f"File uploaded by {current_user.email}: {file.filename} -> {unique_filename}")

        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "file_url": file_url,
            "file_path": str(file_path),
            "file_size": len(content)
        }

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

# Assignment Submission Schemas
class AssignmentSubmissionCreate(BaseModel):
    """Schema for creating a new assignment submission"""
    submission_text: Optional[str] = None
    attachment_paths: Optional[List[str]] = None

class AssignmentSubmissionGrade(BaseModel):
    """Schema for grading an assignment submission"""
    score: float
    feedback: Optional[str] = None

# Assignment Submission Endpoints
@router.post("/{assignment_id}/submit", response_model=dict)
async def submit_assignment(
    assignment_id: int,
    submission_data: AssignmentSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Submit an assignment (student endpoint)"""
    
    # Check if current user is a student
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit assignments"
        )
    
    # Get the assignment
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if assignment is published
    if not assignment.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment is not published"
        )
    
    # Get student record
    from app.models.student import Student
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student record not found"
        )
    
    # Check if student is in the correct class
    if student.current_class_id != assignment.class_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit assignments for your class"
        )
    
    # Check if already submitted
    existing_submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_id == student.id
    ).first()
    
    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment already submitted"
        )
    
    # Check if submission is late
    is_late = datetime.now() > assignment.due_date
    
    try:
        # Create submission
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student.id,
            submission_text=submission_data.submission_text,
            attachment_paths=submission_data.attachment_paths,
            submitted_at=datetime.now(),
            is_late=is_late,
            status="submitted"
        )
        
        db.add(submission)
        
        # Don't update assignment status - let teacher manage it
        # assignment.status = "submitted"

        db.commit()
        db.refresh(submission)
        
        logger.info(f"Assignment {assignment_id} submitted by student {student.id}")
        
        return {
            "message": "Assignment submitted successfully",
            "submission_id": submission.id,
            "is_late": is_late
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit assignment"
        )

@router.get("/{assignment_id}/submissions", response_model=dict)
async def get_assignment_submissions(
    assignment_id: int,
    status: Optional[str] = Query(None, description="Filter by submission status"),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get submissions for an assignment (teacher/admin endpoint)"""
    
    # Check permissions
    if not role_config.can_access_module(current_user.role.value, "assignments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access assignments module"
        )
    
    # Get the assignment
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Build query
    query = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id
    )
    
    # Apply filters
    if status:
        query = query.filter(AssignmentSubmission.status == status)
    if student_id:
        query = query.filter(AssignmentSubmission.student_id == student_id)
    
    # Get submissions with student info
    from app.models.student import Student
    submissions = query.options(
        joinedload(AssignmentSubmission.student).joinedload(Student.user)
    ).all()
    
    # Format response
    submission_list = []
    for submission in submissions:
        submission_list.append({
            "id": submission.id,
            "student_id": submission.student_id,
            "student_name": f"{submission.student.user.first_name} {submission.student.user.last_name}",
            "student_email": submission.student.user.email,
            "submission_text": submission.submission_text,
            "attachment_paths": submission.attachment_paths,
            "submitted_at": submission.submitted_at,
            "is_late": submission.is_late,
            "status": submission.status,
            "score": submission.score,
            "feedback": submission.feedback,
            "graded_at": submission.graded_at
        })
    
    return {
        "submissions": submission_list,
        "total": len(submission_list)
    }

@router.post("/{assignment_id}/submissions/{submission_id}/grade", response_model=dict)
async def grade_submission(
    assignment_id: int,
    submission_id: int,
    grade_data: AssignmentSubmissionGrade,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Grade an assignment submission (teacher endpoint)"""
    
    # Check permissions
    if not role_config.can_access_module(current_user.role.value, "assignments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access assignments module"
        )
    
    # Get the submission
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.id == submission_id,
        AssignmentSubmission.assignment_id == assignment_id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    try:
        # Update submission with grade
        submission.score = grade_data.score
        submission.feedback = grade_data.feedback
        submission.status = "graded"
        submission.graded_by = current_user.id
        submission.graded_at = datetime.now()
        
        # Calculate grade letter (simple A-F scale)
        if grade_data.score >= 90:
            submission.grade_letter = "A"
        elif grade_data.score >= 80:
            submission.grade_letter = "B"
        elif grade_data.score >= 70:
            submission.grade_letter = "C"
        elif grade_data.score >= 60:
            submission.grade_letter = "D"
        else:
            submission.grade_letter = "F"
        
        db.commit()
        db.refresh(submission)
        
        logger.info(f"Submission {submission_id} graded by {current_user.email} with score {grade_data.score}")
        
        return {
            "message": "Submission graded successfully",
            "submission_id": submission.id,
            "score": submission.score,
            "grade_letter": submission.grade_letter
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error grading submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grade submission"
        )

# Student submission viewing endpoint
@router.get("/{assignment_id}/my-submission", response_model=dict)
async def get_my_submission(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current student's submission for an assignment"""
    
    # Check if current user is a student
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their own submissions"
        )
    
    # Get the assignment
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Get student record
    from app.models.student import Student
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student record not found"
        )
    
    # Get student's submission
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_id == student.id
    ).first()
    
    if not submission:
        return {
            "submission": None,
            "message": "No submission found for this assignment"
        }
    
    # Format response
    submission_data = {
        "id": submission.id,
        "submission_text": submission.submission_text,
        "attachment_paths": submission.attachment_paths,
        "submitted_at": submission.submitted_at,
        "is_late": submission.is_late,
        "status": submission.status,
        "score": submission.score,
        "grade_letter": submission.grade_letter,
        "feedback": submission.feedback,
        "graded_at": submission.graded_at,
        "attempt_number": submission.attempt_number
    }
    
    return {
        "submission": submission_data,
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "max_score": assignment.max_score,
            "due_date": assignment.due_date
        }
    }