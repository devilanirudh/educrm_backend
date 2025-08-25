"""live_classes API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Dict, Any
from app.api import deps
from app.models.live_class import LiveClass, LiveClassStatus
from app.schemas.live_class import LiveClassCreate, LiveClass as LiveClassSchema, ClassAttendance
from app.models.user import User
from app.core.permissions import UserRole
from app.models.teacher import Teacher, teacher_class_associations
from app.core.role_config import role_config
from app.services.jitsi import jitsi_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=LiveClassSchema, status_code=status.HTTP_201_CREATED)
def schedule_live_class(
    *,
    db: Session = Depends(deps.get_db),
    live_class_in: LiveClassCreate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Schedule a new live class with Jitsi Meet integration.
    """
    if not role_config.can_access_module(current_user.role.value, "live_classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access live classes",
        )

    try:
        # Create Jitsi meeting room
        room_name = f"class-{live_class_in.class_id}-{live_class_in.topic.replace(' ', '-').lower()}"
        teacher_name = f"{current_user.first_name} {current_user.last_name}"
        
        # Get class name for the meeting
        from app.models.academic import Class
        class_info = db.query(Class).filter(Class.id == live_class_in.class_id).first()
        class_name = class_info.full_name if class_info else f"Class {live_class_in.class_id}"
        
        jitsi_config = jitsi_service.create_meeting_room(
            room_name=room_name,
            teacher_name=teacher_name,
            class_name=class_name
        )
        
        # Create live class with Jitsi integration
        live_class_data = live_class_in.dict()

        # Determine assigned teacher id: if admin/super_admin scheduled, try class teacher; else current user
        assigned_teacher_user_id = current_user.id
        if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            try:
                teacher = (
                    db.query(Teacher)
                    .join(teacher_class_associations, Teacher.id == teacher_class_associations.c.teacher_id)
                    .filter(teacher_class_associations.c.class_id == live_class_in.class_id)
                    .order_by(teacher_class_associations.c.is_class_teacher.desc())
                    .first()
                )
                if teacher and teacher.user_id:
                    assigned_teacher_user_id = teacher.user_id
            except Exception:
                assigned_teacher_user_id = current_user.id

        live_class_data.update({
            "teacher_id": assigned_teacher_user_id,
            "jitsi_room_name": jitsi_config["room_name"],
            "jitsi_meeting_url": jitsi_config["meeting_url"],
            "jitsi_settings": jitsi_config["settings"],
            "status": LiveClassStatus.SCHEDULED
        })
        
        live_class = LiveClass(**live_class_data)
        db.add(live_class)
        db.commit()
        db.refresh(live_class)
        
        # Load relationships
        db.refresh(live_class)
        live_class = db.query(LiveClass).options(
            joinedload(LiveClass.teacher),
            joinedload(LiveClass.class_)
        ).filter(LiveClass.id == live_class.id).first()
        
        logger.info(f"Created live class with Jitsi room: {jitsi_config['room_name']}")
        
        # Convert to dict to avoid serialization issues
        return {
            "id": live_class.id,
            "topic": live_class.topic,
            "start_time": live_class.start_time,
            "duration": live_class.duration,
            "teacher_id": live_class.teacher_id,
            "class_id": live_class.class_id,
            "status": live_class.status,
            "recording_url": live_class.recording_url,
            "jitsi_room_name": live_class.jitsi_room_name,
            "jitsi_meeting_url": live_class.jitsi_meeting_url,
            "jitsi_meeting_id": live_class.jitsi_meeting_id,
            "jitsi_settings": live_class.jitsi_settings,
            "jitsi_token": live_class.jitsi_token,
            "description": live_class.description,
            "max_participants": live_class.max_participants,
            "is_password_protected": live_class.is_password_protected,
            "meeting_password": live_class.meeting_password,
            "allow_join_before_host": live_class.allow_join_before_host,
            "mute_upon_entry": live_class.mute_upon_entry,
            "video_off_upon_entry": live_class.video_off_upon_entry,
            "enable_chat": live_class.enable_chat,
            "enable_whiteboard": live_class.enable_whiteboard,
            "enable_screen_sharing": live_class.enable_screen_sharing,
            "enable_recording": live_class.enable_recording,
            "enable_breakout_rooms": live_class.enable_breakout_rooms,
            "enable_polls": live_class.enable_polls,
            "enable_reactions": live_class.enable_reactions,
            "teacher": {
                "id": live_class.teacher.id,
                "first_name": live_class.teacher.first_name,
                "last_name": live_class.teacher.last_name,
                "email": live_class.teacher.email
            } if live_class.teacher else None,
            "class_": {
                "id": live_class.class_.id,
                "name": live_class.class_.name,
                "section": live_class.class_.section
            } if live_class.class_ else None,
            "attendance": []
        }
        
    except Exception as e:
        logger.error(f"Error creating live class: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create live class"
        )

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
    if not role_config.can_access_module(current_user.role.value, "live_classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access live classes",
        )
    
    # Filter based on user role
    query = db.query(LiveClass).options(
        joinedload(LiveClass.teacher),
        joinedload(LiveClass.class_)
    )
    
    if current_user.role == UserRole.TEACHER:
        query = query.filter(LiveClass.teacher_id == current_user.id)
    elif current_user.role == UserRole.STUDENT:
        # Get classes where student is enrolled
        from app.models.student import Student
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student and student.current_class_id:
            query = query.filter(LiveClass.class_id == student.current_class_id)
    
    live_classes = query.offset(skip).limit(limit).all()
    
    # Convert to dict to avoid serialization issues
    result = []
    for live_class in live_classes:
        live_class_dict = {
            "id": live_class.id,
            "topic": live_class.topic,
            "start_time": live_class.start_time,
            "duration": live_class.duration,
            "teacher_id": live_class.teacher_id,
            "class_id": live_class.class_id,
            "status": live_class.status,
            "recording_url": live_class.recording_url,
            "jitsi_room_name": live_class.jitsi_room_name,
            "jitsi_meeting_url": live_class.jitsi_meeting_url,
            "jitsi_meeting_id": live_class.jitsi_meeting_id,
            "jitsi_settings": live_class.jitsi_settings,
            "jitsi_token": live_class.jitsi_token,
            "description": live_class.description,
            "max_participants": live_class.max_participants,
            "is_password_protected": live_class.is_password_protected,
            "meeting_password": live_class.meeting_password,
            "allow_join_before_host": live_class.allow_join_before_host,
            "mute_upon_entry": live_class.mute_upon_entry,
            "video_off_upon_entry": live_class.video_off_upon_entry,
            "enable_chat": live_class.enable_chat,
            "enable_whiteboard": live_class.enable_whiteboard,
            "enable_screen_sharing": live_class.enable_screen_sharing,
            "enable_recording": live_class.enable_recording,
            "enable_breakout_rooms": live_class.enable_breakout_rooms,
            "enable_polls": live_class.enable_polls,
            "enable_reactions": live_class.enable_reactions,
            "teacher": {
                "id": live_class.teacher.id,
                "first_name": live_class.teacher.first_name,
                "last_name": live_class.teacher.last_name,
                "email": live_class.teacher.email
            } if live_class.teacher else None,
            "class_": {
                "id": live_class.class_.id,
                "name": live_class.class_.name,
                "section": live_class.class_.section
            } if live_class.class_ else None,
            "attendance": []
        }
        result.append(live_class_dict)
    
    return result

