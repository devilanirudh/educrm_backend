"""
Parent management API endpoints
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
from app.models.user import User, Parent
from app.models.student import Student, AttendanceRecord, Grade
from app.models.academic import Class, Subject
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/me/profile", response_model=dict)
async def get_current_parent_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get the current user's parent profile"""
    
    # Check if user is a parent
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access their profile"
        )
    
    # Get parent profile
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    # If parent profile doesn't exist, create a basic one
    if not parent:
        parent = Parent(
            user_id=current_user.id,
            occupation="Not specified",
            workplace="Not specified",
            work_phone="Not specified",
            relationship_to_student="Parent",
            is_primary_contact=True,
            can_pickup_student=True,
            receives_notifications=True
        )
        db.add(parent)
        db.commit()
    
    return {
        "id": parent.id,
        "user_id": parent.user_id,
        "occupation": parent.occupation,
        "workplace": parent.workplace,
        "work_phone": parent.work_phone,
        "relationship_to_student": parent.relationship_to_student,
        "is_primary_contact": parent.is_primary_contact,
        "can_pickup_student": parent.can_pickup_student,
        "receives_notifications": parent.receives_notifications,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone": current_user.phone,
            "is_active": current_user.is_active
        }
    }

@router.get("/me/children", response_model=dict)
async def get_my_children(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get all children of the current parent"""
    
    # Check if user is a parent
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access their children"
        )
    
    # Get parent profile
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    # If parent profile doesn't exist, create a basic one
    if not parent:
        parent = Parent(
            user_id=current_user.id,
            occupation="Not specified",
            workplace="Not specified",
            work_phone="Not specified",
            relationship_to_student="Parent",
            is_primary_contact=True,
            can_pickup_student=True,
            receives_notifications=True
        )
        db.add(parent)
        db.commit()
    
    # Get children with detailed information
    children = db.query(Student).join(User).options(
        joinedload(Student.user),
        joinedload(Student.current_class)
    ).filter(Student.parents.any(id=parent.id)).all()
    
    children_list = []
    for child in children:
        # Get recent attendance
        recent_attendance = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == child.id
        ).order_by(AttendanceRecord.date.desc()).limit(5).all()
        
        # Get recent grades
        recent_grades = db.query(Grade).join(Subject).filter(
            Grade.student_id == child.id
        ).order_by(Grade.created_at.desc()).limit(5).all()
        
        child_data = {
            "id": child.id,
            "student_id": child.student_id,
            "user": {
                "id": child.user.id,
                "first_name": child.user.first_name,
                "last_name": child.user.last_name,
                "email": child.user.email,
                "phone": child.user.phone
            },
            "academic_info": {
                "current_class": {
                    "id": child.current_class.id,
                    "name": child.current_class.name,
                    "section": child.current_class.section,
                    "grade_level": child.current_class.grade_level
                } if child.current_class else None,
                "academic_year": child.academic_year,
                "roll_number": child.roll_number,
                "section": child.section,
                "admission_date": child.admission_date
            },
            "recent_attendance": [
                {
                    "date": record.date,
                    "status": record.status,
                    "check_in_time": record.actual_check_in,
                    "check_out_time": record.actual_check_out
                }
                for record in recent_attendance
            ],
            "recent_grades": [
                {
                    "subject": grade.subject.name,
                    "score": grade.score,
                    "max_score": grade.max_score,
                    "grade": grade.grade,
                    "created_at": grade.created_at
                }
                for grade in recent_grades
            ],
            "is_active": child.is_active
        }
        children_list.append(child_data)
    
    return {
        "parent_id": parent.id,
        "children": children_list,
        "total_children": len(children_list)
    }

@router.get("/me/children/{child_id}/attendance", response_model=dict)
async def get_child_attendance(
    child_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get attendance records for a specific child"""
    
    # Check if user is a parent
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access attendance records"
        )
    
    # Get parent profile
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    # If parent profile doesn't exist, create a basic one
    if not parent:
        parent = Parent(
            user_id=current_user.id,
            occupation="Not specified",
            workplace="Not specified",
            work_phone="Not specified",
            relationship_to_student="Parent",
            is_primary_contact=True,
            can_pickup_student=True,
            receives_notifications=True
        )
        db.add(parent)
        db.commit()
    
    # Get child and verify parent relationship
    child = db.query(Student).filter(
        Student.id == child_id,
        Student.parents.any(id=parent.id)
    ).first()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )
    
    # Get attendance records
    query = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == child_id)
    
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
        "child_id": child_id,
        "child_name": f"{child.user.first_name} {child.user.last_name}",
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

