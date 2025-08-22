"""
Teacher management API endpoints
"""

from typing import Any, List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from app.database.session import get_db
from app.api.deps import get_current_user
from app.core.permissions import UserRole
from app.models.user import User
from app.models.teacher import Teacher
from app.models.academic import Class, Subject
from app.models.form import Form, FieldType
from app.services.auth import AuthService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def validate_dynamic_data(db: Session, dynamic_data: dict):
    """Validate dynamic data against the teacher_form schema"""
    teacher_form = db.query(Form).filter(Form.key == "teacher_form").first()
    if not teacher_form:
        raise HTTPException(status_code=404, detail="Teacher form schema not found")

    errors = {}
    for field in teacher_form.fields:
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

# Pydantic schemas for Teacher API
from pydantic import BaseModel, EmailStr

class TeacherCreateRequest(BaseModel):
    """Schema for creating a new teacher"""
    # User information
    email: EmailStr
    username: Optional[str] = None
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    
    # Teacher specific information
    employee_id: str
    qualifications: Optional[str] = None
    experience: Optional[int] = None
    specialization: Optional[str] = None
    
    # Personal information
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Employment details
    hire_date: date
    employment_type: str
    salary: Optional[float] = None
    department: Optional[str] = None
    dynamic_data: Optional[dict] = None

