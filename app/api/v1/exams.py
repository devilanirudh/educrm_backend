"""
Exam management API endpoints
"""

from typing import Any, List, Optional
from datetime import date, datetime, time
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from app.database.session import get_db
from app.api.deps import get_current_user
from app.core.permissions import UserRole
from app.core.role_config import role_config
from app.models.user import User
from app.models.academic import Exam, ExamResult, ExamAnswer
from app.models.teacher import Teacher
from app.models.form import Form, FieldType
import logging
import os
from werkzeug.utils import secure_filename

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

# Get student exams endpoint
@router.get("/my-exams", response_model=dict)
async def get_student_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get exams for the current student"""
    
    # Check if current user is a student
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access their exams"
        )
    
    # Get student record
    from app.models.student import Student
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student record not found"
        )
    
    # Get exams for student's class
    exams = db.query(Exam).filter(
        Exam.class_id == student.current_class_id,
        Exam.status.in_(["draft", "published", "active", "completed", "cancelled"])
    ).options(
        joinedload(Exam.subject),
        joinedload(Exam.teacher).joinedload(Teacher.user)
    ).all()
    
    # Format response
    exams_list = []
    for exam in exams:
        exams_list.append({
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "exam_date": exam.exam_date,
            "duration_minutes": exam.duration_minutes,
            "max_score": exam.max_score,
            "status": exam.status,
            "subject": {
                "id": exam.subject.id,
                "name": exam.subject.name
            } if exam.subject else None,
            "teacher": {
                "id": exam.teacher.id,
                "first_name": exam.teacher.user.first_name,
                "last_name": exam.teacher.user.last_name
            } if exam.teacher else None
        })
    
    return {
        "exams": exams_list,
        "total": len(exams_list)
    }

# Dropdown endpoints for exam form
@router.get("/available-teachers", response_model=dict)
async def get_available_teachers_for_exam(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get available teachers for exam creation"""
    
    # Check permissions
    if not role_config.can_access_module(current_user.role.value, "exams"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access exams module"
        )
    
    # Get all active teachers
    teachers = db.query(Teacher).filter(Teacher.is_active == True).options(
        joinedload(Teacher.user)
    ).all()
    
    # Format response
    teachers_list = []
    for teacher in teachers:
        teachers_list.append({
            "value": str(teacher.id),
            "label": f"{teacher.user.first_name} {teacher.user.last_name} ({teacher.employee_id})"
        })
    
    return {"teachers": teachers_list}

