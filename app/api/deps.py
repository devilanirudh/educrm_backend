"""
API dependency injection for Firebase authentication and authorization
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.firebase_config import verify_firebase_token, get_user_by_uid, get_user_role
from app.core.permissions import UserRole, Permission, check_permission
from app.core.role_config import role_config
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

# Custom security dependency that handles OPTIONS requests
class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        # Skip authentication for OPTIONS requests
        if request.method == "OPTIONS":
            return None
        # For other requests, use normal HTTPBearer behavior
        return await super().__call__(request)

# HTTP Bearer token scheme
security = OptionalHTTPBearer(auto_error=False)

async def get_current_user_firebase(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from Firebase token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required"
        )

    try:
        token = credentials.credentials
        logger.info(f"🔐 Processing Firebase token of length: {len(token)}")
        
        # Verify Firebase token
        firebase_user = verify_firebase_token(token)
        
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        uid = firebase_user['uid']
        email = firebase_user['email']
        
        logger.info(f"🔍 Firebase user verified: {email} (UID: {uid})")
        
        # Get or create user in database
        user = db.query(User).filter(User.email == email).first()
        
        # Check if user has access based on role configuration
        role_str = role_config.get_role_for_email(email)
        
        # Check if user has explicit role mapping (not just default)
        email_mapping = role_config._config.get("email_role_mapping", {})
        domain_mapping = role_config._config.get("domain_role_mapping", {})
        
        has_explicit_mapping = email in email_mapping
        has_domain_mapping = any(email.endswith(domain) for domain in domain_mapping.keys())
        
        # If no explicit mapping found, deny access
        if not has_explicit_mapping and not has_domain_mapping:
            logger.warning(f"🚫 Access denied for email: {email} - No role mapping found")
            logger.info(f"📧 Email: {email} is not in role configuration")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Your email is not authorized to access this system. Please contact the administrator."
            )
        
        if not user:
            # Create new user from Firebase
            logger.info(f"👤 Creating new user from Firebase: {email}")
            
            # Get role from email mapping or Firebase custom claims
            email = firebase_user['email']
            role_str = role_config.get_role_for_email(email)
            
            # If no explicit email mapping, check Firebase custom claims
            email_mapping = role_config._config.get("email_role_mapping", {})
            domain_mapping = role_config._config.get("domain_role_mapping", {})
            
            has_explicit_mapping = email in email_mapping
            has_domain_mapping = any(email.endswith(domain) for domain in domain_mapping.keys())
            
            if not has_explicit_mapping and not has_domain_mapping:
                role_str = firebase_user.get('role', role_str)
            
            try:
                role = UserRole(role_str.lower())
                logger.info(f"🎭 Assigned role '{role.value}' to email: {email}")
            except ValueError:
                logger.warning(f"⚠️ Invalid role '{role_str}', using default from config")
                role = UserRole(role_config.get_default_role('firebase_default'))
            
            # Create user
            user = User(
                email=email,
                first_name=firebase_user.get('name', '').split()[0] if firebase_user.get('name') else '',
                last_name=' '.join(firebase_user.get('name', '').split()[1:]) if firebase_user.get('name') and len(firebase_user.get('name', '').split()) > 1 else '',
                role=role,
                is_active=True,
                is_verified=firebase_user.get('email_verified', False),
                firebase_uid=uid
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"✅ Created new user: {user.id} ({email}) with role: {role.value}")
            
            # Auto-create role-specific profile record
            from datetime import date
            if role == UserRole.STUDENT:
                from app.models.student import Student
                # Generate a unique student ID
                student_count = db.query(Student).count()
                student_id = f"STU{str(student_count + 1).zfill(3)}"
                
                student = Student(
                    user_id=user.id,
                    student_id=student_id,
                    admission_date=date.today(),
                    academic_year="2024-25",  # You might want to make this dynamic
                    is_active=True
                )
                db.add(student)
                db.commit()
                db.refresh(student)
                logger.info(f"✅ Auto-created student profile: {student_id} for user {user.id}")
                
            elif role == UserRole.TEACHER:
                from app.models.teacher import Teacher
                # Generate a unique employee ID
                teacher_count = db.query(Teacher).count()
                employee_id = f"EMP{str(teacher_count + 1).zfill(3)}"
                
                teacher = Teacher(
                    user_id=user.id,
                    employee_id=employee_id,
                    hire_date=date.today(),
                    employment_type="full-time",
                    is_active=True
                )
                db.add(teacher)
                db.commit()
                db.refresh(teacher)
                logger.info(f"✅ Auto-created teacher profile: {employee_id} for user {user.id}")
        else:
            # Update existing user with Firebase UID if not set
            if not user.firebase_uid:
                user.firebase_uid = uid
                db.commit()
                logger.info(f"✅ Updated existing user with Firebase UID: {uid}")
            
            # Update role from email mapping or Firebase if different
            email = firebase_user['email']
            firebase_role = role_config.get_role_for_email(email)
            
            # Check if user has explicit role mapping (not just default)
            email_mapping = role_config._config.get("email_role_mapping", {})
            domain_mapping = role_config._config.get("domain_role_mapping", {})
            
            has_explicit_mapping = email in email_mapping
            has_domain_mapping = any(email.endswith(domain) for domain in domain_mapping.keys())
            
            # If no explicit mapping found, deny access
            if not has_explicit_mapping and not has_domain_mapping:
                logger.warning(f"🚫 Access denied for existing user: {email} - No role mapping found")
                logger.info(f"📧 Email: {email} is not in role configuration")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Your email is not authorized to access this system. Please contact the administrator."
                )
            
            # If no explicit email mapping, check Firebase custom claims
            if not has_explicit_mapping and not has_domain_mapping:
                firebase_role = firebase_user.get('role', firebase_role)
            try:
                firebase_role_enum = UserRole(firebase_role.lower())
                if user.role != firebase_role_enum:
                    user.role = firebase_role_enum
                    db.commit()
                    logger.info(f"🔄 Updated user role from {user.role.value} to {firebase_role_enum.value}")
            except ValueError:
                logger.warning(f"⚠️ Invalid Firebase role '{firebase_role}', keeping existing role: {user.role.value}")
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        logger.info(f"✅ Successfully authenticated: {email} ({user.id}) with role: {user.role.value}")
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 403 Forbidden) without modification
        raise
    except Exception as e:
        logger.error(f"❌ Firebase authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

# Alias for backward compatibility
get_current_user = get_current_user_firebase

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for get_current_user for clarity)
    """
    return current_user

