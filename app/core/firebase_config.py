"""
Firebase configuration and authentication utilities
"""
import os
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.exceptions import FirebaseError
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Firebase configuration
FIREBASE_PROJECT_ID = "educrm-9f3f9"
FIREBASE_FRONTEND_KEY = "AIzaSyDMiQ2voLNHsKLC5pn9opzku8vDTxd_faY"

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account"""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            # Use the service account file
            cred = credentials.Certificate("educrm-9f3f9-firebase-adminsdk-fbsvc-7aca51fb42.json")
            firebase_admin.initialize_app(cred, {
                'projectId': FIREBASE_PROJECT_ID
            })
            logger.info("✅ Firebase Admin SDK initialized successfully")
        else:
            logger.info("✅ Firebase Admin SDK already initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase Admin SDK: {str(e)}")
        raise

def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    """
    Verify Firebase ID token and return user information
    
    Args:
        id_token: Firebase ID token from frontend
        
    Returns:
        Dict containing user information from Firebase
    """
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        
        # Extract user information
        user_info = {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'email_verified': decoded_token.get('email_verified', False),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture'),
            'provider_id': decoded_token.get('firebase', {}).get('sign_in_provider'),
            'custom_claims': decoded_token.get('firebase', {}).get('sign_in_provider') == 'custom',
            'role': decoded_token.get('role', 'student'),  # Default role
            'created_at': decoded_token.get('iat'),
            'expires_at': decoded_token.get('exp')
        }
        
        logger.info(f"✅ Firebase token verified for user: {user_info['email']}")
        return user_info
        
    except FirebaseError as e:
        logger.error(f"❌ Firebase token verification failed: {str(e)}")
        raise ValueError(f"Invalid Firebase token: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error during token verification: {str(e)}")
        raise ValueError(f"Token verification failed: {str(e)}")

def get_user_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    """
    Get user information from Firebase by UID
    
    Args:
        uid: Firebase user UID
        
    Returns:
        User information dict or None if not found
    """
    try:
        user_record = auth.get_user(uid)
        return {
            'uid': user_record.uid,
            'email': user_record.email,
            'email_verified': user_record.email_verified,
            'display_name': user_record.display_name,
            'photo_url': user_record.photo_url,
            'disabled': user_record.disabled,
            'custom_claims': user_record.custom_claims or {},
            'created_at': user_record.user_metadata.creation_timestamp,
            'last_sign_in': user_record.user_metadata.last_sign_in_timestamp
        }
    except FirebaseError as e:
        logger.error(f"❌ Failed to get user by UID {uid}: {str(e)}")
        return None

def set_user_role(uid: str, role: str) -> bool:
    """
    Set custom claims for user role
    
    Args:
        uid: Firebase user UID
        role: Role to assign (super_admin, admin, teacher, student, parent)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Define role hierarchy
        role_hierarchy = {
            'super_admin': 100,
            'admin': 80,
            'teacher': 60,
            'parent': 40,
            'student': 20
        }
        
        if role not in role_hierarchy:
            raise ValueError(f"Invalid role: {role}")
        
        # Set custom claims
        custom_claims = {
            'role': role,
            'role_level': role_hierarchy[role]
        }
        
        auth.set_custom_user_claims(uid, custom_claims)
        logger.info(f"✅ Set role '{role}' for user {uid}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to set role for user {uid}: {str(e)}")
        return False

def get_user_role(uid: str) -> Optional[str]:
    """
    Get user role from custom claims
    
    Args:
        uid: Firebase user UID
        
    Returns:
        Role string or None if not found
    """
    try:
        user_record = auth.get_user(uid)
        custom_claims = user_record.custom_claims or {}
        return custom_claims.get('role')
    except FirebaseError as e:
        logger.error(f"❌ Failed to get role for user {uid}: {str(e)}")
        return None

# Initialize Firebase on module import
initialize_firebase()