@router.get("/available-classes/{teacher_id}", response_model=dict)
async def get_available_classes_for_teacher_exam(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get available classes for a specific teacher"""
    
    # Check permissions
    if not role_config.can_access_module(current_user.role.value, "exams"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access exams module"
        )
    
    # Get classes assigned to the teacher
    from app.models.academic import Class, ClassSubject
    classes = db.query(Class).join(ClassSubject).filter(
        ClassSubject.teacher_id == teacher_id,
        Class.is_active == True
    ).distinct().all()
    
    # Format response
    classes_list = []
    for class_info in classes:
        classes_list.append({
            "value": str(class_info.id),
            "label": f"{class_info.name} - {class_info.section}"
        })
    
    return {"classes": classes_list}

@router.get("/available-subjects/{teacher_id}/{class_id}", response_model=dict)
async def get_available_subjects_for_teacher_class_exam(
    teacher_id: int,
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get available subjects for a specific teacher and class"""
    
    # Check permissions
    if not role_config.can_access_module(current_user.role.value, "exams"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access exams module"
        )
    
    # Get subjects taught by the teacher in the specific class
    from app.models.academic import Subject, ClassSubject
    subjects = db.query(Subject).join(ClassSubject).filter(
        ClassSubject.teacher_id == teacher_id,
        ClassSubject.class_id == class_id
    ).all()
    
    # Format response
    subjects_list = []
    for subject in subjects:
        subjects_list.append({
            "value": str(subject.id),
            "label": f"{subject.name} ({subject.code})"
        })
    
    return {"subjects": subjects_list}

# File upload endpoint for exams
@router.post("/upload-file", response_model=dict)
async def upload_exam_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Upload file for exam materials or images"""
    
    # Check permissions - allow students, teachers, admin, staff
    if current_user.role not in [UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to upload files"
        )
    
    # Validate file type
    allowed_extensions = {
        'image': ['.jpg', '.jpeg', '.png', '.gif'],
        'document': ['.pdf', '.doc', '.docx', '.txt']
    }
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    is_image = file_extension in allowed_extensions['image']
    is_document = file_extension in allowed_extensions['document']
    
    if not (is_image or is_document):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: images (jpg, jpeg, png, gif) and documents (pdf, doc, docx, txt)"
        )
    
    # Validate file size (10MB for documents, 5MB for images)
    max_size = 5 * 1024 * 1024 if is_image else 10 * 1024 * 1024  # 5MB or 10MB
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"exam_{timestamp}_{secure_filename(file.filename)}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            if len(content) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Maximum size: {max_size // (1024*1024)}MB"
                )
            buffer.write(content)
        
        # Return file URL
        file_url = f"/uploads/{safe_filename}"
        
        logger.info(f"File uploaded successfully: {file_url} by user {current_user.email}")
        
        return {
            "message": "File uploaded successfully",
            "file_url": file_url,
            "filename": file.filename,
            "file_type": "image" if is_image else "document"
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
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

    # Check permissions - users need access to exams module
    if not role_config.can_access_module(current_user.role.value, "exams"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access exams module"
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

        if exam_data.class_id is not None:
            exam.class_id = exam_data.class_id
        if exam_data.exam_date is not None:
            exam.exam_date = exam_data.exam_date
        if exam_data.start_time is not None:
            try:
                start_time_obj = datetime.strptime(exam_data.start_time, "%H:%M").time() if exam_data.start_time else None
                exam.start_time = start_time_obj
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start time format. Use HH:MM"
                )
        if exam_data.end_time is not None:
            try:
                end_time_obj = datetime.strptime(exam_data.end_time, "%H:%M").time() if exam_data.end_time else None
                exam.end_time = end_time_obj
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end time format. Use HH:MM"
                )
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

        logger.info(f"Exam '{exam.title}' (ID: {exam.id}) updated by {current_user.email}")

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

    # Check if current user has permission to access exams module
    if not role_config.can_access_module(current_user.role.value, "exams"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access exams module"
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

        logger.info(f"Exam '{exam.title}' (ID: {exam.id}) cancelled by {current_user.email}")

        return {"message": "Exam cancelled successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel exam"
        )

# Exam Submission Schemas
class ExamSubmissionCreate(BaseModel):
    """Schema for creating a new exam submission"""
    answers: List[dict]  # List of question answers
    time_taken_minutes: Optional[int] = None
    notes: Optional[str] = None

class ExamSubmissionGrade(BaseModel):
    """Schema for grading an exam submission"""
    score: float
    teacher_comments: Optional[str] = None
    individual_feedback: Optional[List[dict]] = None  # Feedback for each question

# Exam Submission Endpoints
@router.post("/{exam_id}/submit", response_model=dict)
async def submit_exam(
    exam_id: int,
    submission_data: ExamSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Submit an exam (student endpoint)"""
    
    # Check if current user is a student
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit exams"
        )
    
    # Get the exam
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    # Check if exam is published/active
    if exam.status not in ["published", "active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam is not available for submission"
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
    if student.current_class_id != exam.class_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit exams for your class"
        )
    
    # Check if already submitted
    existing_result = db.query(ExamResult).filter(
        ExamResult.exam_id == exam_id,
        ExamResult.student_id == student.id
    ).first()
    
    if existing_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam already submitted"
        )
    
    try:
        # Calculate initial score (for auto-graded questions)
        total_score = 0.0
        max_score = 0.0
        
        # Get exam questions
        from app.models.academic import ExamQuestion
        questions = db.query(ExamQuestion).filter(
            ExamQuestion.exam_id == exam_id
        ).order_by(ExamQuestion.order_number).all()
        
        # Create exam result
        exam_result = ExamResult(
            exam_id=exam_id,
            student_id=student.id,
            score=0.0,  # Will be updated after grading
            max_score=exam.max_score,
            percentage=0.0,  # Will be calculated after grading
            start_time=datetime.now(),
            end_time=datetime.now(),
            time_taken_minutes=submission_data.time_taken_minutes,
            status="submitted",
            is_passed=False  # Will be determined after grading
        )
        
        db.add(exam_result)
        db.flush()  # Get the result ID
        
        # Process answers and calculate auto-graded score
        for answer_data in submission_data.answers:
            question_id = answer_data.get('question_id')
            answer_text = answer_data.get('answer_text')
            selected_option = answer_data.get('selected_option')
            
            # Find the question
            question = next((q for q in questions if q.id == question_id), None)
            if not question:
                continue
            
            max_score += question.points
            
            # Check if answer is correct (for auto-graded questions)
            is_correct = False
            points_earned = 0.0
            
            if question.question_type in ['mcq', 'true_false']:
                if selected_option == question.correct_answer:
                    is_correct = True
                    points_earned = question.points
                    total_score += question.points
            
            # Create exam answer record
            exam_answer = ExamAnswer(
                result_id=exam_result.id,
                question_id=question_id,
                answer_text=answer_text,
                selected_option=selected_option,
                is_correct=is_correct,
                points_earned=points_earned
            )
            
            db.add(exam_answer)
        
        # Update result with auto-graded score
        exam_result.score = total_score
        exam_result.percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Determine if passed
        if exam.passing_score:
            exam_result.is_passed = total_score >= exam.passing_score
        
        db.commit()
        db.refresh(exam_result)
        
        logger.info(f"Exam {exam_id} submitted by student {student.id}")
        
        return {
            "message": "Exam submitted successfully",
            "result_id": exam_result.id,
            "auto_score": total_score,
            "max_score": max_score,
            "percentage": exam_result.percentage
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit exam"
        )

