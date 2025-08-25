"""
Event management API endpoints
"""

from typing import Any, List, Optional
from datetime import date, datetime, time
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from app.database.session import get_db
from app.api.deps import get_current_user
from app.core.permissions import UserRole
from app.core.role_config import role_config
from app.models.user import User
from app.models.student import Student
from app.models.academic import Class, ClassSubject
from app.models.events import Event, EventAssignment
from app.services.notification import NotificationService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic schemas
from pydantic import BaseModel

class EventCreateRequest(BaseModel):
    """Schema for creating a new event"""
    title: str
    description: Optional[str] = None
    event_type: Optional[str] = "General"  # Default event type if not provided
    date: Optional[date] = None  # Will be extracted from start datetime
    start_time: Optional[time] = None  # Will be extracted from start datetime
    end_time: Optional[time] = None  # Will be extracted from end datetime
    location: Optional[str] = None
    target_type: Optional[str] = None  # Will be mapped from audience
    target_class_id: Optional[int] = None
    
    # Frontend fields
    start: Optional[str] = None  # Frontend sends "2025-05-20T02:22"
    end: Optional[str] = None    # Frontend sends "2025-05-20T14:22"
    audience: Optional[str] = None  # Frontend sends "all", "teachers", "class"

class EventUpdateRequest(BaseModel):
    """Schema for updating an event"""
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    target_type: Optional[str] = None
    target_class_id: Optional[int] = None
    status: Optional[str] = None

class EventResponse(BaseModel):
    """Schema for event response"""
    id: int
    title: str
    description: Optional[str]
    event_type: str
    date: str
    start_time: Optional[str]
    end_time: Optional[str]
    location: Optional[str]
    target_type: str
    target_class_id: Optional[int]
    status: str
    created_by: int
    created_at: str
    updated_at: str
    creator_name: Optional[str] = None
    target_class_name: Optional[str] = None

# Helper function to check if teacher can create events for a class
def can_teacher_create_for_class(db: Session, teacher_id: int, class_id: int) -> bool:
    """Check if teacher can create events for a specific class"""
    # Check if teacher is the class teacher
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if class_obj and class_obj.class_teacher_id == teacher_id:
        return True
    
    # Check if teacher teaches subjects in this class
    subject_assignments = db.query(ClassSubject).filter(
        ClassSubject.class_id == class_id,
        ClassSubject.teacher_id == teacher_id
    ).first()
    
    return subject_assignments is not None

# Helper function to get target audience for notifications
def get_target_audience(db: Session, event: Event) -> List[int]:
    """Get list of user IDs to notify based on event target"""
    user_ids = []
    logger.info(f"Getting target audience for event: target_type={event.target_type}, target_class_id={event.target_class_id}")
    
    if event.target_type == "school_wide":
        # All students, teachers, parents
        students = db.query(Student).filter(Student.is_active == True).all()
        teachers = db.query(User).filter(User.role == UserRole.TEACHER).all()
        
        # Add student user IDs
        for student in students:
            user_ids.append(student.user_id)
        
        # Add teacher user IDs
        for teacher in teachers:
            user_ids.append(teacher.id)
            
        # Add parent user IDs (parents of students)
        for student in students:
            # Get parents of this student
            from app.models.user import Parent
            parents = db.query(Parent).join(Parent.children).filter(Student.id == student.id).all()
            for parent in parents:
                user_ids.append(parent.user_id)
    
    elif event.target_type == "teachers":
        # All teachers only
        teachers = db.query(User).filter(User.role == UserRole.TEACHER).all()
        for teacher in teachers:
            user_ids.append(teacher.id)
    
    elif event.target_type == "class_specific" and event.target_class_id:
        # Students in specific class + their parents + class teacher
        students = db.query(Student).filter(
            Student.current_class_id == event.target_class_id,
            Student.is_active == True
        ).all()
        
        # Add student user IDs
        for student in students:
            user_ids.append(student.user_id)
        
        # Add class teacher
        class_obj = db.query(Class).filter(Class.id == event.target_class_id).first()
        if class_obj and class_obj.class_teacher_id:
            user_ids.append(class_obj.class_teacher_id)
        
        # Add parents of students in this class
        for student in students:
            from app.models.user import Parent
            parents = db.query(Parent).join(Parent.children).filter(Student.id == student.id).all()
            for parent in parents:
                user_ids.append(parent.user_id)
    
    unique_user_ids = list(set(user_ids))  # Remove duplicates
    logger.info(f"Target audience calculated: {len(unique_user_ids)} unique users")
    logger.info(f"User IDs: {unique_user_ids}")
    return unique_user_ids

