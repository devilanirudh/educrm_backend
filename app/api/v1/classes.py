"""Class management API endpoints"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database.session import get_db
from app.models.academic import Class, ClassSubject, Subject
from app.models.student import Student
from app.models.teacher import Teacher
from app.schemas.classes import (
    ClassCreate, 
    ClassUpdate, 
    ClassResponse, 
    ClassListResponse,
    ClassSubjectCreate,
    ClassSubjectResponse
)
from app.core.permissions import get_current_user, UserRole
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=ClassListResponse)
async def get_classes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by class name or section"),
    grade_level: Optional[int] = Query(None, description="Filter by grade level"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all classes with pagination and filtering"""
    query = db.query(Class)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Class.name.ilike(f"%{search}%"),
                Class.section.ilike(f"%{search}%")
            )
        )
    
    if grade_level is not None:
        query = query.filter(Class.grade_level == grade_level)
    
    if academic_year:
        query = query.filter(Class.academic_year == academic_year)
    
    if is_active is not None:
        query = query.filter(Class.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    classes = query.offset(skip).limit(limit).all()
    
    return {
        "data": classes,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific class by ID"""
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return class_obj

@router.post("/", response_model=ClassResponse)
async def create_class(
    class_data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new class"""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check if class already exists
    existing_class = db.query(Class).filter(
        and_(
            Class.name == class_data.name,
            Class.section == class_data.section,
            Class.academic_year == class_data.academic_year
        )
    ).first()
    
    if existing_class:
        raise HTTPException(status_code=400, detail="Class already exists")
    
    class_obj = Class(**class_data.dict())
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)
    
    return class_obj

@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: int,
    class_data: ClassUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a class"""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Update fields
    for field, value in class_data.dict(exclude_unset=True).items():
        setattr(class_obj, field, value)
    
    db.commit()
    db.refresh(class_obj)
    
    return class_obj

@router.delete("/{class_id}")
async def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a class"""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check if class has students
    student_count = db.query(Student).filter(Student.current_class_id == class_id).count()
    if student_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete class with enrolled students")
    
    db.delete(class_obj)
    db.commit()
    
    return {"message": "Class deleted successfully"}

@router.get("/{class_id}/students", response_model=Dict[str, Any])
async def get_class_students(
    class_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get students enrolled in a class"""
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    students = db.query(Student).filter(
        Student.current_class_id == class_id
    ).offset(skip).limit(limit).all()
    
    total = db.query(Student).filter(Student.current_class_id == class_id).count()
    
    return {
        "data": students,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{class_id}/subjects", response_model=List[ClassSubjectResponse])
async def get_class_subjects(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get subjects assigned to a class"""
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    class_subjects = db.query(ClassSubject).filter(
        ClassSubject.class_id == class_id
    ).all()
    
    return class_subjects

@router.post("/{class_id}/subjects", response_model=ClassSubjectResponse)
async def add_subject_to_class(
    class_id: int,
    subject_data: ClassSubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a subject to a class"""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check if subject exists
    subject = db.query(Subject).filter(Subject.id == subject_data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Check if subject is already assigned to this class
    existing = db.query(ClassSubject).filter(
        and_(
            ClassSubject.class_id == class_id,
            ClassSubject.subject_id == subject_data.subject_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Subject already assigned to this class")
    
    class_subject = ClassSubject(
        class_id=class_id,
        **subject_data.dict()
    )
    
    db.add(class_subject)
    db.commit()
    db.refresh(class_subject)
    
    return class_subject

@router.delete("/{class_id}/subjects/{subject_id}")
async def remove_subject_from_class(
    class_id: int,
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a subject from a class"""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    class_subject = db.query(ClassSubject).filter(
        and_(
            ClassSubject.class_id == class_id,
            ClassSubject.subject_id == subject_id
        )
    ).first()
    
    if not class_subject:
        raise HTTPException(status_code=404, detail="Subject not found in this class")
    
    db.delete(class_subject)
    db.commit()
    
    return {"message": "Subject removed from class successfully"}

@router.get("/{class_id}/teachers", response_model=List[Dict[str, Any]])
async def get_class_teachers(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get teachers assigned to a class"""
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Get class teacher
    class_teacher = None
    if class_obj.class_teacher_id:
        class_teacher = db.query(Teacher).filter(Teacher.id == class_obj.class_teacher_id).first()
    
    # Get subject teachers
    subject_teachers = db.query(Teacher).join(ClassSubject).filter(
        ClassSubject.class_id == class_id
    ).distinct().all()
    
    return {
        "class_teacher": class_teacher,
        "subject_teachers": subject_teachers
    }

@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_classes_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get classes statistics overview"""
    total_classes = db.query(Class).count()
    active_classes = db.query(Class).filter(Class.is_active == True).count()
    total_students = db.query(Student).count()
    
    # Classes by grade level
    grade_distribution = db.query(
        Class.grade_level,
        db.func.count(Class.id).label('count')
    ).group_by(Class.grade_level).all()
    
    return {
        "total_classes": total_classes,
        "active_classes": active_classes,
        "total_students": total_students,
        "grade_distribution": [
            {"grade_level": grade, "count": count} 
            for grade, count in grade_distribution
        ]
    }