@router.post("/{class_id}/join", response_model=Dict[str, Any])
def join_live_class(
    class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Join a live class with Jitsi Meet integration.
    """
    if not role_config.can_access_module(current_user.role.value, "live_classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to join live class.",
        )

    live_class = db.query(LiveClass).filter(LiveClass.id == class_id).first()
    if not live_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live class not found.",
        )

    try:
        # Check if class is active
        if live_class.status != LiveClassStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Live class is not currently active.",
            )

        # Join Jitsi meeting
        participant_name = f"{current_user.first_name} {current_user.last_name}"
        participant_role = "teacher" if current_user.role == UserRole.TEACHER else "student"
        
        jitsi_join_config = jitsi_service.join_meeting(
            room_name=live_class.jitsi_room_name,
            participant_name=participant_name,
            participant_role=participant_role
        )
        
        # Generate JWT token for authentication
        jitsi_token = jitsi_service.generate_meeting_token(
            room_name=live_class.jitsi_room_name,
            participant_name=participant_name,
            participant_role=participant_role
        )
        
        # Record attendance
        from app.models.live_class import ClassAttendance
        attendance = ClassAttendance(
            live_class_id=class_id,
            user_id=current_user.id,
            join_time=datetime.utcnow(),
            jitsi_participant_id=jitsi_join_config.get("participant_id"),
            jitsi_join_token=jitsi_token
        )
        db.add(attendance)
        db.commit()
        
        logger.info(f"User {participant_name} joined live class {class_id}")
        
        return {
            "success": True,
            "meeting_url": jitsi_join_config["meeting_url"],
            "jitsi_token": jitsi_token,
            "participant_name": participant_name,
            "participant_role": participant_role,
            "settings": jitsi_join_config["settings"],
            "attendance_id": attendance.id
        }
        
    except Exception as e:
        logger.error(f"Error joining live class: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join live class"
        )

@router.post("/{class_id}/start", response_model=LiveClassSchema)
def start_live_class(
    class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Start a live class (teacher only).
    """
    # Only teachers and admins can start live classes
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and administrators can start live classes.",
        )

    live_class = db.query(LiveClass).filter(LiveClass.id == class_id).first()
    if not live_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live class not found.",
        )

    # Allow admins to start any class, teachers only their own classes
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and live_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned teacher or administrators can start this live class.",
        )

    live_class.status = LiveClassStatus.IN_PROGRESS
    db.commit()
    db.refresh(live_class)
    
    # Load relationships
    live_class = db.query(LiveClass).options(
        joinedload(LiveClass.teacher),
        joinedload(LiveClass.class_)
    ).filter(LiveClass.id == live_class.id).first()
    
    logger.info(f"Live class {class_id} started by teacher {current_user.id}")
    
    # Convert to dict to avoid serialization issues
    return {
        "id": live_class.id,
        "topic": live_class.topic,
        "start_time": live_class.start_time,
        "duration": live_class.duration,
        "teacher_id": live_class.teacher_id,
        "class_id": live_class.class_id,
        "status": live_class.status,
        "recording_url": live_class.recording_url,
        "jitsi_room_name": live_class.jitsi_room_name,
        "jitsi_meeting_url": live_class.jitsi_meeting_url,
        "jitsi_meeting_id": live_class.jitsi_meeting_id,
        "jitsi_settings": live_class.jitsi_settings,
        "jitsi_token": live_class.jitsi_token,
        "description": live_class.description,
        "max_participants": live_class.max_participants,
        "is_password_protected": live_class.is_password_protected,
        "meeting_password": live_class.meeting_password,
        "allow_join_before_host": live_class.allow_join_before_host,
        "mute_upon_entry": live_class.mute_upon_entry,
        "video_off_upon_entry": live_class.video_off_upon_entry,
        "enable_chat": live_class.enable_chat,
        "enable_whiteboard": live_class.enable_whiteboard,
        "enable_screen_sharing": live_class.enable_screen_sharing,
        "enable_recording": live_class.enable_recording,
        "enable_breakout_rooms": live_class.enable_breakout_rooms,
        "enable_polls": live_class.enable_polls,
        "enable_reactions": live_class.enable_reactions,
        "teacher": {
            "id": live_class.teacher.id,
            "first_name": live_class.teacher.first_name,
            "last_name": live_class.teacher.last_name,
            "email": live_class.teacher.email
        } if live_class.teacher else None,
        "class_": {
            "id": live_class.class_.id,
            "name": live_class.class_.name,
            "section": live_class.class_.section
        } if live_class.class_ else None,
        "attendance": []
    }

