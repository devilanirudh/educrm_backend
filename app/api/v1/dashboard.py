"""
Dashboard API endpoints for aggregated dashboard data
"""

from typing import Any, List, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.database.session import get_db
from app.api.deps import get_current_user
from app.core.permissions import UserRole
from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.academic import Class
from app.models.student import AttendanceRecord
from app.models.audit import AuditLog
from app.models.events import Event
from app.models.academic import Assignment
from app.models.communication import Notification
from app.models.financial import Invoice, PaymentStatus
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic schemas for dashboard responses
from pydantic import BaseModel
from typing import Optional

class KPIData(BaseModel):
    current: int
    previous: int
    change_percentage: float
    change_type: str  # "increase" or "decrease"

class ChartDataPoint(BaseModel):
    label: str
    value: int

class RecentActivity(BaseModel):
    id: int
    action: str
    details: str
    timestamp: str
    user_name: Optional[str] = None
    user_role: Optional[str] = None

class QuickStats(BaseModel):
    pending_assignments: int
    unread_notifications: int
    upcoming_events: int
    overdue_fees: int

class AdminDashboardResponse(BaseModel):
    kpis: Dict[str, KPIData]
    charts: Dict[str, List[ChartDataPoint]]
    recent_activities: List[RecentActivity]
    quick_stats: QuickStats