class TeacherUpdateRequest(BaseModel):
    """Schema for updating teacher information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    qualifications: Optional[str] = None
    experience: Optional[int] = None
    specialization: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    salary: Optional[float] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    dynamic_data: Optional[dict] = None

# Teacher CRUD Operations
@router.get("", response_model=dict)
async def list_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, email, or employee ID"),
    department: Optional[str] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    filters: Optional[str] = Query(None, description="Dynamic filters based on form schema"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all teachers with filtering and pagination"""
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Base query with joins
    query = db.query(Teacher).join(User).options(
        joinedload(Teacher.user)
    )
    
    # Apply filters
    if search:
        search_filter = or_(
            User.first_name.ilike(f"%{search}%"),
            User.last_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            Teacher.employee_id.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if department:
        query = query.filter(Teacher.department.ilike(f"%{department}%"))
    
    if is_active is not None:
        query = query.filter(Teacher.is_active == is_active)

    # Apply dynamic filters
    if filters:
        try:
            teacher_form = db.query(Form).filter(Form.key == "teacher_form").first()
            if teacher_form:
                for field in teacher_form.fields:
                    if field.is_filterable and field.field_name in filters:
                        value = filters[field.field_name]
                        if value:
                            query = query.filter(Teacher.dynamic_data[field.field_name].astext == str(value))
        except Exception as e:
            logger.error(f"Error applying dynamic filters: {e}")
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    teachers = query.offset(skip).limit(limit).all()
    
    # Format response
    teacher_list = []
    for teacher in teachers:
        teacher_data = {
            "id": teacher.id,
            "employee_id": teacher.employee_id,
            "user": {
                "id": teacher.user.id,
                "email": teacher.user.email,
                "first_name": teacher.user.first_name,
                "last_name": teacher.user.last_name,
                "phone": teacher.user.phone,
                "is_active": teacher.user.is_active,
            },
            "qualifications": teacher.qualifications,
            "experience": teacher.experience,
            "specialization": teacher.specialization,
            "department": teacher.department,
            "hire_date": teacher.hire_date,
            "is_active": teacher.is_active,
            "created_at": teacher.created_at,
            "dynamic_data": teacher.dynamic_data
        }
        teacher_list.append(teacher_data)
    
    return {
        "teachers": teacher_list,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
        "has_next": skip + limit < total,
        "has_prev": skip > 0
    }

@router.post("", response_model=dict)
async def create_teacher(
    teacher_data: TeacherCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new teacher"""
    
    # Check if current user has permission (admin only)
    if current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create teachers"
        )
    
    try:
        # Validate dynamic data
        if teacher_data.dynamic_data:
            validate_dynamic_data(db, teacher_data.dynamic_data)

        # Check if email or employee_id already exists
        existing_user = db.query(User).filter(User.email == teacher_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_teacher = db.query(Teacher).filter(Teacher.employee_id == teacher_data.employee_id).first()
        if existing_teacher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
        
        # Create user account
        auth_service = AuthService(db)
        user = auth_service.create_user(
            email=teacher_data.email,
            username=teacher_data.username,
            password=teacher_data.password,
            first_name=teacher_data.first_name,
            last_name=teacher_data.last_name,
            phone=teacher_data.phone,
            role=UserRole.TEACHER,
            date_of_birth=teacher_data.date_of_birth,
            gender=teacher_data.gender,
            address=teacher_data.address,
            city=teacher_data.city,
            state=teacher_data.state,
            country=teacher_data.country,
            postal_code=teacher_data.postal_code
        )
        
        # Create teacher record
        teacher = Teacher(
            user_id=user.id,
            employee_id=teacher_data.employee_id,
            qualifications=teacher_data.qualifications,
            experience=teacher_data.experience,
            specialization=teacher_data.specialization,
            hire_date=teacher_data.hire_date,
            employment_type=teacher_data.employment_type,
            salary=teacher_data.salary,
            department=teacher_data.department,
            dynamic_data=teacher_data.dynamic_data
        )
        
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        
        logger.info(f"Teacher {teacher.employee_id} created by {current_user.email}")
        
        return {
            "message": "Teacher created successfully",
            "teacher_id": teacher.id,
            "employee_id": teacher.employee_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating teacher: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create teacher"
        )

@router.get("/{teacher_id}", response_model=dict)
async def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get teacher by ID with detailed information"""
    
    teacher = db.query(Teacher).options(
        joinedload(Teacher.user)
    ).filter(Teacher.id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check permissions - teachers can view their own data, admin can view all
    if (current_user.role == UserRole.TEACHER and 
        current_user.id != teacher.user_id and 
        current_user.role not in [UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": teacher.id,
        "employee_id": teacher.employee_id,
        "user": {
            "id": teacher.user.id,
            "email": teacher.user.email,
            "username": teacher.user.username,
            "first_name": teacher.user.first_name,
            "last_name": teacher.user.last_name,
            "phone": teacher.user.phone,
            "date_of_birth": teacher.user.date_of_birth,
            "gender": teacher.user.gender,
            "address": teacher.user.address,
            "city": teacher.user.city,
            "state": teacher.user.state,
            "country": teacher.user.country,
            "postal_code": teacher.user.postal_code,
            "is_active": teacher.user.is_active,
            "is_verified": teacher.user.is_verified,
            "last_login": teacher.user.last_login,
            "created_at": teacher.user.created_at
        },
        "qualifications": teacher.qualifications,
        "experience": teacher.experience,
        "specialization": teacher.specialization,
        "hire_date": teacher.hire_date,
        "salary": teacher.salary,
        "department": teacher.department,
        "is_active": teacher.is_active,
        "created_at": teacher.created_at,
        "updated_at": teacher.updated_at,
        "dynamic_data": teacher.dynamic_data
    }

@router.put("/{teacher_id}", response_model=dict)
async def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update teacher information"""
    
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check permissions - teachers can update some of their own data, admin can update all
    if (current_user.role == UserRole.TEACHER and 
        current_user.id != teacher.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Only admin can update sensitive fields like salary and is_active
    if (current_user.role != UserRole.ADMIN and 
        (teacher_data.salary is not None or teacher_data.is_active is not None)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update sensitive fields"
        )
    
    try:
        # Validate dynamic data
        if teacher_data.dynamic_data:
            validate_dynamic_data(db, teacher_data.dynamic_data)
            
        # Update user information
        user = teacher.user
        if teacher_data.first_name is not None:
            user.first_name = teacher_data.first_name
        if teacher_data.last_name is not None:
            user.last_name = teacher_data.last_name
        if teacher_data.phone is not None:
            user.phone = teacher_data.phone
        if teacher_data.address is not None:
            user.address = teacher_data.address
        if teacher_data.city is not None:
            user.city = teacher_data.city
        if teacher_data.state is not None:
            user.state = teacher_data.state
        if teacher_data.country is not None:
            user.country = teacher_data.country
        if teacher_data.postal_code is not None:
            user.postal_code = teacher_data.postal_code
        
        # Update teacher information
        if teacher_data.qualifications is not None:
            teacher.qualifications = teacher_data.qualifications
        if teacher_data.experience is not None:
            teacher.experience = teacher_data.experience
        if teacher_data.specialization is not None:
            teacher.specialization = teacher_data.specialization
        if teacher_data.department is not None:
            teacher.department = teacher_data.department
        if teacher_data.dynamic_data is not None:
            teacher.dynamic_data = teacher_data.dynamic_data
        
        # Admin-only fields
        if current_user.role == UserRole.ADMIN:
            if teacher_data.salary is not None:
                teacher.salary = teacher_data.salary
            if teacher_data.is_active is not None:
                teacher.is_active = teacher_data.is_active
                user.is_active = teacher_data.is_active
        
        db.commit()
        
        logger.info(f"Teacher {teacher.employee_id} updated by {current_user.email}")
        
        return {"message": "Teacher updated successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating teacher: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update teacher"
        )

@router.delete("/{teacher_id}", response_model=dict)
async def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Soft delete a teacher (deactivate)"""
    
    if current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete teachers"
        )
    
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    try:
        # Soft delete - deactivate instead of removing
        teacher.is_active = False
        teacher.user.is_active = False
        
        db.commit()
        
        logger.info(f"Teacher {teacher.employee_id} deactivated by {current_user.email}")
        
        return {"message": "Teacher deactivated successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating teacher: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate teacher"
        )

# Teacher's Classes and Subjects
@router.get("/{teacher_id}/classes", response_model=dict)
async def get_teacher_classes(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get classes assigned to a teacher"""
    
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check permissions
    if (current_user.role == UserRole.TEACHER and 
        current_user.id != teacher.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get classes where this teacher is the class teacher or teaches subjects
    classes = db.query(Class).filter(
        or_(
            Class.class_teacher_id == teacher_id,
            Class.subjects.any(Subject.teacher_id == teacher_id)
        )
    ).all()
    
    class_list = []
    for cls in classes:
        class_data = {
            "id": cls.id,
            "name": cls.name,
            "section": cls.section,
            "academic_year": cls.academic_year,
            "grade_level": cls.grade_level,
            "is_class_teacher": cls.class_teacher_id == teacher_id,
            "subjects_taught": [
                {
                    "id": subject.id,
                    "name": subject.name,
                    "code": subject.code
                }
                for subject in cls.subjects if subject.teacher_id == teacher_id
            ]
        }
        class_list.append(class_data)
    
    return {
        "teacher_id": teacher_id,
        "classes": class_list,
        "total_classes": len(class_list)
    }

@router.get("/{teacher_id}/subjects", response_model=dict)
async def get_teacher_subjects(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get subjects taught by a teacher"""
    
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check permissions
    if (current_user.role == UserRole.TEACHER and 
        current_user.id != teacher.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    subjects = db.query(Subject).filter(Subject.teacher_id == teacher_id).all()
    
    subject_list = []
    for subject in subjects:
        subject_data = {
            "id": subject.id,
            "name": subject.name,
            "code": subject.code,
            "description": subject.description,
            "credits": subject.credits,
            "class": {
                "id": subject.class_obj.id,
                "name": subject.class_obj.name,
                "section": subject.class_obj.section
            } if subject.class_obj else None,
            "created_at": subject.created_at
        }
        subject_list.append(subject_data)
    
    return {
        "teacher_id": teacher_id,
        "subjects": subject_list,
        "total_subjects": len(subject_list)
    }

from sqlalchemy import func
from datetime import datetime, timedelta

@router.get("/stats/headcount-trend", response_model=dict)
async def get_headcount_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get teacher headcount trend for the last 12 months"""
    
    # Calculate the date 12 months ago
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    
    # Query to get the count of teachers hired each month
    trend = db.query(
        func.strftime('%Y-%m', Teacher.hire_date).label('month'),
        func.count(Teacher.id).label('count')
    ).filter(
        Teacher.hire_date >= twelve_months_ago
    ).group_by(
        func.strftime('%Y-%m', Teacher.hire_date)
    ).order_by(
        func.strftime('%Y-%m', Teacher.hire_date)
    ).all()
    
    return {
        "trend": [
            {"month": month, "count": count}
            for month, count in trend
        ]
    }
