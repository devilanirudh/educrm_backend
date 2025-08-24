"""
Comprehensive Attendance Management API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Optional, Any, Dict
from datetime import datetime, date, timedelta
import logging
from pydantic import BaseModel
from enum import Enum

from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.academic import Class, Subject
from app.models.student import (
    AttendanceRecord, AttendancePolicy, AttendanceSession, 
    PeriodAttendance, AttendanceException, AttendanceNotification
)
from app.api.deps import get_current_user
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["attendance"])

# Pydantic Models
class AttendanceStatusEnum(str, Enum):
    present = "present"
    absent = "absent"
    late = "late"
    excused = "excused"
    half_day = "half_day"
    sick_leave = "sick_leave"
    personal_leave = "personal_leave"
    emergency_leave = "emergency_leave"


class AttendanceRecordCreate(BaseModel):
    student_id: int
    class_id: int
    date: date
    status: AttendanceStatusEnum
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    expected_hours: Optional[float] = None


class BulkAttendanceCreate(BaseModel):
    class_id: int
    date: date
    records: List[AttendanceRecordCreate]
    policy_id: Optional[int] = None


class AttendancePolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    class_id: Optional[int] = None
    academic_year: str
    school_start_time: str  # "HH:MM" format
    school_end_time: str    # "HH:MM" format
    late_threshold_minutes: int = 15
    early_departure_threshold_minutes: int = 30
    minimum_attendance_percentage: float = 75.0
    max_consecutive_absences: int = 5
    max_total_absences: int = 30
    notify_parents_on_absence: bool = True
    notify_parents_on_late: bool = False
    notify_after_consecutive_absences: int = 3
    auto_mark_absent_after_minutes: Optional[int] = None
    allow_self_check_in: bool = False
    allow_self_check_out: bool = False
    grace_period_minutes: int = 5
    half_day_threshold_hours: float = 4.0
    working_days: List[str] = ["monday", "tuesday", "wednesday", "thursday", "friday"]


class AttendanceSessionCreate(BaseModel):
    class_id: int
    subject_id: Optional[int] = None
    session_name: str
    start_time: str  # "HH:MM" format
    end_time: str    # "HH:MM" format
    late_threshold_minutes: int = 5
    is_required: bool = True
    weight: float = 1.0


class AttendanceReportRequest(BaseModel):
    class_id: Optional[int] = None
    student_id: Optional[int] = None
    start_date: date
    end_date: date
    include_details: bool = False
    group_by: str = "student"  # student, date, subject


# Attendance Policies Management
@router.post("/policies", response_model=dict)
async def create_attendance_policy(
    policy_data: AttendancePolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new attendance policy"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and teachers can create attendance policies"
        )
    
    try:
        # Convert time strings to Time objects
        from datetime import time
        start_time = datetime.strptime(policy_data.school_start_time, "%H:%M").time()
        end_time = datetime.strptime(policy_data.school_end_time, "%H:%M").time()
        
        policy = AttendancePolicy(
            name=policy_data.name,
            description=policy_data.description,
            class_id=policy_data.class_id,
            academic_year=policy_data.academic_year,
            school_start_time=start_time,
            school_end_time=end_time,
            late_threshold_minutes=policy_data.late_threshold_minutes,
            early_departure_threshold_minutes=policy_data.early_departure_threshold_minutes,
            minimum_attendance_percentage=policy_data.minimum_attendance_percentage,
            max_consecutive_absences=policy_data.max_consecutive_absences,
            max_total_absences=policy_data.max_total_absences,
            notify_parents_on_absence=policy_data.notify_parents_on_absence,
            notify_parents_on_late=policy_data.notify_parents_on_late,
            notify_after_consecutive_absences=policy_data.notify_after_consecutive_absences,
            auto_mark_absent_after_minutes=policy_data.auto_mark_absent_after_minutes,
            allow_self_check_in=policy_data.allow_self_check_in,
            allow_self_check_out=policy_data.allow_self_check_out,
            grace_period_minutes=policy_data.grace_period_minutes,
            half_day_threshold_hours=policy_data.half_day_threshold_hours,
            working_days=policy_data.working_days,
            created_by=current_user.id
        )
        
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        logger.info(f"Attendance policy '{policy.name}' created by {current_user.email}")
        
        return {
            "message": "Attendance policy created successfully",
            "policy_id": policy.id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating attendance policy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attendance policy"
        )


@router.get("/policies", response_model=dict)
async def list_attendance_policies(
    class_id: Optional[int] = Query(None),
    academic_year: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List attendance policies"""
    
    query = db.query(AttendancePolicy).options(
        joinedload(AttendancePolicy.class_info),
        joinedload(AttendancePolicy.creator)
    )
    
    if class_id:
        query = query.filter(AttendancePolicy.class_id == class_id)
    if academic_year:
        query = query.filter(AttendancePolicy.academic_year == academic_year)
    if is_active is not None:
        query = query.filter(AttendancePolicy.is_active == is_active)
    
    policies = query.order_by(desc(AttendancePolicy.created_at)).all()
    
    return {
        "policies": [
            {
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "class_id": policy.class_id,
                "class_name": policy.class_info.name if policy.class_info else None,
                "academic_year": policy.academic_year,
                "school_start_time": str(policy.school_start_time),
                "school_end_time": str(policy.school_end_time),
                "minimum_attendance_percentage": policy.minimum_attendance_percentage,
                "created_by": policy.creator.email if policy.creator else None,
                "created_at": policy.created_at,
                "is_active": policy.is_active
            }
            for policy in policies
        ]
    }


