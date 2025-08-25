"""
Authentication API endpoints
"""

from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.config import settings
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    verify_token,
    generate_password_reset_token,
    verify_password_reset_token,
    create_email_verification_token,
    verify_email_verification_token,
    validate_password_strength
)
from app.models.user import User, UserSession
from app.api.deps import get_current_user, get_current_user_with_impersonation
from app.schemas.user import UserCreate, UserResponse, Token, PasswordReset, PasswordResetConfirm
from app.services.auth import AuthService
from app.services.notification import NotificationService
from app.core.permissions import UserRole
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    background_tasks: BackgroundTasks,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    User login with username/email and password
    
    Returns access and refresh tokens
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    try:
        # Find user by email or username
        logger.info("Querying for user...")
        user = db.query(User).filter(
            (User.email == form_data.username) |
            (User.username == form_data.username)
        ).first()
        logger.info(f"User found: {user.email if user else 'No'}")
        
        if not user:
            logger.warning(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        logger.info("Verifying password...")
        if not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Invalid password for user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        logger.info("Password verified.")
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive account login attempt: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Create tokens
        logger.info("Creating access and refresh tokens...")
        access_token = create_access_token(
            subject=user.id,
            additional_claims={
                "role": user.role.value,
                "current_role": user.role.value
            }
        )
        refresh_token = create_refresh_token(subject=user.id)
        logger.info("Tokens created.")
        
        # Update last login
        logger.info("Updating last login time.")
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create session record (in background)
        auth_service = AuthService(db)
        background_tasks.add_task(
            auth_service.create_session,
            user.id,
            access_token,
            form_data.client_id if hasattr(form_data, 'client_id') else None
        )
        
        logger.info(f"User {user.email} logged in successfully")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified
            }
        }
        
    except HTTPException as http_exc:
        logger.warning(f"HTTP exception during login for {form_data.username}: {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during login for {form_data.username}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during login."
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token
    """
    try:
        # Verify refresh token
        user_id = verify_token(refresh_token, "refresh")
        
        # Get user
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = create_access_token(
            subject=user.id,
            additional_claims={"role": user.role.value}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,  # Keep the same refresh token
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    User logout - invalidate session
    """
    try:
        # Invalidate user sessions
        db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        
        logger.info(f"User {current_user.email} logged out")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information
    """
    return current_user

@router.post("/register", response_model=UserResponse)
async def register(
    background_tasks: BackgroundTasks,
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    Note: This might be restricted based on school policies
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | 
            (User.username == user_data.username)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        
        # Validate password strength
        if not validate_password_strength(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements"
            )
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=user_data.role,
            is_active=True,
            is_verified=False  # Require email verification
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send verification email (in background)
        notification_service = NotificationService(db)
        verification_token = create_email_verification_token(user.email)
        background_tasks.add_task(
            notification_service.send_email_verification,
            user.email,
            verification_token
        )
        
        logger.info(f"New user registered: {user.email}")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify user email address
    """
    try:
        # Verify token and get email
        email = verify_email_verification_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Update user verification status
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_verified:
            return {"message": "Email already verified"}
        
        user.is_verified = True
        db.commit()
        
        logger.info(f"Email verified for user: {user.email}")
        
        return {"message": "Email verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )

@router.post("/forgot-password")
async def forgot_password(
    background_tasks: BackgroundTasks,
    password_reset: PasswordReset,
    db: Session = Depends(get_db)
) -> Any:
    """
    Request password reset
    """
    try:
        # Find user by email
        user = db.query(User).filter(User.email == password_reset.email).first()
        if not user:
            # Don't reveal if email exists or not
            return {"message": "If the email exists, a password reset link has been sent"}
        
        # Generate reset token
        reset_token = generate_password_reset_token(user.email)
        
        # Send reset email (in background)
        notification_service = NotificationService(db)
        background_tasks.add_task(
            notification_service.send_password_reset_email,
            user.email,
            reset_token
        )
        
        logger.info(f"Password reset requested for: {user.email}")
        
        return {"message": "If the email exists, a password reset link has been sent"}
        
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )

@router.post("/reset-password")
async def reset_password(
    password_reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Any:
    """
    Reset password with token
    """
    try:
        # Verify reset token
        email = verify_password_reset_token(password_reset_confirm.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Validate new password
        if not validate_password_strength(password_reset_confirm.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements"
            )
        
        # Update user password
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.hashed_password = get_password_hash(password_reset_confirm.new_password)
        
        # Invalidate all user sessions
        db.query(UserSession).filter(
            UserSession.user_id == user.id
        ).update({"is_active": False})
        
        db.commit()
        
        logger.info(f"Password reset completed for: {user.email}")
        
        return {"message": "Password reset successful"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Change password for authenticated user
    """
    try:
        # Verify current password
        if not verify_password(current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if not validate_password_strength(new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password does not meet security requirements"
            )
        
        # Update password
        current_user.hashed_password = get_password_hash(new_password)
        
        # Invalidate all other sessions
        db.query(UserSession).filter(
            UserSession.user_id == current_user.id
        ).update({"is_active": False})
        
        db.commit()
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.post("/switch-role", response_model=Token)
async def switch_role(
    new_role: UserRole,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Switch the current user's role (e.g., from Super Admin to Admin)
    """
    # Validate that the user is allowed to switch to the new role
    if not current_user.role == UserRole.SUPER_ADMIN and not new_role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to switch to this role"
        )

    # Create a new access token with the updated current_role
    access_token = create_access_token(
        subject=current_user.id,
        additional_claims={
            "role": current_user.role.value,
            "current_role": new_role.value
        }
    )
    
    # Log the role switch
    auth_service = AuthService(db)
    auth_service.create_audit_log(
        user_id=current_user.id,
        action="role_switch",
        details=f"Switched role to {new_role.value}"
    )

    return {
        "access_token": access_token,
        "refresh_token": "",  # A new refresh token is not issued
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/impersonate-user/{user_id}")
async def impersonate_user(
    user_id: int,
    current_user: User = Depends(get_current_user_with_impersonation),
    db: Session = Depends(get_db)
) -> Any:
    """
    Impersonate another user (Super Admin and Admin only)
    """
    # Only super admins and admins can impersonate users
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can impersonate users"
        )
    
    # Get the user to impersonate
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent impersonating other admins unless you're a super admin
    if target_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN] and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can impersonate other administrators"
        )
    
    # For now, let's use a simpler approach - store impersonation state in the database
    # and modify the Firebase authentication to check for impersonation
    
    # Create an impersonation session
    from app.models.user import UserSession
    import secrets
    
    # Generate a unique session token
    session_token = f"impersonation_{secrets.token_urlsafe(32)}"
    
    logger.info(f"🎭 Creating impersonation session for user {target_user.id} by {current_user.id}")
    logger.info(f"🔑 Generated session token: {session_token}")
    
    impersonation_session = UserSession(
        user_id=target_user.id,
        session_token=session_token,
        impersonated_by=current_user.id,
        is_impersonation=True,
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(hours=1)  # 1 hour session
    )
    db.add(impersonation_session)
    db.commit()
    
    logger.info(f"✅ Impersonation session created with ID: {impersonation_session.id}")
    
    # Log the impersonation
    auth_service = AuthService(db)
    auth_service.create_audit_log(
        user_id=current_user.id,
        action="user_impersonation",
        details=f"Impersonated user {target_user.email} (ID: {target_user.id})"
    )
    
    # Also log for the target user
    auth_service.create_audit_log(
        user_id=target_user.id,
        action="user_impersonated",
        details=f"Impersonated by {current_user.email} (ID: {current_user.id})"
    )

    # Get the original user (the one doing the impersonation)
    original_user = db.query(User).filter(User.id == current_user.id).first()
    
    # Debug role values
    logger.info(f"🎭 Target user role: {target_user.role} (type: {type(target_user.role)})")
    logger.info(f"🎭 Target user role value: {target_user.role.value} (type: {type(target_user.role.value)})")
    logger.info(f"🎭 Original user role: {original_user.role} (type: {type(original_user.role)})")
    logger.info(f"🎭 Original user role value: {original_user.role.value} (type: {type(original_user.role.value)})")
    
    return {
        "access_token": session_token,  # Return the actual session token
        "refresh_token": "",
        "token_type": "bearer",
        "expires_in": 3600,  # 1 hour
        "impersonated_user": {
            "id": target_user.id,
            "email": target_user.email,
            "first_name": target_user.first_name,
            "last_name": target_user.last_name,
            "role": str(target_user.role.value),
            "is_active": target_user.is_active,
            "is_verified": target_user.is_verified,
            "created_at": target_user.created_at.isoformat() if target_user.created_at else datetime.utcnow().isoformat(),
            "updated_at": target_user.updated_at.isoformat() if target_user.updated_at else datetime.utcnow().isoformat(),
            "language_preference": "en",
            "timezone": "UTC"
        },
        "original_user": {
            "id": original_user.id,
            "email": original_user.email,
            "first_name": original_user.first_name,
            "last_name": original_user.last_name,
            "role": str(original_user.role.value),
            "is_active": original_user.is_active,
            "is_verified": original_user.is_verified,
            "created_at": original_user.created_at.isoformat() if original_user.created_at else datetime.utcnow().isoformat(),
            "updated_at": original_user.updated_at.isoformat() if original_user.updated_at else datetime.utcnow().isoformat(),
            "language_preference": "en",
            "timezone": "UTC"
        },
        "session_id": impersonation_session.id
    }


@router.post("/stop-impersonation", response_model=Token)
async def stop_impersonation(
    current_user: User = Depends(get_current_user_with_impersonation),
    db: Session = Depends(get_db)
) -> Any:
    """
    Stop impersonating and return to original user
    """
    # Check if user is currently impersonating
    if not hasattr(current_user, 'impersonated_by') or not current_user.impersonated_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not currently impersonating any user"
        )
    
    # Get the original user
    original_user = db.query(User).filter(User.id == current_user.impersonated_by).first()
    if not original_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original user not found"
        )
    
    # Deactivate the impersonation session
    from app.models.user import UserSession
    session = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.impersonated_by == current_user.impersonated_by,
        UserSession.is_impersonation == True,
        UserSession.is_active == True
    ).first()
    
    if session:
        session.is_active = False
        db.commit()
    
    # Log the end of impersonation
    auth_service = AuthService(db)
    auth_service.create_audit_log(
        user_id=original_user.id,
        action="impersonation_ended",
        details=f"Stopped impersonating user {current_user.email} (ID: {current_user.id})"
    )

    return {
        "access_token": "session_ended",
        "refresh_token": "",
        "token_type": "bearer",
        "expires_in": 0,
    }


@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a user and their profile (cascade delete)"""
    
    # Only super_admin and admin can delete users
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete users"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        # Store user info for logging
        user_email = user.email
        user_role = user.role.value
        
        # Delete the user (this will cascade to related profile records)
        db.delete(user)
        
        db.commit()
        
        logger.info(f"User {user_email} (role: {user_role}) deleted by {current_user.email}")
        
        return {"message": "User and related profile deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
