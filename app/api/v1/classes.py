"""
Class management API endpoints
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
from app.models.academic import Class, ClassSubject
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.form import Form, FieldType
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def validate_dynamic_data(db: Session, dynamic_data: dict):
    """Validate dynamic data against the class_form schema"""
    class_form = db.query(Form).filter(Form.key == "class_form").first()
    if not class_form:
        raise HTTPException(status_code=404, detail="Class form schema not found")

    errors = {}
    for field in class_form.fields:
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

# Pydantic schemas for Class API
from pydantic import BaseModel, EmailStr

class ClassCreateRequest(BaseModel):
    """Schema for creating a new class"""
    name: str
    section: str
    stream: Optional[str] = None
    grade_level: int
    academic_year: str
    max_students: Optional[int] = None
    room_number: Optional[str] = None
    class_teacher_id: Optional[int] = None
    dynamic_data: Optional[dict] = None

class ClassUpdateRequest(BaseModel):
    """Schema for updating class information"""
    name: Optional[str] = None
    section: Optional[str] = None
    stream: Optional[str] = None
    grade_level: Optional[int] = None
    academic_year: Optional[str] = None
    max_students: Optional[int] = None
    room_number: Optional[str] = None
    class_teacher_id: Optional[int] = None
    is_active: Optional[bool] = None
    dynamic_data: Optional[dict] = None

class ClassDynamicCreateRequest(BaseModel):
    """Schema for creating a class from dynamic form data"""
    dynamic_data: dict

# Class CRUD Operations
@router.get("", response_model=dict)
async def list_classes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, section, or stream"),
    grade_level: Optional[int] = Query(None, description="Filter by grade level"),
    section: Optional[str] = Query(None, description="Filter by section"),
    stream: Optional[str] = Query(None, description="Filter by stream"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    class_teacher_id: Optional[int] = Query(None, description="Filter by class teacher"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    filters: Optional[str] = Query(None, description="Dynamic filters based on form schema"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all classes with filtering and pagination"""

    # Check permissions using role configuration
    if not role_config.can_access_module(current_user.role.value, "classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access classes module"
        )

    # Base query with joins
    query = db.query(Class).options(
        joinedload(Class.class_teacher).joinedload(Teacher.user)
    )

    # Apply static filters
    if search:
        search_filter = or_(
            Class.name.ilike(f"%{search}%"),
            Class.section.ilike(f"%{search}%"),
            Class.stream.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if grade_level:
        query = query.filter(Class.grade_level == grade_level)

    if section:
        query = query.filter(Class.section.ilike(f"%{section}%"))

    if stream:
        query = query.filter(Class.stream.ilike(f"%{stream}%"))

    if academic_year:
        query = query.filter(Class.academic_year == academic_year)

    if class_teacher_id:
        query = query.filter(Class.class_teacher_id == class_teacher_id)

    # Show all classes by default, allow filtering by active status
    if is_active is not None:
        query = query.filter(Class.is_active == is_active)

    # Apply dynamic filters
    if filters:
        try:
            class_form = db.query(Form).filter(Form.key == "class_form").first()
            if class_form:
                for field in class_form.fields:
                    if field.is_filterable and field.field_name in filters:
                        value = filters[field.field_name]
                        if value:
                            query = query.filter(Class.dynamic_data[field.field_name].astext == str(value))
        except Exception as e:
            logger.error(f"Error applying dynamic filters: {e}")

    # Get total count
    total = query.count()

    # Apply pagination
    classes = query.offset(skip).limit(limit).all()

    # Format response
    class_list = []
    for class_item in classes:
        class_data = {
            "id": class_item.id,
            "name": class_item.name,
            "section": class_item.section,
            "stream": class_item.stream,
            "grade_level": class_item.grade_level,
            "academic_year": class_item.academic_year,
            "max_students": class_item.max_students,
            "room_number": class_item.room_number,
            "is_active": class_item.is_active,
            "created_at": class_item.created_at,
            "class_teacher": {
                "id": class_item.class_teacher.id,
                "employee_id": class_item.class_teacher.employee_id,
                "first_name": class_item.class_teacher.user.first_name,
                "last_name": class_item.class_teacher.user.last_name,
                "email": class_item.class_teacher.user.email,
                "department": class_item.class_teacher.department,
                "specialization": class_item.class_teacher.specialization,
            } if class_item.class_teacher and class_item.class_teacher.user else None,
            "dynamic_data": class_item.dynamic_data
        }
        class_list.append(class_data)

    return {
        "data": class_list,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
        "pages": (total + limit - 1) // limit,
        "has_next": skip + limit < total,
        "has_prev": skip > 0
    }

@router.post("", response_model=dict)
async def create_class(
    class_data: ClassCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new class"""

    # Check if current user has permission to access classes module
    if not role_config.can_access_module(current_user.role.value, "classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access classes module"
        )

    try:
        # Validate dynamic data
        if class_data.dynamic_data:
            validate_dynamic_data(db, class_data.dynamic_data)

        # Check if class name and section already exists for the same academic year
        existing_class = db.query(Class).filter(
            Class.name == class_data.name,
            Class.section == class_data.section,
            Class.academic_year == class_data.academic_year
        ).first()
        if existing_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class name and section already exists for this academic year"
            )

        # Create class record
        class_obj = Class(
            name=class_data.name,
            section=class_data.section,
            stream=class_data.stream,
            grade_level=class_data.grade_level,
            academic_year=class_data.academic_year,
            max_students=class_data.max_students,
            room_number=class_data.room_number,
            class_teacher_id=class_data.class_teacher_id,
            dynamic_data=class_data.dynamic_data
        )

        db.add(class_obj)
        db.commit()
        db.refresh(class_obj)

        logger.info(f"Class {class_obj.name} created by {current_user.email}")

        return {
            "message": "Class created successfully",
            "class_id": class_obj.id,
            "class_name": class_obj.name
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating class: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create class"
        )

@router.post("/dynamic", response_model=dict)
async def create_class_from_dynamic_form(
    class_data: ClassDynamicCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new class from dynamic form data"""

    # Log the incoming data for debugging
    logger.info(f"Creating class from dynamic form with data: {class_data.dynamic_data}")

    # Check if current user has permission to access classes module
    if not role_config.can_access_module(current_user.role.value, "classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access classes module"
        )

    try:
        # Extract required fields from dynamic data
        name = class_data.dynamic_data.get('name')
        section = class_data.dynamic_data.get('section')
        grade_level = class_data.dynamic_data.get('grade_level')
        academic_year = class_data.dynamic_data.get('academic_year')

        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class name is required"
            )

        if not section:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Section is required"
            )

        if not grade_level:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grade level is required"
            )

        if not academic_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Academic year is required"
            )

        # Check if class name and section already exists for the same academic year
        existing_class = db.query(Class).filter(
            Class.name == name,
            Class.section == section,
            Class.academic_year == academic_year
        ).first()
        if existing_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class name and section already exists for this academic year"
            )

        # Create class record
        class_obj = Class(
            name=name,
            section=section,
            stream=class_data.dynamic_data.get('stream'),
            grade_level=grade_level,
            academic_year=academic_year,
            max_students=class_data.dynamic_data.get('max_students'),
            room_number=class_data.dynamic_data.get('room_number'),
            class_teacher_id=class_data.dynamic_data.get('class_teacher_id'),
            dynamic_data=class_data.dynamic_data
        )

        db.add(class_obj)
        db.commit()
        db.refresh(class_obj)

        logger.info(f"Class {class_obj.name} created from dynamic form by {current_user.email}")

        return {
            "message": "Class created successfully",
            "class": {
                "id": class_obj.id,
                "name": class_obj.name,
                "section": class_obj.section,
                "grade_level": class_obj.grade_level,
                "academic_year": class_obj.academic_year
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating class from dynamic form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create class"
        )

@router.get("/{class_id}", response_model=dict)
async def get_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get class by ID with detailed information"""

    class_obj = db.query(Class).options(
        joinedload(Class.class_teacher)
    ).filter(Class.id == class_id).first()

    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    return {
        "id": class_obj.id,
        "name": class_obj.name,
        "section": class_obj.section,
        "stream": class_obj.stream,
        "grade_level": class_obj.grade_level,
        "academic_year": class_obj.academic_year,
        "max_students": class_obj.max_students,
        "room_number": class_obj.room_number,
        "is_active": class_obj.is_active,
        "created_at": class_obj.created_at,
        "updated_at": class_obj.updated_at,
        "class_teacher": {
            "id": class_obj.class_teacher.id,
            "first_name": class_obj.class_teacher.user.first_name,
            "last_name": class_obj.class_teacher.user.last_name,
        } if class_obj.class_teacher and class_obj.class_teacher.user else None,
        "dynamic_data": class_obj.dynamic_data
    }

@router.put("/{class_id}", response_model=dict)
async def update_class(
    class_id: int,
    class_data: ClassUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update class information"""

    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Check permissions - use role configuration
    if not role_config.can_access_module(current_user.role.value, "classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access classes module"
        )

    try:
        # Validate dynamic data
        if class_data.dynamic_data:
            validate_dynamic_data(db, class_data.dynamic_data)

        # Update class information
        if class_data.name is not None:
            class_obj.name = class_data.name
        if class_data.section is not None:
            class_obj.section = class_data.section
        if class_data.stream is not None:
            class_obj.stream = class_data.stream
        if class_data.grade_level is not None:
            class_obj.grade_level = class_data.grade_level
        if class_data.academic_year is not None:
            class_obj.academic_year = class_data.academic_year
        if class_data.max_students is not None:
            class_obj.max_students = class_data.max_students
        if class_data.room_number is not None:
            class_obj.room_number = class_data.room_number
        if class_data.class_teacher_id is not None:
            class_obj.class_teacher_id = class_data.class_teacher_id
        if class_data.dynamic_data is not None:
            class_obj.dynamic_data = class_data.dynamic_data

        # Admin-only fields - only users with module access can update these
        if role_config.can_access_module(current_user.role.value, "classes"):
            if class_data.is_active is not None:
                class_obj.is_active = class_data.is_active

        db.commit()

        logger.info(f"Class {class_obj.name} updated by {current_user.email}")

        return {"message": "Class updated successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating class: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update class"
        )

@router.delete("/{class_id}", response_model=dict)
async def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Permanently delete a class"""

    if not role_config.can_access_module(current_user.role.value, "classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access classes module"
        )

    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    try:
        # Store class info for logging
        class_name = class_obj.name
        class_section = class_obj.section
        
        # First, set all students' current_class_id to NULL
        from app.models.student import Student
        students_in_class = db.query(Student).filter(Student.current_class_id == class_id).all()
        for student in students_in_class:
            student.current_class_id = None
        
        # Permanently delete the class
        db.delete(class_obj)
        db.commit()

        logger.info(f"Class {class_name} {class_section} permanently deleted by {current_user.email}")

        return {"message": "Class permanently deleted successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting class: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete class"
        )

@router.get("/{class_id}/students", response_model=dict)
async def get_class_students(
    class_id: int,
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all students in a specific class"""
    
    # Check if class exists
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Check permissions - teachers can only see their assigned classes
    if current_user.role == UserRole.TEACHER:
        # Check if teacher is assigned to this class
        teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher profile not found"
            )
        
        # Check if teacher is assigned to this class (either as class teacher or subject teacher)
        is_class_teacher = class_obj.class_teacher_id == teacher.id
        is_subject_teacher = db.query(ClassSubject).filter(
            ClassSubject.class_id == class_id,
            ClassSubject.teacher_id == teacher.id
        ).first() is not None
        
        if not is_class_teacher and not is_subject_teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not assigned to this class"
            )
    
    # Get students in the class
    query = db.query(Student).join(User).filter(Student.current_class_id == class_id)
    
    if is_active is not None:
        query = query.filter(Student.is_active == is_active)
    
    students = query.options(
        joinedload(Student.user)
    ).all()
    
    # Get subjects for this class
    class_subjects = db.query(ClassSubject).filter(
        ClassSubject.class_id == class_id
    ).options(
        joinedload(ClassSubject.subject),
        joinedload(ClassSubject.teacher).joinedload(Teacher.user)
    ).all()
    
    # Format response
    student_list = []
    for student in students:
        # Get subjects for this student (same as class subjects since student is in this class)
        subjects_info = []
        for class_subject in class_subjects:
            teacher_name = "Not Assigned"
            if class_subject.teacher and class_subject.teacher.user:
                teacher_name = f"{class_subject.teacher.user.first_name} {class_subject.teacher.user.last_name}"
            
            subjects_info.append({
                "id": class_subject.subject.id,
                "name": class_subject.subject.name,
                "teacher": teacher_name,
                "weekly_hours": class_subject.weekly_hours,
                "is_optional": class_subject.is_optional
            })
        
        student_data = {
            "id": student.id,
            "student_id": student.student_id,
            "user": {
                "id": student.user.id,
                "email": student.user.email,
                "first_name": student.user.first_name,
                "last_name": student.user.last_name,
                "phone": student.user.phone,
                "is_active": student.user.is_active,
            },
            "roll_number": student.roll_number,
            "section": student.section,
            "is_active": student.is_active,
            "admission_date": student.admission_date,
            "academic_year": student.academic_year,
            "subjects": subjects_info
        }
        student_list.append(student_data)
    
    return {
        "students": student_list,
        "total": len(student_list),
        "class": {
            "id": class_obj.id,
            "name": class_obj.name,
            "section": class_obj.section
        }
    }


@router.patch("/{class_id}/toggle-status", response_model=dict)
async def toggle_class_status(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Toggle the active status of a class"""
    
    # Check if current user has permission to access classes module
    if not role_config.can_access_module(current_user.role.value, "classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access classes module"
        )

    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    try:
        # Toggle the active status
        class_obj.is_active = not class_obj.is_active
        status_text = "activated" if class_obj.is_active else "deactivated"

        db.commit()

        logger.info(f"Class {class_obj.name} {status_text} by {current_user.email}")

        return {
            "message": f"Class {status_text} successfully",
            "is_active": class_obj.is_active
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error toggling class status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle class status"
        )