# Bulk Attendance Operations
@router.post("/bulk", response_model=dict)
async def mark_bulk_attendance(
    bulk_data: BulkAttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Mark attendance for multiple students at once"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and administrators can mark attendance"
        )
    
    try:
        # Get the class and verify teacher has access
        class_info = db.query(Class).filter(Class.id == bulk_data.class_id).first()
        if not class_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        
        # Get policy if specified
        policy = None
        if bulk_data.policy_id:
            policy = db.query(AttendancePolicy).filter(AttendancePolicy.id == bulk_data.policy_id).first()
        
        success_count = 0
        error_count = 0
        errors = []
        
        for record_data in bulk_data.records:
            try:
                # Check if attendance already exists
                existing = db.query(AttendanceRecord).filter(
                    and_(
                        AttendanceRecord.student_id == record_data.student_id,
                        AttendanceRecord.class_id == record_data.class_id,
                        AttendanceRecord.date == bulk_data.date
                    )
                ).first()
                
                if existing:
                    # Update existing record
                    existing.status = record_data.status
                    existing.check_in_time = record_data.check_in_time
                    existing.check_out_time = record_data.check_out_time
                    existing.reason = record_data.reason
                    existing.notes = record_data.notes
                    existing.expected_hours = record_data.expected_hours
                    existing.updated_at = datetime.utcnow()
                    success_count += 1
                else:
                    # Create new record
                    attendance = AttendanceRecord(
                        student_id=record_data.student_id,
                        class_id=record_data.class_id,
                        policy_id=policy.id if policy else None,
                        date=bulk_data.date,
                        status=record_data.status,
                        check_in_time=record_data.check_in_time,
                        check_out_time=record_data.check_out_time,
                        reason=record_data.reason,
                        notes=record_data.notes,
                        expected_hours=record_data.expected_hours,
                        marked_by=current_user.id
                    )
                    db.add(attendance)
                    success_count += 1
                    
            except Exception as e:
                error_count += 1
                errors.append(f"Student {record_data.student_id}: {str(e)}")
        
        db.commit()
        
        logger.info(f"Bulk attendance marked for {success_count} students by {current_user.email}")
        
        return {
            "message": f"Attendance marked for {success_count} students",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking bulk attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark bulk attendance"
        )