@router.post("/", response_model=EventResponse)
async def create_event(
    event_data: EventCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new event"""
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can create events"
        )
    
    # Process frontend data format
    # Map audience to target_type
    if event_data.audience:
        if event_data.audience == "all":
            target_type = "school_wide"
        elif event_data.audience == "teachers":
            target_type = "teachers"
        elif event_data.audience == "class":
            target_type = "class_specific"
        else:
            target_type = "school_wide"  # Default
    else:
        target_type = event_data.target_type or "school_wide"
    
    # Extract date and time from start/end datetime strings
    event_date = event_data.date
    start_time = event_data.start_time
    end_time = event_data.end_time
    
    if event_data.start:
        try:
            # Parse start datetime (e.g., "2025-05-20T02:22")
            start_datetime = datetime.fromisoformat(event_data.start.replace('Z', '+00:00'))
            event_date = start_datetime.date()
            start_time = start_datetime.time()
        except Exception as e:
            logger.error(f"Failed to parse start datetime: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start datetime format"
            )
    
    if event_data.end:
        try:
            # Parse end datetime (e.g., "2025-05-20T14:22")
            end_datetime = datetime.fromisoformat(event_data.end.replace('Z', '+00:00'))
            end_time = end_datetime.time()
        except Exception as e:
            logger.error(f"Failed to parse end datetime: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end datetime format"
            )
    
    # Validate target class if specified
    if target_type == "class_specific":
        if not event_data.target_class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="target_class_id is required for class_specific events"
            )
        
        # Check if class exists
        class_obj = db.query(Class).filter(Class.id == event_data.target_class_id).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target class not found"
            )
        
        # If teacher, check if they can create events for this class
        if current_user.role == UserRole.TEACHER:
            if not can_teacher_create_for_class(db, current_user.id, event_data.target_class_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create events for classes you teach"
                )
    
    # Create event
    event = Event(
        title=event_data.title,
        description=event_data.description,
        event_type=event_data.event_type or "General",
        date=event_date,
        start_time=start_time,
        end_time=end_time,
        location=event_data.location,
        target_type=target_type,
        target_class_id=event_data.target_class_id,
        created_by=current_user.id
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # Create event assignments for students
    if event.target_type in ["school_wide", "class_specific"]:
        students_query = db.query(Student).filter(Student.is_active == True)
        
        if event.target_type == "class_specific":
            students_query = students_query.filter(Student.current_class_id == event.target_class_id)
        
        students = students_query.all()
        
        for student in students:
            assignment = EventAssignment(
                event_id=event.id,
                student_id=student.id
            )
            db.add(assignment)
        
        db.commit()
    
    # Send notifications
    try:
        notification_service = NotificationService(db)
        target_user_ids = get_target_audience(db, event)
        
        logger.info(f"Sending notifications for event '{event.title}' to {len(target_user_ids)} users")
        logger.info(f"Target user IDs: {target_user_ids}")
        
        for user_id in target_user_ids:
            try:
                logger.info(f"Sending create notification to user {user_id}")
                notification = await notification_service.send_notification(
                    user_id=user_id,
                    title=f"New Event: {event.title}",
                    message=f"A new event '{event.title}' has been scheduled for {event.date}",
                    notification_type="info",
                    action_url=f"/events/{event.id}",
                    data={"event_id": event.id}
                )
                logger.info(f"Create notification sent successfully to user {user_id}, notification ID: {notification.id}")
            except Exception as user_error:
                logger.error(f"Failed to send create notification to user {user_id}: {user_error}")
                import traceback
                logger.error(f"User notification error traceback: {traceback.format_exc()}")
    except Exception as e:
        logger.error(f"Failed to send event notifications: {e}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Get creator name and target class name
    creator_name = f"{current_user.first_name} {current_user.last_name}"
    target_class_name = None
    if event.target_class_id:
        class_obj = db.query(Class).filter(Class.id == event.target_class_id).first()
        if class_obj:
            target_class_name = f"{class_obj.name} {class_obj.section}"
    
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "event_type": event.event_type,
        "date": event.date.isoformat() if event.date else None,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "location": event.location,
        "target_type": event.target_type,
        "target_class_id": event.target_class_id,
        "status": event.status,
        "created_by": event.created_by,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "updated_at": event.updated_at.isoformat() if event.updated_at else None,
        "creator_name": creator_name,
        "target_class_name": target_class_name
    }

@router.get("/", response_model=List[EventResponse])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    target_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List events based on user role"""
    
    # Build query based on user role
    query = db.query(Event).options(
        joinedload(Event.creator),
        joinedload(Event.target_class)
    )
    
    # Apply filters
    if target_type:
        query = query.filter(Event.target_type == target_type)
    if status:
        query = query.filter(Event.status == status)
    
    # Role-based filtering
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        # Admins see all events
        pass
    elif current_user.role == UserRole.TEACHER:
        # Teachers see school-wide events + events for their classes
        teacher_classes = db.query(Class).filter(
            or_(
                Class.class_teacher_id == current_user.id,
                Class.id.in_(
                    db.query(Class.id).join(ClassSubject).filter(ClassSubject.teacher_id == current_user.id)
                )
            )
        ).all()
        
        class_ids = [cls.id for cls in teacher_classes]
        query = query.filter(
            or_(
                Event.target_type == "school_wide",
                Event.target_type == "teachers",
                and_(Event.target_type == "class_specific", Event.target_class_id.in_(class_ids))
            )
        )
    elif current_user.role == UserRole.STUDENT:
        # Students see school-wide events + events for their class
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student and student.current_class_id:
            query = query.filter(
                or_(
                    Event.target_type == "school_wide",
                    and_(Event.target_type == "class_specific", Event.target_class_id == student.current_class_id)
                )
            )
        else:
            # Student without class only sees school-wide events
            query = query.filter(Event.target_type == "school_wide")
    elif current_user.role == UserRole.PARENT:
        # Parents see events for their children
        from app.models.user import Parent
        parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
        if parent and parent.children:
            child_class_ids = [child.current_class_id for child in parent.children if child.current_class_id]
            query = query.filter(
                or_(
                    Event.target_type == "school_wide",
                    and_(Event.target_type == "class_specific", Event.target_class_id.in_(child_class_ids))
                )
            )
        else:
            # Parent without children only sees school-wide events
            query = query.filter(Event.target_type == "school_wide")
    
    # Apply pagination and ordering
    events = query.order_by(Event.date.desc(), Event.created_at.desc()).offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for event in events:
        creator_name = f"{event.creator.first_name} {event.creator.last_name}" if event.creator else None
        target_class_name = f"{event.target_class.name} {event.target_class.section}" if event.target_class else None
        
        result.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type,
            "date": event.date.isoformat() if event.date else None,
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "location": event.location,
            "target_type": event.target_type,
            "target_class_id": event.target_class_id,
            "status": event.status,
            "created_by": event.created_by,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "updated_at": event.updated_at.isoformat() if event.updated_at else None,
            "creator_name": creator_name,
            "target_class_name": target_class_name
        })
    
    return result