@router.post("/{class_id}/end", response_model=LiveClassSchema)
def end_live_class(
    class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    End a live class (teacher only).
    """
    # Only teachers and admins can end live classes
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and administrators can end live classes.",
        )

    live_class = db.query(LiveClass).filter(LiveClass.id == class_id).first()
    if not live_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live class not found.",
        )

    # Allow admins to end any class, teachers only their own classes
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and live_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned teacher or administrators can end this live class.",
        )

    # End Jitsi meeting
    jitsi_service.end_meeting(live_class.jitsi_room_name)
    
    live_class.status = LiveClassStatus.COMPLETED
    db.commit()
    db.refresh(live_class)
    
    # Load relationships
    live_class = db.query(LiveClass).options(
        joinedload(LiveClass.teacher),
        joinedload(LiveClass.class_)
    ).filter(LiveClass.id == live_class.id).first()
    
    logger.info(f"Live class {class_id} ended by teacher {current_user.id}")
    
    # Convert to dict to avoid serialization issues
    return {
        "id": live_class.id,
        "topic": live_class.topic,
        "start_time": live_class.start_time,
        "duration": live_class.duration,
        "teacher_id": live_class.teacher_id,
        "class_id": live_class.class_id,
        "status": live_class.status,
        "recording_url": live_class.recording_url,
        "jitsi_room_name": live_class.jitsi_room_name,
        "jitsi_meeting_url": live_class.jitsi_meeting_url,
        "jitsi_meeting_id": live_class.jitsi_meeting_id,
        "jitsi_settings": live_class.jitsi_settings,
        "jitsi_token": live_class.jitsi_token,
        "description": live_class.description,
        "max_participants": live_class.max_participants,
        "is_password_protected": live_class.is_password_protected,
        "meeting_password": live_class.meeting_password,
        "allow_join_before_host": live_class.allow_join_before_host,
        "mute_upon_entry": live_class.mute_upon_entry,
        "video_off_upon_entry": live_class.video_off_upon_entry,
        "enable_chat": live_class.enable_chat,
        "enable_whiteboard": live_class.enable_whiteboard,
        "enable_screen_sharing": live_class.enable_screen_sharing,
        "enable_recording": live_class.enable_recording,
        "enable_breakout_rooms": live_class.enable_breakout_rooms,
        "enable_polls": live_class.enable_polls,
        "enable_reactions": live_class.enable_reactions,
        "teacher": {
            "id": live_class.teacher.id,
            "first_name": live_class.teacher.first_name,
            "last_name": live_class.teacher.last_name,
            "email": live_class.teacher.email
        } if live_class.teacher else None,
        "class_": {
            "id": live_class.class_.id,
            "name": live_class.class_.name,
            "section": live_class.class_.section
        } if live_class.class_ else None,
        "attendance": []
    }

@router.get("/{class_id}/attendance", response_model=list[ClassAttendance])
def get_live_class_attendance(
    class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get the attendance for a live class.
    """
    if not role_config.can_access_module(current_user.role.value, "live_classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view live class attendance",
        )

    attendance = (
        db.query(ClassAttendance)
        .options(joinedload(ClassAttendance.user))
        .filter(ClassAttendance.live_class_id == class_id)
        .all()
    )
    
    # Convert to dict to avoid serialization issues
    result = []
    for record in attendance:
        attendance_dict = {
            "id": record.id,
            "user_id": record.user_id,
            "live_class_id": record.live_class_id,
            "join_time": record.join_time,
            "leave_time": record.leave_time,
            "jitsi_participant_id": record.jitsi_participant_id,
            "jitsi_join_token": record.jitsi_join_token,
            "connection_quality": record.connection_quality,
            "device_info": record.device_info,
            "user": {
                "id": record.user.id,
                "first_name": record.user.first_name,
                "last_name": record.user.last_name,
                "email": record.user.email
            } if record.user else None
        }
        result.append(attendance_dict)
    
    return result

@router.post("/{class_id}/leave", response_model=ClassAttendance)
def leave_live_class(
    class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Leave a live class.
    """
    if not role_config.can_access_module(current_user.role.value, "live_classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to leave live class",
        )
    
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
    
    # Load user relationship
    attendance = db.query(ClassAttendance).options(
        joinedload(ClassAttendance.user)
    ).filter(ClassAttendance.id == attendance.id).first()
    
    logger.info(f"User {current_user.id} left live class {class_id}")
    
    # Convert to dict to avoid serialization issues
    return {
        "id": attendance.id,
        "user_id": attendance.user_id,
        "live_class_id": attendance.live_class_id,
        "join_time": attendance.join_time,
        "leave_time": attendance.leave_time,
        "jitsi_participant_id": attendance.jitsi_participant_id,
        "jitsi_join_token": attendance.jitsi_join_token,
        "connection_quality": attendance.connection_quality,
        "device_info": attendance.device_info,
        "user": {
            "id": attendance.user.id,
            "first_name": attendance.user.first_name,
            "last_name": attendance.user.last_name,
            "email": attendance.user.email
        } if attendance.user else None
    }

@router.get("/{class_id}/info", response_model=Dict[str, Any])
def get_live_class_info(
    class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get detailed information about a live class including Jitsi meeting info.
    """
    if not role_config.can_access_module(current_user.role, "live_classes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view live class information",
        )
    
    live_class = db.query(LiveClass).filter(LiveClass.id == class_id).first()
    if not live_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live class not found.",
        )

    # Get Jitsi meeting info
    jitsi_info = jitsi_service.get_meeting_info(live_class.jitsi_room_name)
    
    # Load relationships
    live_class = db.query(LiveClass).options(
        joinedload(LiveClass.teacher),
        joinedload(LiveClass.class_)
    ).filter(LiveClass.id == live_class.id).first()
    
    return {
        "live_class": {
            "id": live_class.id,
            "topic": live_class.topic,
            "start_time": live_class.start_time,
            "duration": live_class.duration,
            "teacher_id": live_class.teacher_id,
            "class_id": live_class.class_id,
            "status": live_class.status,
            "recording_url": live_class.recording_url,
            "jitsi_room_name": live_class.jitsi_room_name,
            "jitsi_meeting_url": live_class.jitsi_meeting_url,
            "jitsi_meeting_id": live_class.jitsi_meeting_id,
            "jitsi_settings": live_class.jitsi_settings,
            "jitsi_token": live_class.jitsi_token,
            "description": live_class.description,
            "max_participants": live_class.max_participants,
            "is_password_protected": live_class.is_password_protected,
            "meeting_password": live_class.meeting_password,
            "allow_join_before_host": live_class.allow_join_before_host,
            "mute_upon_entry": live_class.mute_upon_entry,
            "video_off_upon_entry": live_class.video_off_upon_entry,
            "enable_chat": live_class.enable_chat,
            "enable_whiteboard": live_class.enable_whiteboard,
            "enable_screen_sharing": live_class.enable_screen_sharing,
            "enable_recording": live_class.enable_recording,
            "enable_breakout_rooms": live_class.enable_breakout_rooms,
            "enable_polls": live_class.enable_polls,
            "enable_reactions": live_class.enable_reactions,
            "teacher": {
                "id": live_class.teacher.id,
                "first_name": live_class.teacher.first_name,
                "last_name": live_class.teacher.last_name,
                "email": live_class.teacher.email
            } if live_class.teacher else None,
            "class_": {
                "id": live_class.class_.id,
                "name": live_class.class_.name,
                "section": live_class.class_.section
            } if live_class.class_ else None
        },
        "jitsi_info": jitsi_info,
        "meeting_url": live_class.jitsi_meeting_url,
        "room_name": live_class.jitsi_room_name
    }
