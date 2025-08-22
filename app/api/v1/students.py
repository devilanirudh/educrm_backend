"""
Student management API endpoints
"""

from typing import Any, List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from app.database.session import get_db
from app.api.deps import get_current_user
from app.core.permissions import UserRole
from app.models.user import User
from app.models.student import Student, AttendanceRecord, Grade, StudentDocument
from app.models.academic import Class, Subject
from app.models.form import Form
from app.schemas.user import UserCreate, UserResponse
from app.models.form import FieldType
from app.core.security import get_password_hash
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def validate_dynamic_data(db: Session, dynamic_data: dict):
    """Validate dynamic data against the student_form schema"""
    logger.info(f"Validating dynamic data: {dynamic_data}")
    
    student_form = db.query(Form).filter(Form.key == "student_form").first()
    if not student_form:
        logger.error("Student form schema not found")
        raise HTTPException(status_code=404, detail="Student form schema not found")

    errors = {}
    for field in student_form.fields:
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
        logger.error(f"Validation errors: {errors}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors}
        )

# Pydantic schemas for Student API
from pydantic import BaseModel, EmailStr, validator

class StudentCreateRequest(BaseModel):
    """Schema for creating a new student"""
    # User information
    email: EmailStr
    username: Optional[str] = None
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    
    # Student specific information
    student_id: str
    admission_date: date
    current_class_id: Optional[int] = None
    academic_year: str
    roll_number: Optional[str] = None
    section: Optional[str] = None
    
    # Personal information
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Additional information
    allergies: Optional[str] = None
    medical_conditions: Optional[str] = None
    transportation_mode: Optional[str] = None
    previous_school: Optional[str] = None
    hobbies: Optional[str] = None
    special_needs: Optional[str] = None

    # Dynamic data
    dynamic_data: Optional[dict] = None

class StudentUpdateRequest(BaseModel):
    """Schema for updating student information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    current_class_id: Optional[int] = None
    roll_number: Optional[str] = None
    section: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    allergies: Optional[str] = None
    medical_conditions: Optional[str] = None
    transportation_mode: Optional[str] = None
    hobbies: Optional[str] = None
    special_needs: Optional[str] = None
    is_active: Optional[bool] = None
    dynamic_data: Optional[dict] = None

class AttendanceCreateRequest(BaseModel):
    """Schema for creating attendance record"""
    student_id: int
    class_id: int
    date: date
    status: str  # present, absent, late, excused
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    reason: Optional[str] = None

# Add this new schema for dynamic form submission
class StudentDynamicCreateRequest(BaseModel):
    """Schema for creating a student from dynamic form data"""
    dynamic_data: dict

# Student CRUD Operations
@router.get("", response_model=dict)
async def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, email, or student ID"),
    class_id: Optional[int] = Query(None, description="Filter by class"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    filters: Optional[str] = Query(None, description="Dynamic filters based on form schema"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all students with filtering and pagination"""
    
    # Base query with joins
    query = db.query(Student).join(User).options(
        joinedload(Student.user),
        joinedload(Student.current_class)
    )
    
    # Apply static filters
    if search:
        search_filter = or_(
            User.first_name.ilike(f"%{search}%"),
            User.last_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            Student.student_id.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if class_id:
        query = query.filter(Student.current_class_id == class_id)
    
    if academic_year:
        query = query.filter(Student.academic_year == academic_year)
    
    if is_active is not None:
        query = query.filter(Student.is_active == is_active)

    # Apply dynamic filters
    if filters:
        try:
            student_form = db.query(Form).filter(Form.key == "student_form").first()
            if student_form:
                for field in student_form.fields:
                    if field.is_filterable and field.field_name in filters:
                        value = filters[field.field_name]
                        if value:
                            query = query.filter(Student.dynamic_data[field.field_name].astext == str(value))
        except Exception as e:
            logger.error(f"Error applying dynamic filters: {e}")

    
    # Get total count
    total = query.count()
    
    # Apply pagination
    students = query.offset(skip).limit(limit).all()
    
    # Format response
    student_list = []
    for student in students:
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
            "admission_date": student.admission_date,
            "current_class": student.current_class.name if student.current_class else None,
            "academic_year": student.academic_year,
            "roll_number": student.roll_number,
            "section": student.section,
            "is_active": student.is_active,
            "created_at": student.created_at,
            "dynamic_data": student.dynamic_data
        }
        student_list.append(student_data)
    
    return {
        "students": student_list,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
        "has_next": skip + limit < total,
        "has_prev": skip > 0
    }

