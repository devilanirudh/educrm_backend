"""live_classes API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.models.live_class import LiveClass
from app.schemas.live_class import LiveClassCreate, LiveClass as LiveClassSchema, ClassAttendance
from app.models.user import User
from app.core.permissions import UserRole

router = APIRouter()

@router.post("/", response_model=LiveClassSchema, status_code=status.HTTP_201_CREATED)
def schedule_live_class(
    *,
    db: Session = Depends(deps.get_db),
    live_class_in: LiveClassCreate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Schedule a new live class.
    """
    if not current_user.role in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    live_class = LiveClass(**live_class_in.dict())
    db.add(live_class)
    db.commit()
    db.refresh(live_class)
    return live_class

@router.get("/", response_model=list[LiveClassSchema])
def get_live_classes(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Retrieve a list of live classes.
    """
    if not current_user.role in [UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT, UserRole.PARENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    live_classes = db.query(LiveClass).offset(skip).limit(limit).all()
    return live_classes

@router.post("/{class_id}/join", response_model=ClassAttendance)
def join_live_class(
    class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Join a live class.
    """
    if not current_user.role in [UserRole.STUDENT, UserRole.PARENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and parents can join a live class.",
        )

    live_class = db.query(LiveClass).filter(LiveClass.id == class_id).first()
    if not live_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live class not found.",
        )

    attendance = ClassAttendance(
        live_class_id=class_id,
        user_id=current_user.id,
        join_time=datetime.utcnow(),
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance

@router.get("/{class_id}/attendance", response_model=list[ClassAttendance])
def get_live_class_attendance(
    class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get the attendance for a live class.
    """
    if not current_user.role in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    attendance = (
        db.query(ClassAttendance)
        .filter(ClassAttendance.live_class_id == class_id)
        .all()
    )
    return attendance

@router.post("/{class_id}/leave", response_model=ClassAttendance)
def leave_live_class(
    class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Leave a live class.
    """
    attendance = (
        db.query(ClassAttendance)
        .filter(
            ClassAttendance.live_class_id == class_id,
            ClassAttendance.user_id == current_user.id,
        )
        .first()
    )

    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found.",
        )

    attendance.leave_time = datetime.utcnow()
    db.commit()
    db.refresh(attendance)
    return attendance
