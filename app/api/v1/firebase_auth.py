"""
Firebase Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_user, get_current_admin_user
from app.models.user import User
from app.core.firebase_config import verify_firebase_token, set_user_role, get_user_role
from app.core.permissions import UserRole
from app.core.role_config import role_config
from app.schemas.auth import UserResponse, RoleUpdateRequest
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/verify-token")
async def verify_token(
    token_data: Dict[str, str],
    db: Session = Depends(get_db)
):
    """
    Verify Firebase ID token and return user information
    """
    try:
        id_token = token_data.get("idToken")
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID token is required"
            )
        
        # Verify the token
        firebase_user = verify_firebase_token(id_token)
        
        # Get or create user in database
        user = db.query(User).filter(User.email == firebase_user['email']).first()
        
        # Check if user has access based on role configuration
        email = firebase_user['email']
        role_str = role_config.get_role_for_email(email)
        
        # If no role mapping found, deny access
        if role_str == role_config.get_default_role('firebase_default'):
            logger.warning(f"🚫 Access denied for email: {email} - No role mapping found")
            logger.info(f"📧 Email: {email} is not in role configuration")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Your email is not authorized to access this system. Please contact the administrator."
            )
        
        if not user:
            # Create new user
            email = firebase_user['email']
            role_str = role_config.get_role_for_email(email)
            
            # If no email mapping, check Firebase custom claims
            if role_str == role_config.get_default_role('firebase_default'):
                role_str = firebase_user.get('role', role_str)
            
            try:
                role = UserRole(role_str.lower())
                logger.info(f"🎭 Assigned role '{role.value}' to email: {email}")
            except ValueError:
                logger.warning(f"⚠️ Invalid role '{role_str}', using default from config")
                role = UserRole(role_config.get_default_role('firebase_default'))
            
            user = User(
                email=firebase_user['email'],
                first_name=firebase_user.get('name', '').split()[0] if firebase_user.get('name') else '',
                last_name=' '.join(firebase_user.get('name', '').split()[1:]) if firebase_user.get('name') and len(firebase_user.get('name', '').split()) > 1 else '',
                role=role,
                is_active=True,
                is_verified=firebase_user.get('email_verified', False),
                firebase_uid=firebase_user['uid']
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"✅ Created new user from Firebase: {user.email} with role: {role.value}")
        else:
            # Update existing user's role if needed
            email = firebase_user['email']
            firebase_role = role_config.get_role_for_email(email)
            
            # If no role mapping found, deny access
            if firebase_role == role_config.get_default_role('firebase_default'):
                logger.warning(f"🚫 Access denied for existing user: {email} - No role mapping found")
                logger.info(f"📧 Email: {email} is not in role configuration")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Your email is not authorized to access this system. Please contact the administrator."
                )
            
            # If no email mapping, check Firebase custom claims
            if firebase_role == role_config.get_default_role('firebase_default'):
                firebase_role = firebase_user.get('role', firebase_role)
            
            try:
                firebase_role_enum = UserRole(firebase_role.lower())
                if user.role != firebase_role_enum:
                    user.role = firebase_role_enum
                    db.commit()
                    logger.info(f"🔄 Updated user role from {user.role.value} to {firebase_role_enum.value}")
            except ValueError:
                logger.warning(f"⚠️ Invalid Firebase role '{firebase_role}', keeping existing role: {user.role.value}")
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "firebase_uid": user.firebase_uid
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 403 Forbidden) without modification
        raise
    except Exception as e:
        logger.error(f"❌ Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return current_user

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: RoleUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user role (admin only)
    """
    try:
        # Get user to update
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate role
        try:
            new_role = UserRole(role_data.role.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role_data.role}"
            )
        
        # Update role in database
        user.role = new_role
        db.commit()
        
        # Update role in Firebase if user has Firebase UID
        if user.firebase_uid:
            success = set_user_role(user.firebase_uid, role_data.role.lower())
            if not success:
                logger.warning(f"⚠️ Failed to update Firebase role for user {user.email}")
        
        logger.info(f"✅ Updated role for user {user.email} to {new_role.value}")
        
        return {
            "success": True,
            "message": f"Role updated to {new_role.value}",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role.value
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update user role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )

@router.get("/users/{user_id}/firebase-role")
async def get_firebase_user_role(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user's Firebase role (admin only)
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.firebase_uid:
            return {
                "firebase_uid": None,
                "firebase_role": None,
                "message": "User does not have Firebase UID"
            }
        
        firebase_role = get_user_role(user.firebase_uid)
        
        return {
            "firebase_uid": user.firebase_uid,
            "firebase_role": firebase_role,
            "database_role": user.role.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get Firebase role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Firebase role"
        )

@router.post("/sync-firebase-roles")
async def sync_firebase_roles(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Sync all user roles from database to Firebase (admin only)
    """
    try:
        users = db.query(User).filter(User.firebase_uid.isnot(None)).all()
        updated_count = 0
        failed_count = 0
        
        for user in users:
            try:
                success = set_user_role(user.firebase_uid, user.role.value)
                if success:
                    updated_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to sync role for user {user.email}: {str(e)}")
                failed_count += 1
        
        return {
            "success": True,
            "message": f"Role sync completed",
            "updated": updated_count,
            "failed": failed_count,
            "total": len(users)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to sync Firebase roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync Firebase roles"
        )