# Attendance Reports
@router.post("/reports", response_model=dict)
async def generate_attendance_report(
    report_request: AttendanceReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generate comprehensive attendance reports"""
    
    try:
        # Build base query
        query = db.query(AttendanceRecord).options(
            joinedload(AttendanceRecord.student).joinedload(Student.user),
            joinedload(AttendanceRecord.class_info)
        )
        
        # Apply filters
        if report_request.class_id:
            query = query.filter(AttendanceRecord.class_id == report_request.class_id)
        if report_request.student_id:
            query = query.filter(AttendanceRecord.student_id == report_request.student_id)
        
        query = query.filter(
            and_(
                AttendanceRecord.date >= report_request.start_date,
                AttendanceRecord.date <= report_request.end_date
            )
        )
        
        records = query.order_by(AttendanceRecord.date.desc()).all()
        
        # Calculate statistics
        total_records = len(records)
        present_count = len([r for r in records if r.status == 'present'])
        absent_count = len([r for r in records if r.status == 'absent'])
        late_count = len([r for r in records if r.status == 'late'])
        excused_count = len([r for r in records if r.status == 'excused'])
        
        attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
        
        # Group by student if requested
        student_stats = {}
        if report_request.group_by == "student":
            for record in records:
                student_id = record.student_id
                if student_id not in student_stats:
                    student_stats[student_id] = {
                        "student_id": student_id,
                        "student_name": f"{record.student.user.first_name} {record.student.user.last_name}",
                        "class_name": record.class_info.name,
                        "total_days": 0,
                        "present_days": 0,
                        "absent_days": 0,
                        "late_days": 0,
                        "excused_days": 0,
                        "attendance_percentage": 0,
                        "details": [] if report_request.include_details else None
                    }
                
                student_stats[student_id]["total_days"] += 1
                if record.status == 'present':
                    student_stats[student_id]["present_days"] += 1
                elif record.status == 'absent':
                    student_stats[student_id]["absent_days"] += 1
                elif record.status == 'late':
                    student_stats[student_id]["late_days"] += 1
                elif record.status == 'excused':
                    student_stats[student_id]["excused_days"] += 1
                
                if report_request.include_details:
                    student_stats[student_id]["details"].append({
                        "date": record.date,
                        "status": record.status,
                        "check_in_time": record.actual_check_in,
                        "check_out_time": record.actual_check_out,
                        "reason": record.reason
                    })
            
            # Calculate percentages
            for stats in student_stats.values():
                if stats["total_days"] > 0:
                    stats["attendance_percentage"] = round(
                        (stats["present_days"] / stats["total_days"]) * 100, 2
                    )
        
        return {
            "report_summary": {
                "total_records": total_records,
                "present_count": present_count,
                "absent_count": absent_count,
                "late_count": late_count,
                "excused_count": excused_count,
                "overall_attendance_percentage": round(attendance_percentage, 2),
                "date_range": {
                    "start_date": report_request.start_date,
                    "end_date": report_request.end_date
                }
            },
            "student_statistics": list(student_stats.values()) if report_request.group_by == "student" else None,
            "detailed_records": [
                {
                    "id": record.id,
                    "student_id": record.student_id,
                    "student_name": f"{record.student.user.first_name} {record.student.user.last_name}",
                    "class_name": record.class_info.name,
                    "date": record.date,
                    "status": record.status,
                    "check_in_time": record.actual_check_in,
                    "check_out_time": record.actual_check_out,
                    "reason": record.reason,
                    "notes": record.notes
                }
                for record in records
            ] if report_request.include_details else None
        }
        
    except Exception as e:
        logger.error(f"Error generating attendance report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate attendance report"
        )


# Attendance Sessions Management
@router.post("/sessions", response_model=dict)
async def create_attendance_session(
    session_data: AttendanceSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new attendance session"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and teachers can create attendance sessions"
        )
    
    try:
        # Convert time strings to Time objects
        start_time = datetime.strptime(session_data.start_time, "%H:%M").time()
        end_time = datetime.strptime(session_data.end_time, "%H:%M").time()
        
        session = AttendanceSession(
            class_id=session_data.class_id,
            subject_id=session_data.subject_id,
            session_name=session_data.session_name,
            start_time=start_time,
            end_time=end_time,
            late_threshold_minutes=session_data.late_threshold_minutes,
            is_required=session_data.is_required,
            weight=session_data.weight
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Attendance session '{session.session_name}' created by {current_user.email}")
        
        return {
            "message": "Attendance session created successfully",
            "session_id": session.id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating attendance session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attendance session"
        )


@router.get("/sessions", response_model=dict)
async def list_attendance_sessions(
    class_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List attendance sessions"""
    
    query = db.query(AttendanceSession).options(
        joinedload(AttendanceSession.class_info),
        joinedload(AttendanceSession.subject)
    )
    
    if class_id:
        query = query.filter(AttendanceSession.class_id == class_id)
    if is_active is not None:
        query = query.filter(AttendanceSession.is_active == is_active)
    
    sessions = query.order_by(AttendanceSession.start_time).all()
    
    return {
        "sessions": [
            {
                "id": session.id,
                "session_name": session.session_name,
                "class_id": session.class_id,
                "class_name": session.class_info.name if session.class_info else None,
                "subject_id": session.subject_id,
                "subject_name": session.subject.name if session.subject else None,
                "start_time": str(session.start_time),
                "end_time": str(session.end_time),
                "late_threshold_minutes": session.late_threshold_minutes,
                "is_required": session.is_required,
                "weight": session.weight,
                "is_active": session.is_active
            }
            for session in sessions
        ]
    }


# Student Self Check-in/Check-out
@router.post("/check-in", response_model=dict)
async def student_check_in(
    class_id: int,
    location: Optional[Dict[str, float]] = None,  # {lat, lng}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Student self check-in"""
    
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can check in"
        )
    
    try:
        # Get student record
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student record not found"
            )
        
        # Check if self check-in is allowed
        policy = db.query(AttendancePolicy).filter(
            and_(
                AttendancePolicy.class_id == class_id,
                AttendancePolicy.is_active == True
            )
        ).first()
        
        if not policy or not policy.allow_self_check_in:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Self check-in is not allowed for this class"
            )
        
        today = date.today()
        now = datetime.utcnow()
        
        # Check if attendance record exists for today
        attendance = db.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.class_id == class_id,
                AttendanceRecord.date == today
            )
        ).first()
        
        if not attendance:
            # Create new attendance record
            attendance = AttendanceRecord(
                student_id=student.id,
                class_id=class_id,
                policy_id=policy.id,
                date=today,
                status='present',
                actual_check_in=now,
                expected_check_in=policy.school_start_time,
                check_in_location=location,
                check_in_device="mobile",
                marked_by=current_user.id
            )
            db.add(attendance)
        else:
            # Update existing record
            attendance.actual_check_in = now
            attendance.check_in_location = location
            attendance.check_in_device = "mobile"
            attendance.status = 'present'
        
        db.commit()
        
        logger.info(f"Student {current_user.email} checked in for class {class_id}")
        
        return {
            "message": "Check-in successful",
            "check_in_time": now,
            "status": attendance.status
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during student check-in: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check in"
        )


