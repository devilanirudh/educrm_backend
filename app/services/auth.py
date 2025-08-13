"""
Authentication service for user management and session handling
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, UserSession
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service class"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, email_or_username: str, password: str) -> Optional[User]:
        """
        Authenticate user with email/username and password
        
        Args:
            email_or_username: User's email or username
            password: Plain text password
        
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # Find user by email or username
            user = self.db.query(User).filter(
                (User.email == email_or_username) | 
                (User.username == email_or_username)
            ).first()
            
            if not user:
                return None
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                return None
            
            # Check if user is active
            if not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None
    
    def create_session(
        self, 
        user_id: int, 
        session_token: str, 
        client_info: Optional[Dict[str, Any]] = None
    ) -> UserSession:
        """
        Create a new user session
        
        Args:
            user_id: User ID
            session_token: Session token
            client_info: Client information (IP, user agent, etc.)
        
        Returns:
            Created UserSession object
        """
        try:
            # Create session
            session = UserSession(
                user_id=user_id,
                session_token=session_token,
                ip_address=client_info.get('ip_address') if client_info else None,
                user_agent=client_info.get('user_agent') if client_info else None,
                device_type=client_info.get('device_type') if client_info else None,
                location=client_info.get('location') if client_info else None,
                expires_at=datetime.utcnow() + timedelta(
                    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
                )
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            return session
            
        except Exception as e:
            logger.error(f"Session creation error: {str(e)}")
            self.db.rollback()
            raise
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate a user session
        
        Args:
            session_token: Session token to invalidate
        
        Returns:
            True if session was invalidated, False otherwise
        """
        try:
            session = self.db.query(UserSession).filter(
                UserSession.session_token == session_token,
                UserSession.is_active == True
            ).first()
            
            if session:
                session.is_active = False
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Session invalidation error: {str(e)}")
            self.db.rollback()
            return False
    
    def invalidate_all_user_sessions(self, user_id: int) -> int:
        """
        Invalidate all sessions for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Number of sessions invalidated
        """
        try:
            result = self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).update({"is_active": False})
            
            self.db.commit()
            return result
            
        except Exception as e:
            logger.error(f"User sessions invalidation error: {str(e)}")
            self.db.rollback()
            return 0
    
    def get_active_sessions(self, user_id: int) -> list[UserSession]:
        """
        Get all active sessions for a user
        
        Args:
            user_id: User ID
        
        Returns:
            List of active UserSession objects
        """
        try:
            sessions = self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).all()
            
            return sessions
            
        except Exception as e:
            logger.error(f"Get active sessions error: {str(e)}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            result = self.db.query(UserSession).filter(
                UserSession.expires_at < datetime.utcnow()
            ).update({"is_active": False})
            
            self.db.commit()
            return result
            
        except Exception as e:
            logger.error(f"Session cleanup error: {str(e)}")
            self.db.rollback()
            return 0
    
    def update_session_activity(self, session_token: str) -> bool:
        """
        Update session last activity timestamp
        
        Args:
            session_token: Session token
        
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            session = self.db.query(UserSession).filter(
                UserSession.session_token == session_token,
                UserSession.is_active == True
            ).first()
            
            if session:
                session.last_activity = datetime.utcnow()
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Session activity update error: {str(e)}")
            self.db.rollback()
            return False
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
        
        Returns:
            True if password changed successfully, False otherwise
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Verify current password
            if not verify_password(current_password, user.hashed_password):
                return False
            
            # Update password
            user.hashed_password = get_password_hash(new_password)
            
            # Invalidate all sessions except current one
            self.invalidate_all_user_sessions(user_id)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Password change error: {str(e)}")
            self.db.rollback()
            return False
    
    def reset_password(self, email: str, new_password: str) -> bool:
        """
        Reset user password
        
        Args:
            email: User email
            new_password: New password
        
        Returns:
            True if password reset successfully, False otherwise
        """
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                return False
            
            # Update password
            user.hashed_password = get_password_hash(new_password)
            
            # Invalidate all sessions
            self.invalidate_all_user_sessions(user.id)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            self.db.rollback()
            return False
    
    def verify_email(self, email: str) -> bool:
        """
        Mark user email as verified
        
        Args:
            email: User email
        
        Returns:
            True if verified successfully, False otherwise
        """
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                return False
            
            user.is_verified = True
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            self.db.rollback()
            return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user account
        
        Args:
            user_id: User ID
        
        Returns:
            True if deactivated successfully, False otherwise
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.is_active = False
            
            # Invalidate all sessions
            self.invalidate_all_user_sessions(user_id)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"User deactivation error: {str(e)}")
            self.db.rollback()
            return False
    
    def activate_user(self, user_id: int) -> bool:
        """
        Activate a user account
        
        Args:
            user_id: User ID
        
        Returns:
            True if activated successfully, False otherwise
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.is_active = True
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"User activation error: {str(e)}")
            self.db.rollback()
            return False
