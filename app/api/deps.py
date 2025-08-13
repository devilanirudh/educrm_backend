"""
API dependency injection for authentication and authorization
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import verify_token
from app.core.permissions import UserRole, Permission, check_permission
from app.models.user import User

# JWT Bearer token security
security = HTTPBearer()

def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        db: Database session
        credentials: JWT credentials from Authorization header
    
    Returns:
        Current user object
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify token and get user ID
    user_id = verify_token(token, "access")
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return user

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
        credentials: Optional JWT credentials
    
    Returns:
        Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_id = verify_token(token, "access")
        user = db.query(User).filter(User.id == int(user_id)).first()
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