@router.post("/check-out", response_model=dict)
async def student_check_out(
    class_id: int,
    location: Optional[Dict[str, float]] = None,  # {lat, lng}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Student self check-out"""
    
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can check out"
        )
    
    try:
        # Get student record
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student record not found"
            )
        
        # Check if self check-out is allowed
        policy = db.query(AttendancePolicy).filter(
            and_(
                AttendancePolicy.class_id == class_id,
                AttendancePolicy.is_active == True
            )
        ).first()
        
        if not policy or not policy.allow_self_check_out:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Self check-out is not allowed for this class"
            )
        
        today = date.today()
        now = datetime.utcnow()
        
        # Get attendance record for today
        attendance = db.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.class_id == class_id,
                AttendanceRecord.date == today
            )
        ).first()
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No check-in record found for today"
            )
        
        # Update check-out time
        attendance.actual_check_out = now
        attendance.check_out_location = location
        attendance.check_out_device = "mobile"
        
        # Calculate total hours if check-in time exists
        if attendance.actual_check_in:
            duration = now - attendance.actual_check_in
            attendance.total_hours = duration.total_seconds() / 3600
        
        db.commit()
        
        logger.info(f"Student {current_user.email} checked out from class {class_id}")
        
        return {
            "message": "Check-out successful",
            "check_out_time": now,
            "total_hours": attendance.total_hours
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during student check-out: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check out"
        )