@router.post("", response_model=dict)
async def create_student(
    student_data: StudentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Log the incoming data for debugging
    logger.info(f"Creating student with data: {student_data.dict()}")
    
    # Check if current user has permission (admin or staff)
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if current user has permission (admin or staff)
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        # Validate dynamic data
        if student_data.dynamic_data:
            validate_dynamic_data(db, student_data.dynamic_data)

        # Check if email or student_id already exists
        existing_user = db.query(User).filter(User.email == student_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_student = db.query(Student).filter(Student.student_id == student_data.student_id).first()
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student ID already exists"
            )
        
        # Create user account
        user = User(
            email=student_data.email,
            username=student_data.username,
            hashed_password=get_password_hash(student_data.password),
            first_name=student_data.first_name,
            last_name=student_data.last_name,
            phone=student_data.phone,
            role=UserRole.STUDENT,
            date_of_birth=student_data.date_of_birth,
            gender=student_data.gender,
            address=student_data.address,
            city=student_data.city,
            state=student_data.state,
            country=student_data.country,
            postal_code=student_data.postal_code
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create student record
        student = Student(
            user_id=user.id,
            student_id=student_data.student_id,
            admission_date=student_data.admission_date,
            current_class_id=student_data.current_class_id,
            academic_year=student_data.academic_year,
            roll_number=student_data.roll_number,
            section=student_data.section,
            blood_group=student_data.blood_group,
            allergies=student_data.allergies,
            medical_conditions=student_data.medical_conditions,
            transportation_mode=student_data.transportation_mode,
            previous_school=student_data.previous_school,
            hobbies=student_data.hobbies,
            special_needs=student_data.special_needs,
            dynamic_data=student_data.dynamic_data
        )
        
        db.add(student)
        db.commit()
        db.refresh(student)
        
        logger.info(f"Student {student.student_id} created by {current_user.email}")
        
        return {
            "message": "Student created successfully",
            "student_id": student.id,
            "student_number": student.student_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating student: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create student"
        )

@router.post("/dynamic", response_model=dict)
async def create_student_from_dynamic_form(
    student_data: StudentDynamicCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new student from dynamic form data"""
    
    # Log the incoming data for debugging
    logger.info(f"Creating student from dynamic form with data: {student_data.dynamic_data}")
    
    # Check if current user has permission (admin or staff)
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        # Extract required fields from dynamic data
        student_id = student_data.dynamic_data.get('student_id')
        admission_date_str = student_data.dynamic_data.get('admission_date')
        academic_year = student_data.dynamic_data.get('academic_year')
        email = student_data.dynamic_data.get('email')
        password = student_data.dynamic_data.get('password')
        first_name = student_data.dynamic_data.get('first_name')
        last_name = student_data.dynamic_data.get('last_name')
        
        if not student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student ID is required"
            )
        
        if not admission_date_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admission date is required"
            )
        
        if not academic_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Academic year is required"
            )
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required"
            )
        
        if not first_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="First name is required"
            )
        
        if not last_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Last name is required"
            )

        # Parse admission date
        try:
            admission_date = datetime.strptime(admission_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid admission date format. Use YYYY-MM-DD"
            )

        # Check if student_id already exists
        existing_student = db.query(Student).filter(Student.student_id == student_id).first()
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student ID already exists"
            )
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user account
        user = User(
            email=email,
            username=student_id.lower(),
            hashed_password=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone=student_data.dynamic_data.get('phone'),
            role=UserRole.STUDENT,
            date_of_birth=None,  # Will be set if provided in dynamic data
            gender=student_data.dynamic_data.get('gender'),
            address=student_data.dynamic_data.get('address'),
            city=student_data.dynamic_data.get('city'),
            state=student_data.dynamic_data.get('state'),
            country=student_data.dynamic_data.get('country'),
            postal_code=student_data.dynamic_data.get('postal_code')
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create student record
        student = Student(
            user_id=user.id,
            student_id=student_id,
            admission_date=admission_date,
            current_class_id=None,  # Will be set if provided
            academic_year=academic_year,
            roll_number=student_data.dynamic_data.get('roll_number'),
            section=student_data.dynamic_data.get('section'),
            blood_group=student_data.dynamic_data.get('blood_group'),
            allergies=student_data.dynamic_data.get('allergies'),
            medical_conditions=student_data.dynamic_data.get('medical_conditions'),
            transportation_mode=student_data.dynamic_data.get('transportation_mode'),
            previous_school=student_data.dynamic_data.get('previous_school'),
            hobbies=student_data.dynamic_data.get('hobbies'),
            special_needs=student_data.dynamic_data.get('special_needs'),
            dynamic_data=student_data.dynamic_data
        )
        
        db.add(student)
        db.commit()
        db.refresh(student)
        
        logger.info(f"Student {student.student_id} created by {current_user.email}")
        
        return {
            "message": "Student created successfully",
            "student_id": student.student_id,
            "user_id": user.id,
            "email": email,
            "password": password,  # Return the password for admin reference
            "student": {
                "id": student.id,
                "student_id": student.student_id,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone": user.phone,
                    "is_active": user.is_active
                },
                "admission_date": student.admission_date,
                "academic_year": student.academic_year,
                "roll_number": student.roll_number,
                "section": student.section,
                "is_active": student.is_active,
                "created_at": student.created_at,
                "dynamic_data": student.dynamic_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating student from dynamic form: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the student"
        )

@router.get("/{student_id}", response_model=dict)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get student by ID with detailed information"""
    
    student = db.query(Student).options(
        joinedload(Student.user),
        joinedload(Student.current_class),
        joinedload(Student.bus_route),
        joinedload(Student.hostel_room)
    ).filter(Student.id == student_id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check permissions - students can only view their own data
    if (current_user.role == UserRole.STUDENT and 
        current_user.id != student.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": student.id,
        "student_id": student.student_id,
        "user": {
            "id": student.user.id,
            "email": student.user.email,
            "username": student.user.username,
            "first_name": student.user.first_name,
            "last_name": student.user.last_name,
            "phone": student.user.phone,
            "date_of_birth": student.user.date_of_birth,
            "gender": student.user.gender,
            "address": student.user.address,
            "city": student.user.city,
            "state": student.user.state,
            "country": student.user.country,
            "postal_code": student.user.postal_code,
            "is_active": student.user.is_active,
            "is_verified": student.user.is_verified,
            "last_login": student.user.last_login,
            "created_at": student.user.created_at
        },
        "admission_date": student.admission_date,
        "current_class": {
            "id": student.current_class.id,
            "name": student.current_class.name,
            "section": student.current_class.section
        } if student.current_class else None,
        "academic_year": student.academic_year,
        "roll_number": student.roll_number,
        "section": student.section,
        "blood_group": student.blood_group,
        "allergies": student.allergies,
        "medical_conditions": student.medical_conditions,
        "transportation_mode": student.transportation_mode,
        "bus_route": {
            "id": student.bus_route.id,
            "route_name": student.bus_route.route_name,
            "route_number": student.bus_route.route_number
        } if student.bus_route else None,
        "hostel_room": {
            "id": student.hostel_room.id,
            "room_number": student.hostel_room.room_number,
            "block": student.hostel_room.block.block_name
        } if student.hostel_room else None,
        "is_hosteller": student.is_hosteller,
        "previous_school": student.previous_school,
        "hobbies": student.hobbies,
        "special_needs": student.special_needs,
        "is_active": student.is_active,
        "graduation_date": student.graduation_date,
        "created_at": student.created_at,
        "updated_at": student.updated_at
    }

@router.put("/{student_id}", response_model=dict)
async def update_student(
    student_id: int,
    student_data: StudentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update student information"""
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        # Validate dynamic data
        if student_data.dynamic_data:
            validate_dynamic_data(db, student_data.dynamic_data)
            
        # Update user information
        user = student.user
        if student_data.first_name is not None:
            user.first_name = student_data.first_name
        if student_data.last_name is not None:
            user.last_name = student_data.last_name
        if student_data.phone is not None:
            user.phone = student_data.phone
        if student_data.address is not None:
            user.address = student_data.address
        if student_data.city is not None:
            user.city = student_data.city
        if student_data.state is not None:
            user.state = student_data.state
        if student_data.country is not None:
            user.country = student_data.country
        if student_data.postal_code is not None:
            user.postal_code = student_data.postal_code
        if student_data.is_active is not None:
            user.is_active = student_data.is_active
        
        # Update student information
        if student_data.current_class_id is not None:
            student.current_class_id = student_data.current_class_id
        if student_data.roll_number is not None:
            student.roll_number = student_data.roll_number
        if student_data.section is not None:
            student.section = student_data.section
        if student_data.blood_group is not None:
            student.blood_group = student_data.blood_group
        if student_data.allergies is not None:
            student.allergies = student_data.allergies
        if student_data.medical_conditions is not None:
            student.medical_conditions = student_data.medical_conditions
        if student_data.transportation_mode is not None:
            student.transportation_mode = student_data.transportation_mode
        if student_data.hobbies is not None:
            student.hobbies = student_data.hobbies
        if student_data.special_needs is not None:
            student.special_needs = student_data.special_needs
        if student_data.dynamic_data is not None:
            student.dynamic_data = student_data.dynamic_data
        
        db.commit()
        
        logger.info(f"Student {student.student_id} updated by {current_user.email}")
        
        return {"message": "Student updated successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating student: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update student"
        )

@router.delete("/{student_id}", response_model=dict)
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Soft delete a student (deactivate)"""
    
    if current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete students"
        )
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    try:
        # Soft delete - deactivate instead of removing
        student.is_active = False
        student.user.is_active = False
        student.dropout_date = datetime.utcnow().date()
        
        db.commit()
        
        logger.info(f"Student {student.student_id} deactivated by {current_user.email}")
        
        return {"message": "Student deactivated successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating student: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate student"
        )

# Attendance Management
@router.get("/{student_id}/attendance", response_model=dict)
async def get_student_attendance(
    student_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get student attendance records"""
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check permissions
    if (current_user.role == UserRole.STUDENT and 
        current_user.id != student.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    query = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id)
    
    if start_date:
        query = query.filter(AttendanceRecord.date >= start_date)
    if end_date:
        query = query.filter(AttendanceRecord.date <= end_date)
    
    attendance_records = query.order_by(AttendanceRecord.date.desc()).all()
    
    # Calculate statistics
    total_days = len(attendance_records)
    present_days = len([r for r in attendance_records if r.status == 'present'])
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    return {
        "student_id": student_id,
        "attendance_records": [
            {
                "id": record.id,
                "date": record.date,
                "status": record.status,
                "check_in_time": record.check_in_time,
                "check_out_time": record.check_out_time,
                "reason": record.reason
            }
            for record in attendance_records
        ],
        "statistics": {
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": total_days - present_days,
            "attendance_percentage": round(attendance_percentage, 2)
        }
    }

@router.post("/{student_id}/attendance", response_model=dict)
async def mark_attendance(
    student_id: int,
    attendance_data: AttendanceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Mark student attendance"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and administrators can mark attendance"
        )
    
    # Check if attendance already exists for this date
    existing_attendance = db.query(AttendanceRecord).filter(
        and_(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.date == attendance_data.date,
            AttendanceRecord.class_id == attendance_data.class_id
        )
    ).first()
    
    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already marked for this date"
        )
    
    try:
        attendance = AttendanceRecord(
            student_id=student_id,
            class_id=attendance_data.class_id,
            date=attendance_data.date,
            status=attendance_data.status,
            check_in_time=attendance_data.check_in_time,
            check_out_time=attendance_data.check_out_time,
            reason=attendance_data.reason,
            marked_by=current_user.id
        )
        
        db.add(attendance)
        db.commit()
        
        logger.info(f"Attendance marked for student {student_id} on {attendance_data.date} by {current_user.email}")
        
        return {"message": "Attendance marked successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark attendance"
        )
