"""Communication API endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.communication import Notification
from app.schemas.communication import NotificationCreate, NotificationResponse, NotificationList, UnreadCountResponse
from app.services.notification import NotificationService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(
    unread_only: bool = Query(False, description="Return only unread notifications"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of notifications"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user notifications"""
    try:
        notification_service = NotificationService(db)
        notifications = notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )
        
        # Filter by type if specified
        if notification_type:
            notifications = [n for n in notifications if n.notification_type == notification_type]
        
        return notifications
    except Exception as e:
        logger.error(f"Get user notifications error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )

@router.get("/notifications/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unread notifications count"""
    try:
        logger.info(f"Getting unread count for user {current_user.id}")
        
        # Check if user exists and has valid ID
        if not current_user or not current_user.id:
            logger.error("Invalid user or user ID")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user"
            )
        
        # Get total notifications for user first
        total_notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).count()
        logger.info(f"Total notifications for user {current_user.id}: {total_notifications}")
        
        # Get unread count
        unread_count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        logger.info(f"Unread notifications for user {current_user.id}: {unread_count}")
        
        result = {"count": unread_count}
        logger.info(f"Unread count result: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get unread count error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )

@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific notification"""
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get notification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification"
        )

@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""
    try:
        notification_service = NotificationService(db)
        success = notification_service.mark_notification_read(notification_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark notification as read error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )

@router.put("/notifications/read-all")
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all user notifications as read"""
    try:
        # Update all unread notifications for the user
        result = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).update({
            Notification.is_read: True,
            Notification.read_at: datetime.utcnow()
        })
        
        db.commit()
        
        return {"message": f"Marked {result} notifications as read"}
    except Exception as e:
        logger.error(f"Mark all notifications as read error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )

@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete notification"""
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        db.delete(notification)
        db.commit()
        
        return {"message": "Notification deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete notification error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )

@router.post("/notifications", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create notification (admin only)"""
    # Check if user has permission to create notifications
    if current_user.role not in ['super_admin', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        notification_service = NotificationService(db)
        notification = await notification_service.send_notification(
            user_id=notification_data.user_id,
            title=notification_data.title,
            message=notification_data.message,
            notification_type=notification_data.notification_type,
            channels=notification_data.channels or ["web"],
            action_url=notification_data.action_url,
            action_text=notification_data.action_text,
            data=notification_data.data
        )
        
        return notification
    except Exception as e:
        logger.error(f"Create notification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )

@router.post("/notifications/bulk")
async def send_bulk_notifications(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send notifications to multiple users (admin only)"""
    # Check if user has permission
    if current_user.role not in ['super_admin', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        notification_service = NotificationService(db)
        success_count = 0
        failed_count = 0
        
        for user_id in data.get('user_ids', []):
            try:
                await notification_service.send_notification(
                    user_id=user_id,
                    title=data['title'],
                    message=data['message'],
                    notification_type=data['notification_type'],
                    channels=data.get('channels', ['web']),
                    action_url=data.get('action_url'),
                    action_text=data.get('action_text'),
                    data=data.get('data')
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {str(e)}")
                failed_count += 1
        
        return {
            "success_count": success_count,
            "failed_count": failed_count
        }
    except Exception as e:
        logger.error(f"Bulk notification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send bulk notifications"
        )