@router.get("/my-events", response_model=List[EventResponse])
async def get_my_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get events assigned to current student"""
    
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only"
        )
    
    # Get student's events through assignments
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    events = db.query(Event).join(EventAssignment).filter(
        EventAssignment.student_id == student.id
    ).options(
        joinedload(Event.creator),
        joinedload(Event.target_class)
    ).order_by(Event.date.desc()).all()
    
    result = []
    for event in events:
        creator_name = f"{event.creator.first_name} {event.creator.last_name}" if event.creator else None
        target_class_name = f"{event.target_class.name} {event.target_class.section}" if event.target_class else None
        
        result.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type,
            "date": event.date.isoformat() if event.date else None,
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "location": event.location,
            "target_type": event.target_type,
            "target_class_id": event.target_class_id,
            "status": event.status,
            "created_by": event.created_by,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "updated_at": event.updated_at.isoformat() if event.updated_at else None,
            "creator_name": creator_name,
            "target_class_name": target_class_name
        })
    
    return result

@router.get("/child-events", response_model=List[EventResponse])
async def get_child_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get events for parent's children"""
    
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for parents only"
        )
    
    from app.models.parent import Parent
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    if not parent or not parent.children:
        return []
    
    # Get events for all children
    child_ids = [child.id for child in parent.children]
    events = db.query(Event).join(EventAssignment).filter(
        EventAssignment.student_id.in_(child_ids)
    ).options(
        joinedload(Event.creator),
        joinedload(Event.target_class)
    ).order_by(Event.date.desc()).all()
    
    result = []
    for event in events:
        creator_name = f"{event.creator.first_name} {event.creator.last_name}" if event.creator else None
        target_class_name = f"{event.target_class.name} {event.target_class.section}" if event.target_class else None
        
        result.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type,
            "date": event.date.isoformat() if event.date else None,
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "location": event.location,
            "target_type": event.target_type,
            "target_class_id": event.target_class_id,
            "status": event.status,
            "created_by": event.created_by,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "updated_at": event.updated_at.isoformat() if event.updated_at else None,
            "creator_name": creator_name,
            "target_class_name": target_class_name
        })
    
    return result

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get specific event details"""
    
    event = db.query(Event).options(
        joinedload(Event.creator),
        joinedload(Event.target_class)
    ).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if user has access to this event
    has_access = False
    
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        has_access = True
    elif current_user.role == UserRole.TEACHER:
        if event.target_type in ["school_wide", "teachers"]:
            has_access = True
        elif event.target_type == "class_specific" and event.target_class_id:
            has_access = can_teacher_create_for_class(db, current_user.id, event.target_class_id)
    elif current_user.role == UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student:
            if event.target_type == "school_wide":
                has_access = True
            elif event.target_type == "class_specific" and event.target_class_id:
                has_access = student.current_class_id == event.target_class_id
    elif current_user.role == UserRole.PARENT:
        from app.models.user import Parent
        parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
        if parent and parent.children:
            child_class_ids = [child.current_class_id for child in parent.children if child.current_class_id]
            if event.target_type == "school_wide":
                has_access = True
            elif event.target_type == "class_specific" and event.target_class_id:
                has_access = event.target_class_id in child_class_ids
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    creator_name = f"{event.creator.first_name} {event.creator.last_name}" if event.creator else None
    target_class_name = f"{event.target_class.name} {event.target_class.section}" if event.target_class else None
    
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "event_type": event.event_type,
        "date": event.date.isoformat() if event.date else None,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "location": event.location,
        "target_type": event.target_type,
        "target_class_id": event.target_class_id,
        "status": event.status,
        "created_by": event.created_by,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "updated_at": event.updated_at.isoformat() if event.updated_at else None,
        "creator_name": creator_name,
        "target_class_name": target_class_name
    }

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update an event"""
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if user can update this event
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if current_user.role == UserRole.TEACHER:
            if event.created_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update events you created"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update events"
            )
    
    # Update event fields
    update_data = event_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    event.updated_at = datetime.now()
    db.commit()
    db.refresh(event)
    
    # Send update notifications
    try:
        logger.info(f"Starting update notifications for event: {event.title}")
        logger.info("Creating notification service...")
        notification_service = NotificationService(db)
        logger.info("Notification service created successfully")
        target_user_ids = get_target_audience(db, event)
        
        logger.info(f"About to send update notifications to {len(target_user_ids)} users")
        logger.info(f"Target user IDs for update: {target_user_ids}")
        
        logger.info(f"Sending update notifications to {len(target_user_ids)} users")
        
        for user_id in target_user_ids:
            try:
                logger.info(f"Sending update notification to user {user_id}")
                notification = await notification_service.send_notification(
                    user_id=user_id,
                    title=f"Event Updated: {event.title}",
                    message=f"The event '{event.title}' has been updated",
                    notification_type="info",
                    action_url=f"/events/{event.id}",
                    data={"event_id": event.id}
                )
                logger.info(f"Update notification sent successfully to user {user_id}, notification ID: {notification.id}")
            except Exception as user_error:
                logger.error(f"Failed to send update notification to user {user_id}: {user_error}")
                import traceback
                logger.error(f"User notification error traceback: {traceback.format_exc()}")
    except Exception as e:
        logger.error(f"Failed to send event update notifications: {e}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Update notification traceback: {traceback.format_exc()}")
    
    # Get creator name and target class name
    creator_name = f"{current_user.first_name} {current_user.last_name}"
    target_class_name = None
    if event.target_class_id:
        class_obj = db.query(Class).filter(Class.id == event.target_class_id).first()
        if class_obj:
            target_class_name = f"{class_obj.name} {class_obj.section}"
    
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "event_type": event.event_type,
        "date": event.date.isoformat() if event.date else None,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "location": event.location,
        "target_type": event.target_type,
        "target_class_id": event.target_class_id,
        "status": event.status,
        "created_by": event.created_by,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "updated_at": event.updated_at.isoformat() if event.updated_at else None,
        "creator_name": creator_name,
        "target_class_name": target_class_name
    }