def calculate_percentage_change(current: int, previous: int) -> tuple[float, str]:
    """Calculate percentage change and determine change type"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0, "increase" if current > 0 else "no_change"
    
    change = ((current - previous) / previous) * 100
    change_type = "increase" if change > 0 else "decrease" if change < 0 else "no_change"
    return round(change, 1), change_type

def get_current_month_range() -> tuple[datetime, datetime]:
    """Get current month start and end dates"""
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        end_of_month = now.replace(year=now.year + 1, month=1, day=1) - timedelta(seconds=1)
    else:
        end_of_month = now.replace(month=now.month + 1, day=1) - timedelta(seconds=1)
    return start_of_month, end_of_month

def get_previous_month_range() -> tuple[datetime, datetime]:
    """Get previous month start and end dates"""
    now = datetime.now()
    if now.month == 1:
        start_of_prev_month = now.replace(year=now.year - 1, month=12, day=1)
    else:
        start_of_prev_month = now.replace(month=now.month - 1, day=1)
    
    end_of_prev_month = now.replace(day=1) - timedelta(seconds=1)
    return start_of_prev_month, end_of_prev_month

@router.get("/admin/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get comprehensive admin dashboard data"""
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access admin dashboard"
        )
    
    try:
        # Get date ranges for calculations
        current_start, current_end = get_current_month_range()
        previous_start, previous_end = get_previous_month_range()
        
        # 1. Calculate KPIs with trends
        kpis = {}
        
        # Total Students KPI
        current_students = db.query(Student).filter(Student.is_active == True).count()
        previous_students = db.query(Student).filter(
            and_(
                Student.is_active == True,
                Student.created_at < current_start
            )
        ).count()
        student_change, student_change_type = calculate_percentage_change(current_students, previous_students)
        
        kpis["total_students"] = KPIData(
            current=current_students,
            previous=previous_students,
            change_percentage=student_change,
            change_type=student_change_type
        )
        
        # Total Teachers KPI
        current_teachers = db.query(User).filter(User.role == UserRole.TEACHER).count()
        previous_teachers = db.query(User).filter(
            and_(
                User.role == UserRole.TEACHER,
                User.created_at < current_start
            )
        ).count()
        teacher_change, teacher_change_type = calculate_percentage_change(current_teachers, previous_teachers)
        
        kpis["total_teachers"] = KPIData(
            current=current_teachers,
            previous=previous_teachers,
            change_percentage=teacher_change,
            change_type=teacher_change_type
        )
        
        # Active Classes KPI
        current_classes = db.query(Class).filter(Class.is_active == True).count()
        previous_classes = db.query(Class).filter(
            and_(
                Class.is_active == True,
                Class.created_at < current_start
            )
        ).count()
        class_change, class_change_type = calculate_percentage_change(current_classes, previous_classes)
        
        kpis["active_classes"] = KPIData(
            current=current_classes,
            previous=previous_classes,
            change_percentage=class_change,
            change_type=class_change_type
        )
        
        # Attendance Rate KPI
        # Calculate current month attendance
        current_attendance_records = db.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.date >= current_start.date(),
                AttendanceRecord.date <= current_end.date()
            )
        ).all()
        
        current_total_days = len(current_attendance_records)
        current_present_days = sum(1 for record in current_attendance_records if record.status == "present")
        current_attendance_rate = (current_present_days / current_total_days * 100) if current_total_days > 0 else 0
        
        # Calculate previous month attendance
        previous_attendance_records = db.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.date >= previous_start.date(),
                AttendanceRecord.date <= previous_end.date()
            )
        ).all()
        
        previous_total_days = len(previous_attendance_records)
        previous_present_days = sum(1 for record in previous_attendance_records if record.status == "present")
        previous_attendance_rate = (previous_present_days / previous_total_days * 100) if previous_total_days > 0 else 0
        
        attendance_change, attendance_change_type = calculate_percentage_change(
            round(current_attendance_rate, 1), 
            round(previous_attendance_rate, 1)
        )
        
        kpis["attendance_rate"] = KPIData(
            current=round(current_attendance_rate, 1),
            previous=round(previous_attendance_rate, 1),
            change_percentage=attendance_change,
            change_type=attendance_change_type
        )
        
        # 2. Generate Chart Data
        charts = {}
        
        # Students by Class Chart
        students_by_class = db.query(
            Class.name,
            Class.section,
            func.count(Student.id).label('student_count')
        ).outerjoin(Student, Class.id == Student.current_class_id).filter(
            Class.is_active == True
        ).group_by(Class.id, Class.name, Class.section).all()
        
        charts["students_by_class"] = [
            ChartDataPoint(
                label=f"{class_data.name} {class_data.section}",
                value=class_data.student_count
            ) for class_data in students_by_class
        ]
        
        # Attendance Trend Chart (last 7 days)
        attendance_trend = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).date()
            day_records = db.query(AttendanceRecord).filter(AttendanceRecord.date == date).all()
            total_days = len(day_records)
            present_days = sum(1 for record in day_records if record.status == "present")
            rate = (present_days / total_days * 100) if total_days > 0 else 0
            
            attendance_trend.append(ChartDataPoint(
                label=date.strftime("%m/%d"),
                value=round(rate, 1)
            ))
        
        charts["attendance_trend"] = list(reversed(attendance_trend))  # Oldest to newest
        

        
        # 4. Calculate Quick Stats
        # Unread notifications
        unread_notifications = db.query(Notification).filter(
            Notification.is_read == False
        ).count()
        
        # Upcoming events (next 7 days)
        upcoming_events = db.query(Event).filter(
            and_(
                Event.date >= datetime.now().date(),
                Event.date <= (datetime.now() + timedelta(days=7)).date()
            )
        ).count()
        
        # Overdue fees
        overdue_fees = db.query(Invoice).filter(
            and_(
                Invoice.due_date < datetime.now().date(),
                Invoice.status == PaymentStatus.PENDING
            )
        ).count()
        
        quick_stats = QuickStats(
            pending_assignments=0,  # Removed pending assignments
            unread_notifications=unread_notifications,
            upcoming_events=upcoming_events,
            overdue_fees=overdue_fees
        )
        
        return AdminDashboardResponse(
            kpis=kpis,
            charts=charts,
            recent_activities=[],  # Removed recent activities
            quick_stats=quick_stats
        )
        
    except Exception as e:
        logger.error(f"Error generating admin dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dashboard data"
        )
