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
from app.core.role_config import role_config
from app.models.user import User, Parent
from app.models.student import Student, AttendanceRecord, Grade, StudentDocument
from app.models.academic import Class, Subject, ClassSubject
from app.models.teacher import Teacher
from app.models.form import Form
from app.schemas.user import UserCreate, UserResponse
from app.models.form import FieldType
from app.core.security import get_password_hash
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

from pydantic import BaseModel
from app.models.academic import Assignment, Exam

class StudentDashboardResponse(BaseModel):
    assignments: dict
    exams: dict
    live_classes: dict
    grades: dict

@router.get("/{student_id}/subjects", response_model=dict)
async def get_student_subjects(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get subjects for a specific student"""

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
    
    # Get student's class
    if not student.current_class_id:
        return {
            "subjects": [],
            "message": "Student not assigned to any class"
        }
    
    # Get subjects for the student's class through ClassSubject
    class_subjects = db.query(ClassSubject).filter(
        ClassSubject.class_id == student.current_class_id
    ).all()
    
    subjects_list = []
    for class_subject in class_subjects:
        subject = class_subject.subject
        teacher_name = "Not Assigned"
        if class_subject.teacher and class_subject.teacher.user:
            teacher_name = f"{class_subject.teacher.user.first_name} {class_subject.teacher.user.last_name}"
        elif class_subject.teacher:
            teacher_name = class_subject.teacher.full_name
        
        subjects_list.append({
            "id": subject.id,
            "name": subject.name,
            "teacher": teacher_name,
            "schedule": f"{class_subject.weekly_hours} hours/week" if class_subject.weekly_hours else "Not Scheduled",
            "is_active": subject.is_active
        })
    
    return {
        "subjects": subjects_list
    }

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

# Debug endpoint to show all users and their profiles
@router.get("/debug/users", response_model=dict)
async def debug_users(db: Session = Depends(get_db)) -> Any:
    """Debug endpoint to show all users and their associated profiles"""
    
    # Get all users
    users = db.query(User).all()
    
    users_info = []
    for user in users:
        # Check if user has student profile
        student = db.query(Student).filter(Student.user_id == user.id).first()
        
        user_info = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "has_student_profile": student is not None,
            "student_id": student.id if student else None,
            "student_number": student.student_id if student else None
        }
        users_info.append(user_info)
    
    return {"users": users_info}

# Get current user's student profile
@router.get("/me/profile", response_model=dict)
async def get_current_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get the current user's student profile"""
    
    # Check if user is a student
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access their profile"
        )
    
    # Get student profile
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    return {
        "id": student.id,
        "student_id": student.student_id,
        "user_id": student.user_id,
        "admission_date": student.admission_date,
        "current_class_id": student.current_class_id,
        "academic_year": student.academic_year,
        "roll_number": student.roll_number,
        "section": student.section,
        "is_active": student.is_active
    }

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
    db: Session = Depends(get_db)
    # Temporarily removed authentication for debugging: current_user: User = Depends(get_current_user)
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

    # Default to showing only active students unless explicitly requested otherwise
    if is_active is not None:
        query = query.filter(Student.is_active == is_active)
    else:
        # By default, only show active students
        query = query.filter(Student.is_active == True)

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
            "current_class": {
                "id": student.current_class.id,
                "name": student.current_class.name,
                "section": student.current_class.section,
                "grade_level": student.current_class.grade_level
            } if student.current_class else None,
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
    
    # Check if current user has permission to access students module
    if not role_config.can_access_module(current_user.role.value, "students"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access students module"
        )
    
    try:
        # Validate dynamic data
        if student_data.dynamic_data:
            validate_dynamic_data(db, student_data.dynamic_data)

        # Check if email already exists
        existing_user = db.query(User).filter(User.email == student_data.email).first()
        if existing_user:
            # Check if this user already has a student profile
            existing_student_profile = db.query(Student).filter(Student.user_id == existing_user.id).first()
            if existing_student_profile:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered with a student profile"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email already registered as {existing_user.role.value}. Cannot create student profile."
                )
        
        # Check if student_id already exists
        existing_student = db.query(Student).filter(Student.student_id == student_data.student_id).first()
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student ID already exists"
            )
        
        # Use transaction to ensure both User and Student are created together
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
        db.flush()  # Get the user ID without committing
        
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
        db.commit()  # Commit both User and Student together
        db.refresh(user)
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
    
    # Check if current user has permission to access students module
    if not role_config.can_access_module(current_user.role.value, "students"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access students module"
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
        parent_email = student_data.dynamic_data.get('parent_email')
        grade_level = student_data.dynamic_data.get('grade_level')
        
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
        
        # Find appropriate class based on grade level and section
        current_class_id = None
        if grade_level and student_data.dynamic_data.get('section'):
            # Try to find a class with matching grade level and section
            class_obj = db.query(Class).filter(
                and_(
                    Class.grade_level == int(grade_level),
                    Class.section == student_data.dynamic_data.get('section'),
                    Class.academic_year == academic_year,
                    Class.is_active == True
                )
            ).first()
            
            if class_obj:
                current_class_id = class_obj.id
                logger.info(f"Auto-assigned student to class: {class_obj.name} {class_obj.section}")
            else:
                logger.warning(f"No matching class found for grade_level={grade_level}, section={student_data.dynamic_data.get('section')}, academic_year={academic_year}")
        
        # Create student record
        student = Student(
            user_id=user.id,
            student_id=student_id,
            admission_date=admission_date,
            current_class_id=current_class_id,
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
        
        # Handle parent creation if parent_email is provided
        parent_user = None
        parent_profile = None
        if parent_email:
            # Check if parent user already exists
            parent_user = db.query(User).filter(User.email == parent_email).first()
            
            if not parent_user:
                # Create new parent user
                parent_user = User(
                    email=parent_email,
                    username=parent_email.split('@')[0],  # Use email prefix as username
                    hashed_password=get_password_hash("parent123"),  # Default password
                    first_name=f"Parent of {first_name}",
                    last_name=last_name,
                    role=UserRole.PARENT,
                    is_active=True
                )
                db.add(parent_user)
                db.commit()
                db.refresh(parent_user)
                
                # Create parent profile
                parent_profile = Parent(
                    user_id=parent_user.id,
                    relationship_to_student="parent",
                    is_primary_contact=True,
                    can_pickup_student=True,
                    receives_notifications=True
                )
                db.add(parent_profile)
                db.commit()
                db.refresh(parent_profile)
                
                logger.info(f"Parent user created: {parent_email}")
            else:
                # Parent user exists, check if they have a parent profile
                parent_profile = db.query(Parent).filter(Parent.user_id == parent_user.id).first()
                if not parent_profile:
                    # Create parent profile for existing user
                    parent_profile = Parent(
                        user_id=parent_user.id,
                        relationship_to_student="parent",
                        is_primary_contact=True,
                        can_pickup_student=True,
                        receives_notifications=True
                    )
                    db.add(parent_profile)
                    db.commit()
                    db.refresh(parent_profile)
            
            # Link parent to student
            if parent_profile:
                student.parents.append(parent_profile)
                db.commit()
                logger.info(f"Parent {parent_email} linked to student {student.student_id}")
        
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
    
    # Check permissions - users need access to students module
    if not role_config.can_access_module(current_user.role.value, "students"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access students module"
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
    """Delete a student and their user record (cascade delete)"""
    
    # Check if current user has permission to access students module
    if not role_config.can_access_module(current_user.role.value, "students"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access students module"
        )
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    try:
        # Store user info for logging
        user_email = student.user.email
        student_id_str = student.student_id
        
        # Delete the student record (this will cascade to related records)
        db.delete(student)
        
        # Delete the user record
        db.delete(student.user)
        
        db.commit()
        
        logger.info(f"Student {student_id_str} and user {user_email} deleted by {current_user.email}")
        
        return {"message": "Student and user record deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting student: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete student"
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
                "check_in_time": record.actual_check_in,
                "check_out_time": record.actual_check_out,
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
    
    # Check if current user has permission to access attendance module
    if not role_config.can_access_module(current_user.role.value, "attendance"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access attendance module"
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
        # Update existing attendance record
        existing_attendance.status = attendance_data.status
        existing_attendance.actual_check_in = attendance_data.check_in_time
        existing_attendance.actual_check_out = attendance_data.check_out_time
        existing_attendance.reason = attendance_data.reason
        existing_attendance.updated_at = func.now()
        
        db.commit()
        
        logger.info(f"Attendance updated for student {student_id} on {attendance_data.date} by {current_user.email}")
        
        return {"message": "Attendance updated successfully"}
    
    try:
        attendance = AttendanceRecord(
            student_id=student_id,
            class_id=attendance_data.class_id,
            date=attendance_data.date,
            status=attendance_data.status,
            actual_check_in=attendance_data.check_in_time,
            actual_check_out=attendance_data.check_out_time,
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


@router.get("/me/classes", response_model=dict)
async def get_my_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get classes for the current student"""
    
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    # Get the student record
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    if not student.current_class_id:
        return {
            "classes": [],
            "message": "Student not assigned to any class"
        }
    
    # Get the student's class
    class_obj = db.query(Class).filter(Class.id == student.current_class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Get ALL subjects that have teachers assigned to them for this class
    subjects_info = []
    
    # Get all ClassSubject assignments for this class that have teachers
    class_subjects = db.query(ClassSubject).filter(
        ClassSubject.class_id == student.current_class_id,
        ClassSubject.teacher_id.isnot(None)  # Only subjects with assigned teachers
    ).options(
        joinedload(ClassSubject.subject),
        joinedload(ClassSubject.teacher).joinedload(Teacher.user)
    ).all()
    
    for class_subject in class_subjects:
        teacher_name = f"{class_subject.teacher.user.first_name} {class_subject.teacher.user.last_name}"
        subjects_info.append({
            "id": class_subject.subject.id,
            "name": class_subject.subject.name,
            "teacher": teacher_name,
            "weekly_hours": class_subject.weekly_hours or 5,
            "is_optional": class_subject.is_optional,
            "room_number": class_obj.room_number
        })
    
    # Format class information
    class_info = {
        "id": class_obj.id,
        "name": class_obj.name,
        "section": class_obj.section,
        "grade_level": class_obj.grade_level,
        "academic_year": class_obj.academic_year,
        "room_number": class_obj.room_number,
        "subjects": subjects_info
    }
    
    return {
        "classes": [class_info],
        "total": 1
    }

# Student Dashboard endpoint
@router.get("/me/dashboard", response_model=dict)
async def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get dashboard data for the current student user"""

    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )

    # Resolve student
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Recent/pending assignments for student's class
    assignments_q = db.query(Assignment).filter(
        Assignment.class_id == student.current_class_id,
        Assignment.is_published == True,
        Assignment.is_active == True
    ).order_by(Assignment.due_date.desc())
    assignments = assignments_q.limit(5).all()

    assignments_payload = {
        "total": assignments_q.count(),
        "items": [
            {
                "id": a.id,
                "title": a.title,
                "subject": a.subject.name if a.subject else None,
                "due_date": a.due_date,
                "status": a.status,
            }
            for a in assignments
        ],
    }

    # Upcoming exams for student's class (next 30 days)
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    upcoming_q = db.query(Exam).filter(
        Exam.class_id == student.current_class_id,
        Exam.exam_date >= now,
    ).order_by(Exam.exam_date.asc())
    upcoming_exams = upcoming_q.limit(5).all()
    exams_payload = {
        "total": upcoming_q.count(),
        "items": [
            {
                "id": e.id,
                "title": e.title,
                "subject": e.subject.name if e.subject else None,
                "date": e.exam_date.date().isoformat() if e.exam_date else None,
                "time": e.start_time.isoformat() if e.start_time else None,
                "room": e.room_number,
            }
            for e in upcoming_exams
        ],
    }

    # Live classes for student's class (next 30 days)
    from app.models.live_class import LiveClass
    live_q = db.query(LiveClass).filter(
        LiveClass.class_id == student.current_class_id
    ).order_by(LiveClass.start_time.desc())
    live_classes = live_q.limit(5).all()
    live_payload = {
        "total": live_q.count(),
        "items": [
            {
                "id": lc.id,
                "subject": lc.topic,
                "teacher": None,
                "time": lc.start_time.isoformat() if lc.start_time else None,
                "status": lc.status.value if hasattr(lc.status, 'value') else lc.status,
            }
            for lc in live_classes
        ],
    }

    # Recent grades for this student
    grades_q = db.query(Grade).filter(Grade.student_id == student.id).order_by(Grade.graded_at.desc())
    grades = grades_q.limit(5).all()
    grades_payload = {
        "total": grades_q.count(),
        "items": [
            {
                "id": g.id,
                "subject": g.subject.name if g.subject else None,
                "assignment": g.assessment_name,
                "grade": g.grade_letter,
                "score": round((g.percentage or g.percentage_score or 0), 2),
            }
            for g in grades
        ],
    }

    return {
        "assignments": assignments_payload,
        "exams": exams_payload,
        "liveClasses": live_payload,
        "grades": grades_payload,
    }