@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete an event"""
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if user can delete this event
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if current_user.role == UserRole.TEACHER:
            if event.created_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete events you created"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete events"
            )
    
    # Store event info before deletion for notifications
    event_title = event.title
    event_target_type = event.target_type
    event_target_class_id = event.target_class_id
    
    # Delete event assignments first
    db.query(EventAssignment).filter(EventAssignment.event_id == event_id).delete()
    
    # Delete event
    db.delete(event)
    db.commit()
    
    # Send delete notifications
    try:
        logger.info(f"Starting delete notifications for event: {event_title}")
        notification_service = NotificationService(db)
        

        
        # Create a temporary event object for notification targeting
        temp_event = type('Event', (), {
            'target_type': event_target_type,
            'target_class_id': event_target_class_id
        })()
        target_user_ids = get_target_audience(db, temp_event)
        
        logger.info(f"Sending delete notifications to {len(target_user_ids)} users")
        
        for user_id in target_user_ids:
            try:
                logger.info(f"Sending delete notification to user {user_id}")
                notification = await notification_service.send_notification(
                    user_id=user_id,
                    title=f"Event Cancelled: {event_title}",
                    message=f"The event '{event_title}' has been cancelled",
                    notification_type="warning",
                    action_url="/events",
                    data={"event_id": event_id}
                )
                logger.info(f"Delete notification sent successfully to user {user_id}, notification ID: {notification.id}")
            except Exception as user_error:
                logger.error(f"Failed to send delete notification to user {user_id}: {user_error}")
                import traceback
                logger.error(f"User notification error traceback: {traceback.format_exc()}")
    except Exception as e:
        logger.error(f"Failed to send event delete notifications: {e}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Delete notification traceback: {traceback.format_exc()}")
    
    return {"message": "Event deleted successfully"}
