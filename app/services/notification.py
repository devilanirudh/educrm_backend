"""
Notification service for email, SMS, and push notifications
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.communication import Notification, EmailTemplate, SMSTemplate
from app.models.user import User
from app.core.config import settings
import logging
import asyncio
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class NotificationService:
    """Notification service for multi-channel communications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        channels: List[str] = None,
        action_url: str = None,
        action_text: str = None,
        data: Dict[str, Any] = None,
        scheduled_at: datetime = None
    ) -> Notification:
        """
        Send a notification to a user
        
        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, error, success)
            channels: List of delivery channels (web, email, sms, push)
            action_url: Optional action URL
            action_text: Optional action button text
            data: Additional notification data
            scheduled_at: Optional scheduled delivery time
        
        Returns:
            Created Notification object
        """
        try:
            # Default channels
            if channels is None:
                channels = ["web"]
            
            # Create notification
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                channels=channels,
                action_url=action_url,
                action_text=action_text,
                data=data,
                scheduled_at=scheduled_at
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            # Send immediately if not scheduled
            if scheduled_at is None:
                await self._deliver_notification(notification)
            
            return notification
            
        except Exception as e:
            logger.error(f"Notification creation error: {str(e)}")
            self.db.rollback()
            raise
    
    async def send_bulk_notification(
        self,
        user_ids: List[int],
        title: str,
        message: str,
        notification_type: str = "info",
        channels: List[str] = None
    ) -> List[Notification]:
        """
        Send notifications to multiple users
        
        Args:
            user_ids: List of target user IDs
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            channels: List of delivery channels
        
        Returns:
            List of created Notification objects
        """
        notifications = []
        
        for user_id in user_ids:
            try:
                notification = await self.send_notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    channels=channels
                )
                notifications.append(notification)
            except Exception as e:
                logger.error(f"Bulk notification error for user {user_id}: {str(e)}")
        
        return notifications
    
    async def send_email_verification(self, email: str, verification_token: str):
        """
        Send email verification email
        
        Args:
            email: User email
            verification_token: Verification token
        """
        try:
            # Get email template
            template = self.db.query(EmailTemplate).filter(
                EmailTemplate.template_type == "email_verification",
                EmailTemplate.is_active == True
            ).first()
            
            if not template:
                # Use default template
                subject = "Verify Your Email Address"
                body = f"""
                Please click the link below to verify your email address:
                
                {settings.FRONTEND_URL}/verify-email?token={verification_token}
                
                If you didn't create an account, please ignore this email.
                """
            else:
                subject = template.subject
                body = template.body_text.replace("{{verification_token}}", verification_token)
            
            # Send email (implement with your email provider)
            await self._send_email(email, subject, body)
            
        except Exception as e:
            logger.error(f"Email verification send error: {str(e)}")
    
    async def send_password_reset_email(self, email: str, reset_token: str):
        """
        Send password reset email
        
        Args:
            email: User email
            reset_token: Password reset token
        """
        try:
            # Get email template
            template = self.db.query(EmailTemplate).filter(
                EmailTemplate.template_type == "password_reset",
                EmailTemplate.is_active == True
            ).first()
            
            if not template:
                # Use default template
                subject = "Reset Your Password"
                body = f"""
                Please click the link below to reset your password:
                
                {settings.FRONTEND_URL}/reset-password?token={reset_token}
                
                If you didn't request this, please ignore this email.
                """
            else:
                subject = template.subject
                body = template.body_text.replace("{{reset_token}}", reset_token)
            
            # Send email
            await self._send_email(email, subject, body)
            
        except Exception as e:
            logger.error(f"Password reset email send error: {str(e)}")
    
    async def send_welcome_email(self, user_id: int):
        """
        Send welcome email to new user
        
        Args:
            user_id: User ID
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            # Get email template
            template = self.db.query(EmailTemplate).filter(
                EmailTemplate.template_type == "welcome",
                EmailTemplate.is_active == True
            ).first()
            
            if not template:
                # Use default template
                subject = f"Welcome to {settings.SCHOOL_NAME}"
                body = f"""
                Dear {user.first_name},
                
                Welcome to {settings.SCHOOL_NAME}! Your account has been created successfully.
                
                You can now log in to access your dashboard and explore all the features.
                
                Best regards,
                The {settings.SCHOOL_NAME} Team
                """
            else:
                subject = template.subject.replace("{{school_name}}", settings.SCHOOL_NAME)
                body = template.body_text.replace("{{first_name}}", user.first_name)
                body = body.replace("{{school_name}}", settings.SCHOOL_NAME)
            
            # Send email
            await self._send_email(user.email, subject, body)
            
        except Exception as e:
            logger.error(f"Welcome email send error: {str(e)}")
    
    async def send_fee_reminder(self, user_id: int, amount: float, due_date: datetime):
        """
        Send fee payment reminder
        
        Args:
            user_id: User ID
            amount: Fee amount
            due_date: Payment due date
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            # Create notification
            await self.send_notification(
                user_id=user_id,
                title="Fee Payment Reminder",
                message=f"Your fee payment of ${amount:.2f} is due on {due_date.strftime('%Y-%m-%d')}",
                notification_type="warning",
                channels=["web", "email", "sms"],
                action_url="/fees/payment",
                action_text="Pay Now"
            )
            
        except Exception as e:
            logger.error(f"Fee reminder send error: {str(e)}")
    
    async def send_grade_notification(self, user_id: int, subject: str, grade: str):
        """
        Send grade notification
        
        Args:
            user_id: Student user ID
            subject: Subject name
            grade: Grade received
        """
        try:
            # Send to student
            await self.send_notification(
                user_id=user_id,
                title="New Grade Available",
                message=f"You received a grade of {grade} in {subject}",
                notification_type="info",
                channels=["web", "email"],
                action_url="/grades",
                action_text="View Grades"
            )
            
            # Send to parents
            student = self.db.query(User).filter(User.id == user_id).first()
            if student and hasattr(student, 'students'):
                for student_profile in student.students:
                    for parent in student_profile.parents:
                        await self.send_notification(
                            user_id=parent.user_id,
                            title=f"Grade Update for {student.first_name}",
                            message=f"{student.first_name} received a grade of {grade} in {subject}",
                            notification_type="info",
                            channels=["web", "email"],
                            action_url=f"/student/{student.id}/grades",
                            action_text="View Grades"
                        )
            
        except Exception as e:
            logger.error(f"Grade notification send error: {str(e)}")
    
    async def send_attendance_alert(self, user_id: int, student_name: str, date: datetime):
        """
        Send attendance alert to parents
        
        Args:
            user_id: Parent user ID
            student_name: Student name
            date: Absence date
        """
        try:
            await self.send_notification(
                user_id=user_id,
                title="Attendance Alert",
                message=f"{student_name} was absent on {date.strftime('%Y-%m-%d')}",
                notification_type="warning",
                channels=["web", "email", "sms"],
                action_url="/attendance",
                action_text="View Attendance"
            )
            
        except Exception as e:
            logger.error(f"Attendance alert send error: {str(e)}")
    
    async def _deliver_notification(self, notification: Notification):
        """
        Deliver notification through specified channels
        
        Args:
            notification: Notification object to deliver
        """
        try:
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user:
                return
            
            for channel in notification.channels:
                try:
                    if channel == "email":
                        await self._send_email(
                            user.email, 
                            notification.title, 
                            notification.message
                        )
                    elif channel == "sms":
                        await self._send_sms(
                            user.phone, 
                            f"{notification.title}: {notification.message}"
                        )
                    elif channel == "push":
                        await self._send_push_notification(
                            user.id, 
                            notification.title, 
                            notification.message
                        )
                    # "web" channel is handled by storing in database
                    
                except Exception as e:
                    logger.error(f"Channel {channel} delivery error: {str(e)}")
            
            # Mark as sent
            notification.is_sent = True
            notification.sent_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Notification delivery error: {str(e)}")
    
    async def _send_email(self, to_email: str, subject: str, body: str):
        """
        Send email using configured email provider
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
        """
        try:
            # Implement with your email provider (SendGrid, Mailgun, etc.)
            # This is a placeholder implementation
            logger.info(f"Sending email to {to_email}: {subject}")
            
            # Example with SendGrid (uncomment and configure)
            # import sendgrid
            # from sendgrid.helpers.mail import Mail
            # 
            # sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            # mail = Mail(
            #     from_email=settings.EMAILS_FROM_EMAIL,
            #     to_emails=to_email,
            #     subject=subject,
            #     plain_text_content=body
            # )
            # response = sg.send(mail)
            
        except Exception as e:
            logger.error(f"Email send error: {str(e)}")
            raise
    
    async def _send_sms(self, to_phone: str, message: str):
        """
        Send SMS using configured SMS provider
        
        Args:
            to_phone: Recipient phone number
            message: SMS message
        """
        try:
            if not to_phone:
                return
            
            # Implement with your SMS provider (Twilio, etc.)
            # This is a placeholder implementation
            logger.info(f"Sending SMS to {to_phone}: {message}")
            
            # Example with Twilio (uncomment and configure)
            # from twilio.rest import Client
            # 
            # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            # message = client.messages.create(
            #     body=message,
            #     from_=settings.TWILIO_PHONE_NUMBER,
            #     to=to_phone
            # )
            
        except Exception as e:
            logger.error(f"SMS send error: {str(e)}")
            raise
    
    async def _send_push_notification(self, user_id: int, title: str, message: str):
        """
        Send push notification
        
        Args:
            user_id: User ID
            title: Notification title
            message: Notification message
        """
        try:
            # Implement push notification logic
            # This is a placeholder implementation
            logger.info(f"Sending push notification to user {user_id}: {title}")
            
        except Exception as e:
            logger.error(f"Push notification send error: {str(e)}")
            raise
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """
        Mark a notification as read
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for security)
        
        Returns:
            True if marked successfully, False otherwise
        """
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if notification:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Mark notification read error: {str(e)}")
            self.db.rollback()
            return False
    
    def get_user_notifications(
        self, 
        user_id: int, 
        limit: int = 20, 
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Notification]:
        """
        Get user notifications
        
        Args:
            user_id: User ID
            limit: Maximum number of notifications
            offset: Offset for pagination
            unread_only: Return only unread notifications
        
        Returns:
            List of Notification objects
        """
        try:
            query = self.db.query(Notification).filter(
                Notification.user_id == user_id
            )
            
            if unread_only:
                query = query.filter(Notification.is_read == False)
            
            notifications = query.order_by(
                Notification.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return notifications
            
        except Exception as e:
            logger.error(f"Get user notifications error: {str(e)}")
            return []
    
    def cleanup_old_notifications(self, days: int = 30) -> int:
        """
        Clean up old notifications
        
        Args:
            days: Number of days to keep notifications
        
        Returns:
            Number of notifications deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = self.db.query(Notification).filter(
                Notification.created_at < cutoff_date
            ).delete()
            
            self.db.commit()
            return result
            
        except Exception as e:
            logger.error(f"Notification cleanup error: {str(e)}")
            self.db.rollback()
            return 0