def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they have admin privileges
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user if they are an admin
    
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user

def get_current_teacher_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are a teacher
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user if they are a teacher
    
    Raises:
        HTTPException: If user is not a teacher
    """
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher privileges required"
        )
    
    return current_user

def get_current_student_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are a student
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user if they are a student
    
    Raises:
        HTTPException: If user is not a student
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student privileges required"
        )
    
    return current_user

def get_current_parent_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are a parent
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user if they are a parent
    
    Raises:
        HTTPException: If user is not a parent
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent privileges required"
        )
    
    return current_user

def require_permission(required_permission: Permission):
    """
    Dependency factory to require specific permission
    
    Args:
        required_permission: Permission required to access the endpoint
    
    Returns:
        Dependency function that checks the permission
    """
    def permission_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        check_permission(current_user.role, required_permission)
        return current_user
    
    return permission_dependency

def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    Used for endpoints that work for both authenticated and anonymous users
    
    Args:
        db: Database session
        credentials: Optional Firebase credentials
    
    Returns:
        Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        firebase_user = verify_firebase_token(token)
        
        if not firebase_user:
            return None
        
        email = firebase_user['email']
        user = db.query(User).filter(User.email == email).first()
        
        if user and user.is_active:
            return user
    except:
        # Invalid token, but we don't want to raise an exception
        # for optional authentication
        pass
    
    return None

class PaginationParams:
    """Pagination parameters"""
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20
    ):
        self.skip = max(0, skip)
        self.limit = min(100, max(1, limit))  # Limit between 1 and 100

def get_pagination_params(
    skip: int = 0,
    limit: int = 20
) -> PaginationParams:
    """
    Get pagination parameters with validation
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        PaginationParams object with validated values
    """
    return PaginationParams(skip=skip, limit=limit)

class SearchParams:
    """Search parameters"""
    def __init__(
        self,
        q: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ):
        self.q = q
        self.sort_by = sort_by
        self.sort_order = sort_order.lower() if sort_order.lower() in ["asc", "desc"] else "asc"

def get_search_params(
    q: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
) -> SearchParams:
    """
    Get search parameters with validation
    
    Args:
        q: Search query string
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)
    
    Returns:
        SearchParams object with validated values
    """
    return SearchParams(q=q, sort_by=sort_by, sort_order=sort_order)

def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session dependency
    """
    return get_db()

# Common permission dependencies
require_admin = require_permission(Permission.USER_CREATE)
require_teacher_read = require_permission(Permission.TEACHER_READ)
require_student_read = require_permission(Permission.STUDENT_READ)
require_class_read = require_permission(Permission.CLASS_READ)
require_assignment_read = require_permission(Permission.ASSIGNMENT_READ)
require_exam_read = require_permission(Permission.EXAM_READ)
require_fee_read = require_permission(Permission.FEE_READ)
require_live_class_read = require_permission(Permission.LIVE_CLASS_READ)
require_library_read = require_permission(Permission.LIBRARY_READ)
require_transport_read = require_permission(Permission.TRANSPORT_READ)
require_hostel_read = require_permission(Permission.HOSTEL_READ)
require_event_read = require_permission(Permission.EVENT_READ)
require_cms_read = require_permission(Permission.CMS_READ)
require_crm_read = require_permission(Permission.CRM_READ)
require_report_view = require_permission(Permission.REPORT_VIEW)
require_communication_read = require_permission(Permission.COMMUNICATION_READ)