@router.get("/{exam_id}/results", response_model=dict)
async def get_exam_results(
    exam_id: int,
    status: Optional[str] = Query(None, description="Filter by result status"),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get results for an exam (teacher/admin endpoint)"""
    
    # Check permissions
    if not role_config.can_access_module(current_user.role.value, "exams"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access exams module"
        )
    
    # Get the exam
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    # Build query
    query = db.query(ExamResult).filter(ExamResult.exam_id == exam_id)
    
    # Apply filters
    if status:
        query = query.filter(ExamResult.status == status)
    if student_id:
        query = query.filter(ExamResult.student_id == student_id)
    
    # Get results with student info
    results = query.options(
        joinedload(ExamResult.student).joinedload(Student.user)
    ).all()
    
    # Format response
    result_list = []
    for result in results:
        result_list.append({
            "id": result.id,
            "student_id": result.student_id,
            "student_name": f"{result.student.user.first_name} {result.student.user.last_name}",
            "student_email": result.student.user.email,
            "score": result.score,
            "max_score": result.max_score,
            "percentage": result.percentage,
            "grade_letter": result.grade_letter,
            "rank": result.rank,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "time_taken_minutes": result.time_taken_minutes,
            "status": result.status,
            "is_passed": result.is_passed,
            "teacher_comments": result.teacher_comments,
            "created_at": result.created_at
        })
    
    return {
        "results": result_list,
        "total": len(result_list)
    }

@router.post("/{exam_id}/results/{result_id}/grade", response_model=dict)
async def grade_exam_result(
    exam_id: int,
    result_id: int,
    grade_data: ExamSubmissionGrade,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Grade an exam result (teacher endpoint)"""
    
    # Check permissions
    if not role_config.can_access_module(current_user.role.value, "exams"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access exams module"
        )
    
    # Get the result
    result = db.query(ExamResult).filter(
        ExamResult.id == result_id,
        ExamResult.exam_id == exam_id
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam result not found"
        )
    
    try:
        # Update result with grade
        result.score = grade_data.score
        result.percentage = (grade_data.score / result.max_score * 100) if result.max_score > 0 else 0
        result.teacher_comments = grade_data.teacher_comments
        result.status = "graded"
        
        # Calculate grade letter (simple A-F scale)
        if result.percentage >= 90:
            result.grade_letter = "A"
        elif result.percentage >= 80:
            result.grade_letter = "B"
        elif result.percentage >= 70:
            result.grade_letter = "C"
        elif result.percentage >= 60:
            result.grade_letter = "D"
        else:
            result.grade_letter = "F"
        
        # Update individual question feedback if provided
        if grade_data.individual_feedback:
            for feedback_item in grade_data.individual_feedback:
                answer_id = feedback_item.get('answer_id')
                feedback_text = feedback_item.get('feedback')
                points_earned = feedback_item.get('points_earned')
                
                if answer_id and feedback_text:
                    answer = db.query(ExamAnswer).filter(ExamAnswer.id == answer_id).first()
                    if answer:
                        answer.teacher_feedback = feedback_text
                        if points_earned is not None:
                            answer.points_earned = points_earned
        
        db.commit()
        db.refresh(result)
        
        logger.info(f"Exam result {result_id} graded by {current_user.email} with score {grade_data.score}")
        
        return {
            "message": "Exam result graded successfully",
            "result_id": result.id,
            "score": result.score,
            "grade_letter": result.grade_letter
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error grading exam result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grade exam result"
        )

# Student exam result viewing endpoint
@router.get("/{exam_id}/my-result", response_model=dict)
async def get_my_exam_result(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current student's result for an exam"""
    
    # Check if current user is a student
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their own exam results"
        )
    
    # Get the exam
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    # Get student record
    from app.models.student import Student
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student record not found"
        )
    
    # Get student's result
    result = db.query(ExamResult).filter(
        ExamResult.exam_id == exam_id,
        ExamResult.student_id == student.id
    ).first()
    
    if not result:
        return {
            "result": None,
            "message": "No result found for this exam"
        }
    
    # Get answers with questions
    answers = db.query(ExamAnswer).options(
        joinedload(ExamAnswer.question)
    ).filter(ExamAnswer.result_id == result.id).all()
    
    # Format response
    result_data = {
        "id": result.id,
        "score": result.score,
        "max_score": result.max_score,
        "percentage": result.percentage,
        "grade_letter": result.grade_letter,
        "rank": result.rank,
        "start_time": result.start_time,
        "end_time": result.end_time,
        "time_taken_minutes": result.time_taken_minutes,
        "status": result.status,
        "is_passed": result.is_passed,
        "teacher_comments": result.teacher_comments,
        "created_at": result.created_at,
        "answers": []
    }
    
    for answer in answers:
        result_data["answers"].append({
            "id": answer.id,
            "question_text": answer.question.question_text,
            "question_type": answer.question.question_type,
            "answer_text": answer.answer_text,
            "selected_option": answer.selected_option,
            "is_correct": answer.is_correct,
            "points_earned": answer.points_earned,
            "teacher_feedback": answer.teacher_feedback
        })
    
    return {
        "result": result_data,
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "max_score": exam.max_score,
            "passing_score": exam.passing_score,
            "exam_date": exam.exam_date
        }
    }

# Get exam questions endpoint
@router.get("/{exam_id}/questions", response_model=dict)
async def get_exam_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get questions for an exam"""
    
    # Get the exam
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    # Get questions
    from app.models.academic import ExamQuestion
    questions = db.query(ExamQuestion).filter(
        ExamQuestion.exam_id == exam_id
    ).order_by(ExamQuestion.order_number).all()
    
    # Format response
    questions_list = []
    for question in questions:
        questions_list.append({
            "id": question.id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "options": question.options,
            "points": question.points,
            "order_number": question.order_number,
            "explanation": question.explanation,
            "image_path": question.image_path
        })
    
    return {
        "questions": questions_list,
        "total": len(questions_list)
    }