@router.get("/me/children/{child_id}/grades", response_model=dict)
async def get_child_grades(
    child_id: int,
    subject_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get grade records for a specific child"""
    
    # Check if user is a parent
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access grade records"
        )
    
    # Get parent profile
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    # If parent profile doesn't exist, create a basic one
    if not parent:
        parent = Parent(
            user_id=current_user.id,
            occupation="Not specified",
            workplace="Not specified",
            work_phone="Not specified",
            relationship_to_student="Parent",
            is_primary_contact=True,
            can_pickup_student=True,
            receives_notifications=True
        )
        db.add(parent)
        db.commit()
    
    # Get child and verify parent relationship
    child = db.query(Student).filter(
        Student.id == child_id,
        Student.parents.any(id=parent.id)
    ).first()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )
    
    # Get grade records
    query = db.query(Grade).join(Subject).filter(Grade.student_id == child_id)
    
    if subject_id:
        query = query.filter(Grade.subject_id == subject_id)
    
    grades = query.order_by(Grade.created_at.desc()).all()
    
    # Calculate average score
    total_score = sum(grade.score for grade in grades if grade.score is not None)
    total_max_score = sum(grade.max_score for grade in grades if grade.max_score is not None)
    average_percentage = (total_score / total_max_score * 100) if total_max_score > 0 else 0
    
    return {
        "child_id": child_id,
        "child_name": f"{child.user.first_name} {child.user.last_name}",
        "grades": [
            {
                "id": grade.id,
                "subject": {
                    "id": grade.subject.id,
                    "name": grade.subject.name,
                    "code": grade.subject.code
                },
                "score": grade.score,
                "max_score": grade.max_score,
                "grade": grade.grade,
                "comments": grade.comments,
                "created_at": grade.created_at
            }
            for grade in grades
        ],
        "statistics": {
            "total_grades": len(grades),
            "average_score": round(total_score / len(grades), 2) if grades else 0,
            "average_percentage": round(average_percentage, 2)
        }
    }

@router.get("/me/dashboard", response_model=dict)
async def get_parent_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get parent dashboard with overview of all children"""
    
    # Check if user is a parent
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access dashboard"
        )
    
    # Get parent profile
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    # If parent profile doesn't exist, create a basic one
    if not parent:
        parent = Parent(
            user_id=current_user.id,
            occupation="Not specified",
            workplace="Not specified",
            work_phone="Not specified",
            relationship_to_student="Parent",
            is_primary_contact=True,
            can_pickup_student=True,
            receives_notifications=True
        )
        db.add(parent)
        db.flush()  # Get the ID without committing
    
    # Get children
    children = db.query(Student).join(User).options(
        joinedload(Student.user),
        joinedload(Student.current_class)
    ).filter(Student.parents.any(id=parent.id)).all()
    
    dashboard_data = {
        "parent_info": {
            "id": parent.id,
            "name": f"{current_user.first_name} {current_user.last_name}",
            "email": current_user.email,
            "phone": current_user.phone
        },
        "children_overview": [],
        "total_children": len(children),
        "summary": {
            "total_attendance_days": 0,
            "total_present_days": 0,
            "overall_attendance_percentage": 0,
            "total_grades": 0,
            "average_grade_percentage": 0
        }
    }
    
    total_attendance_days = 0
    total_present_days = 0
    total_grades = 0
    total_grade_score = 0
    total_grade_max_score = 0
    
    for child in children:
        # Get recent attendance for this child
        recent_attendance = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == child.id
        ).order_by(AttendanceRecord.date.desc()).limit(30).all()  # Last 30 days
        
        # Get recent grades for this child
        recent_grades = db.query(Grade).filter(
            Grade.student_id == child.id
        ).order_by(Grade.created_at.desc()).limit(10).all()  # Last 10 grades
        
        # Calculate attendance stats for this child
        child_attendance_days = len(recent_attendance)
        child_present_days = len([r for r in recent_attendance if r.status == 'present'])
        child_attendance_percentage = (child_present_days / child_attendance_days * 100) if child_attendance_days > 0 else 0
        
        # Calculate grade stats for this child
        child_grades = len(recent_grades)
        child_total_score = sum(g.score for g in recent_grades if g.score is not None)
        child_total_max_score = sum(g.max_score for g in recent_grades if g.max_score is not None)
        child_grade_percentage = (child_total_score / child_total_max_score * 100) if child_total_max_score > 0 else 0
        
        # Update totals
        total_attendance_days += child_attendance_days
        total_present_days += child_present_days
        total_grades += child_grades
        total_grade_score += child_total_score
        total_grade_max_score += child_total_max_score
        
        child_overview = {
            "id": child.id,
            "student_id": child.student_id,
            "name": f"{child.user.first_name} {child.user.last_name}",
            "class": {
                "name": child.current_class.name if child.current_class else "Not Assigned",
                "section": child.current_class.section if child.current_class else None,
                "grade_level": child.current_class.grade_level if child.current_class else None
            },
            "attendance": {
                "total_days": child_attendance_days,
                "present_days": child_present_days,
                "percentage": round(child_attendance_percentage, 2)
            },
            "grades": {
                "total_grades": child_grades,
                "average_percentage": round(child_grade_percentage, 2)
            },
            "is_active": child.is_active
        }
        
        dashboard_data["children_overview"].append(child_overview)
    
    # Calculate overall summary
    if total_attendance_days > 0:
        dashboard_data["summary"]["overall_attendance_percentage"] = round((total_present_days / total_attendance_days) * 100, 2)
    
    if total_grade_max_score > 0:
        dashboard_data["summary"]["average_grade_percentage"] = round((total_grade_score / total_grade_max_score) * 100, 2)
    
    dashboard_data["summary"]["total_attendance_days"] = total_attendance_days
    dashboard_data["summary"]["total_present_days"] = total_present_days
    dashboard_data["summary"]["total_grades"] = total_grades
    
    return dashboard_data