# Attendance Analytics
@router.get("/analytics", response_model=dict)
async def get_attendance_analytics(
    class_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get attendance analytics and trends"""
    
    try:
        # Set default date range if not provided
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # Build base query
        query = db.query(AttendanceRecord).options(
            joinedload(AttendanceRecord.student).joinedload(Student.user),
            joinedload(AttendanceRecord.class_info)
        )
        
        # Apply filters
        if class_id:
            query = query.filter(AttendanceRecord.class_id == class_id)
        if student_id:
            query = query.filter(AttendanceRecord.student_id == student_id)
        
        query = query.filter(
            and_(
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date
            )
        )
        
        records = query.all()
        
        # Calculate analytics
        total_days = len(set(r.date for r in records))
        total_records = len(records)
        
        # Status breakdown
        status_counts = {}
        for record in records:
            status = record.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Daily trends
        daily_stats = {}
        for record in records:
            date_str = record.date.isoformat()
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    "date": record.date,
                    "total": 0,
                    "present": 0,
                    "absent": 0,
                    "late": 0,
                    "excused": 0
                }
            
            daily_stats[date_str]["total"] += 1
            if record.status == 'present':
                daily_stats[date_str]["present"] += 1
            elif record.status == 'absent':
                daily_stats[date_str]["absent"] += 1
            elif record.status == 'late':
                daily_stats[date_str]["late"] += 1
            elif record.status == 'excused':
                daily_stats[date_str]["excused"] += 1
        
        # Calculate percentages for each day
        for day_stats in daily_stats.values():
            if day_stats["total"] > 0:
                day_stats["attendance_percentage"] = round(
                    (day_stats["present"] / day_stats["total"]) * 100, 2
                )
        
        # Overall statistics
        overall_present = status_counts.get('present', 0)
        overall_attendance_percentage = (overall_present / total_records * 100) if total_records > 0 else 0
        
        return {
            "summary": {
                "total_days": total_days,
                "total_records": total_records,
                "overall_attendance_percentage": round(overall_attendance_percentage, 2),
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            "status_breakdown": status_counts,
            "daily_trends": list(daily_stats.values()),
            "top_absent_students": [],  # TODO: Implement
            "improvement_suggestions": []  # TODO: Implement
        }
        
    except Exception as e:
        logger.error(f"Error generating attendance analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate attendance analytics"
        )

@router.get("/reports", response_model=dict)
async def get_attendance_reports(
    class_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    include_details: bool = Query(False),
    group_by: str = Query("student"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get attendance reports via GET request"""
    
    try:
        # Set default date range if not provided
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = date.today()
        
        # Build base query
        query = db.query(AttendanceRecord).options(
            joinedload(AttendanceRecord.student).joinedload(Student.user),
            joinedload(AttendanceRecord.class_info)
        )
        
        # Apply filters
        if class_id:
            query = query.filter(AttendanceRecord.class_id == class_id)
        if student_id:
            query = query.filter(AttendanceRecord.student_id == student_id)
        
        query = query.filter(
            and_(
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date
            )
        )
        
        records = query.order_by(AttendanceRecord.date.desc()).all()
        
        # Calculate statistics
        total_records = len(records)
        present_count = len([r for r in records if r.status == 'present'])
        absent_count = len([r for r in records if r.status == 'absent'])
        late_count = len([r for r in records if r.status == 'late'])
        excused_count = len([r for r in records if r.status == 'excused'])
        
        attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
        
        # Group by student if requested
        student_stats = {}
        if group_by == "student":
            for record in records:
                student_id = record.student_id
                if student_id not in student_stats:
                    student_stats[student_id] = {
                        "student_id": student_id,
                        "student_name": f"{record.student.user.first_name} {record.student.user.last_name}",
                        "class_name": record.class_info.name,
                        "total_days": 0,
                        "present_days": 0,
                        "absent_days": 0,
                        "late_days": 0,
                        "excused_days": 0,
                        "attendance_percentage": 0,
                        "details": [] if include_details else None
                    }
                
                student_stats[student_id]["total_days"] += 1
                if record.status == 'present':
                    student_stats[student_id]["present_days"] += 1
                elif record.status == 'absent':
                    student_stats[student_id]["absent_days"] += 1
                elif record.status == 'late':
                    student_stats[student_id]["late_days"] += 1
                elif record.status == 'excused':
                    student_stats[student_id]["excused_days"] += 1
                
                if include_details:
                    student_stats[student_id]["details"].append({
                        "date": record.date,
                        "status": record.status,
                        "check_in_time": record.actual_check_in,
                        "check_out_time": record.actual_check_out,
                        "reason": record.reason
                    })
            
            # Calculate percentages
            for stats in student_stats.values():
                if stats["total_days"] > 0:
                    stats["attendance_percentage"] = round(
                        (stats["present_days"] / stats["total_days"]) * 100, 2
                    )
        
        return {
            "report_summary": {
                "total_records": total_records,
                "present_count": present_count,
                "absent_count": absent_count,
                "late_count": late_count,
                "excused_count": excused_count,
                "overall_attendance_percentage": round(attendance_percentage, 2),
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            "student_statistics": list(student_stats.values()) if group_by == "student" else None,
            "detailed_records": [
                {
                    "id": record.id,
                    "student_id": record.student_id,
                    "student_name": f"{record.student.user.first_name} {record.student.user.last_name}",
                    "class_id": record.class_id,
                    "class_name": record.class_info.name,
                    "date": record.date,
                    "status": record.status,
                    "check_in_time": record.actual_check_in,
                    "check_out_time": record.actual_check_out,
                    "reason": record.reason,
                    "notes": record.notes
                }
                for record in records
            ] if include_details else None
        }
        
    except Exception as e:
        logger.error(f"Error generating attendance report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate attendance report"
        )
