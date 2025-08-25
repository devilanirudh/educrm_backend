import logging
import secrets
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class JitsiService:
    """Service for managing Jitsi Meet live classes"""
    
    def __init__(self):
        self.jitsi_url = "https://ec2-16-171-4-237.eu-north-1.compute.amazonaws.com:8443"
        self.api_secret = self._generate_api_secret()
        
    def _generate_api_secret(self) -> str:
        """Generate a secure API secret for Jitsi"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def create_meeting_room(self, room_name: str, teacher_name: str, class_name: str) -> Dict[str, Any]:
        """
        Create a Jitsi meeting room for live class
        
        Args:
            room_name: Unique room name
            teacher_name: Name of the teacher
            class_name: Name of the class
            
        Returns:
            Dict containing meeting details
        """
        try:
            # Generate a secure room name
            secure_room_name = f"{room_name}-{secrets.token_urlsafe(8)}"
            
            # Create meeting URL
            meeting_url = f"{self.jitsi_url}/{secure_room_name}"
            
            # Create meeting configuration
            meeting_config = {
                "room_name": secure_room_name,
                "meeting_url": meeting_url,
                "teacher_name": teacher_name,
                "class_name": class_name,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=2),  # 2 hour expiry
                "is_active": True,
                "participants": [],
                "settings": {
                    "start_with_audio_muted": False,
                    "start_with_video_muted": False,
                    "disable_audio_levels": False,
                    "disable_remote_video_menu": False,
                    "disable_1on1_mode": False,
                    "enable_whiteboard": True,
                    "enable_chat": True,
                    "enable_screen_sharing": True,
                    "enable_recording": True,
                    "enable_breakout_rooms": True,
                    "enable_polls": True,
                    "enable_reactions": True,
                    "max_participants": 50
                }
            }
            
            logger.info(f"Created Jitsi meeting room: {secure_room_name}")
            return meeting_config
            
        except Exception as e:
            logger.error(f"Error creating Jitsi meeting room: {str(e)}")
            raise
    
    def join_meeting(self, room_name: str, participant_name: str, participant_role: str) -> Dict[str, Any]:
        """
        Join a Jitsi meeting room
        
        Args:
            room_name: Room name to join
            participant_name: Name of the participant
            participant_role: Role of the participant (teacher/student)
            
        Returns:
            Dict containing join details
        """
        try:
            meeting_url = f"{self.jitsi_url}/{room_name}"
            
            # Configure participant settings based on role
            if participant_role.lower() == "teacher":
                settings = {
                    "start_with_audio_muted": False,
                    "start_with_video_muted": False,
                    "disable_audio_levels": False,
                    "disable_remote_video_menu": False,
                    "can_edit_whiteboard": True,
                    "can_record": True,
                    "can_manage_participants": True,
                    "can_manage_breakout_rooms": True,
                    "can_create_polls": True
                }
            else:  # student
                settings = {
                    "start_with_audio_muted": True,
                    "start_with_video_muted": True,
                    "disable_audio_levels": False,
                    "disable_remote_video_menu": False,
                    "can_edit_whiteboard": False,
                    "can_record": False,
                    "can_manage_participants": False,
                    "can_manage_breakout_rooms": False,
                    "can_create_polls": False
                }
            
            join_config = {
                "room_name": room_name,
                "meeting_url": meeting_url,
                "participant_name": participant_name,
                "participant_role": participant_role,
                "joined_at": datetime.utcnow(),
                "settings": settings
            }
            
            logger.info(f"Participant {participant_name} joined room {room_name} as {participant_role}")
            return join_config
            
        except Exception as e:
            logger.error(f"Error joining Jitsi meeting: {str(e)}")
            raise
    
    def end_meeting(self, room_name: str) -> bool:
        """
        End a Jitsi meeting room
        
        Args:
            room_name: Room name to end
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # In a real implementation, you might call Jitsi's API to end the meeting
            # For now, we'll just log the action
            logger.info(f"Ended Jitsi meeting room: {room_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error ending Jitsi meeting: {str(e)}")
            return False
    
    def get_meeting_info(self, room_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a meeting room
        
        Args:
            room_name: Room name to get info for
            
        Returns:
            Dict containing meeting information or None if not found
        """
        try:
            # In a real implementation, you might call Jitsi's API to get meeting info
            # For now, we'll return basic info
            meeting_url = f"{self.jitsi_url}/{room_name}"
            
            return {
                "room_name": room_name,
                "meeting_url": meeting_url,
                "is_active": True,
                "created_at": datetime.utcnow() - timedelta(minutes=30),  # Mock data
                "participant_count": 0  # Would be fetched from Jitsi API
            }
            
        except Exception as e:
            logger.error(f"Error getting meeting info: {str(e)}")
            return None
    
    def generate_meeting_token(self, room_name: str, participant_name: str, 
                             participant_role: str, exp: int = 3600) -> str:
        """
        Generate a JWT token for joining a meeting
        
        Args:
            room_name: Room name
            participant_name: Name of the participant
            participant_role: Role of the participant
            exp: Token expiration time in seconds
            
        Returns:
            JWT token string
        """
        try:
            # In a real implementation, you would use a JWT library to create tokens
            # For now, we'll return a simple token
            import jwt
            
            payload = {
                "aud": "jitsi",
                "iss": "your-app",
                "sub": self.jitsi_url,
                "room": room_name,
                "context": {
                    "user": {
                        "id": participant_name,
                        "name": participant_name,
                        "email": f"{participant_name}@example.com",
                        "avatar": "",
                        "moderator": participant_role.lower() == "teacher"
                    }
                },
                "exp": datetime.utcnow().timestamp() + exp,
                "iat": datetime.utcnow().timestamp()
            }
            
            token = jwt.encode(payload, self.api_secret, algorithm="HS256")
            return token
            
        except Exception as e:
            logger.error(f"Error generating meeting token: {str(e)}")
            raise

# Create a global instance
jitsi_service = JitsiService()
