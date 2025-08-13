"""
Role-based access control (RBAC) and permissions system
"""

from enum import Enum
from typing import List, Dict, Set
from fastapi import HTTPException, status


class UserRole(str, Enum):
    """User roles in the system"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"
    STAFF = "staff"
    GUEST = "guest"


class Permission(str, Enum):
    """System permissions"""
    
    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    
    # Student Management
    STUDENT_CREATE = "student:create"
    STUDENT_READ = "student:read"
    STUDENT_UPDATE = "student:update"
    STUDENT_DELETE = "student:delete"
    STUDENT_LIST = "student:list"
    STUDENT_GRADES = "student:grades"
    STUDENT_ATTENDANCE = "student:attendance"
    
    # Teacher Management
    TEACHER_CREATE = "teacher:create"
    TEACHER_READ = "teacher:read"
    TEACHER_UPDATE = "teacher:update"
    TEACHER_DELETE = "teacher:delete"
    TEACHER_LIST = "teacher:list"
    TEACHER_SCHEDULE = "teacher:schedule"
    
    # Class Management
    CLASS_CREATE = "class:create"
    CLASS_READ = "class:read"
    CLASS_UPDATE = "class:update"
    CLASS_DELETE = "class:delete"
    CLASS_LIST = "class:list"
    CLASS_ASSIGN_TEACHER = "class:assign_teacher"
    
    # Assignment Management
    ASSIGNMENT_CREATE = "assignment:create"
    ASSIGNMENT_READ = "assignment:read"
    ASSIGNMENT_UPDATE = "assignment:update"
    ASSIGNMENT_DELETE = "assignment:delete"
    ASSIGNMENT_LIST = "assignment:list"
    ASSIGNMENT_GRADE = "assignment:grade"
    ASSIGNMENT_SUBMIT = "assignment:submit"
    
    # Exam Management
    EXAM_CREATE = "exam:create"
    EXAM_READ = "exam:read"
    EXAM_UPDATE = "exam:update"
    EXAM_DELETE = "exam:delete"
    EXAM_LIST = "exam:list"
    EXAM_GRADE = "exam:grade"
    EXAM_TAKE = "exam:take"
    
    # Fee Management
    FEE_CREATE = "fee:create"
    FEE_READ = "fee:read"
    FEE_UPDATE = "fee:update"
    FEE_DELETE = "fee:delete"
    FEE_LIST = "fee:list"
    FEE_PAYMENT = "fee:payment"
    
    # Live Classes
    LIVE_CLASS_CREATE = "live_class:create"
    LIVE_CLASS_READ = "live_class:read"
    LIVE_CLASS_UPDATE = "live_class:update"
    LIVE_CLASS_DELETE = "live_class:delete"
    LIVE_CLASS_LIST = "live_class:list"
    LIVE_CLASS_JOIN = "live_class:join"
    LIVE_CLASS_HOST = "live_class:host"
    
    # Library Management
    LIBRARY_CREATE = "library:create"
    LIBRARY_READ = "library:read"
    LIBRARY_UPDATE = "library:update"
    LIBRARY_DELETE = "library:delete"
    LIBRARY_LIST = "library:list"
    LIBRARY_BORROW = "library:borrow"
    LIBRARY_RETURN = "library:return"
    
    # Transport Management
    TRANSPORT_CREATE = "transport:create"
    TRANSPORT_READ = "transport:read"
    TRANSPORT_UPDATE = "transport:update"
    TRANSPORT_DELETE = "transport:delete"
    TRANSPORT_LIST = "transport:list"
    
    # Hostel Management
    HOSTEL_CREATE = "hostel:create"
    HOSTEL_READ = "hostel:read"
    HOSTEL_UPDATE = "hostel:update"
    HOSTEL_DELETE = "hostel:delete"
    HOSTEL_LIST = "hostel:list"
    
    # Event Management
    EVENT_CREATE = "event:create"
    EVENT_READ = "event:read"
    EVENT_UPDATE = "event:update"
    EVENT_DELETE = "event:delete"
    EVENT_LIST = "event:list"
    EVENT_REGISTER = "event:register"
    
    # CMS Management
    CMS_CREATE = "cms:create"
    CMS_READ = "cms:read"
    CMS_UPDATE = "cms:update"
    CMS_DELETE = "cms:delete"
    CMS_LIST = "cms:list"
    CMS_PUBLISH = "cms:publish"
    
    # CRM Management
    CRM_CREATE = "crm:create"
    CRM_READ = "crm:read"
    CRM_UPDATE = "crm:update"
    CRM_DELETE = "crm:delete"
    CRM_LIST = "crm:list"
    CRM_CONVERT_LEAD = "crm:convert_lead"
    
    # Reports and Analytics
    REPORT_VIEW = "report:view"
    REPORT_CREATE = "report:create"
    REPORT_EXPORT = "report:export"
    ANALYTICS_VIEW = "analytics:view"
    
    # Communication
    COMMUNICATION_SEND = "communication:send"
    COMMUNICATION_READ = "communication:read"
    COMMUNICATION_BROADCAST = "communication:broadcast"
    
    # System Administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_USERS = "system:users"


# Role-Permission Mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.SUPER_ADMIN: {perm for perm in Permission},  # All permissions
    
    UserRole.ADMIN: {
        # User Management
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_LIST,
        
        # Student Management
        Permission.STUDENT_CREATE,
        Permission.STUDENT_READ,
        Permission.STUDENT_UPDATE,
        Permission.STUDENT_DELETE,
        Permission.STUDENT_LIST,
        Permission.STUDENT_GRADES,
        Permission.STUDENT_ATTENDANCE,
        
        # Teacher Management
        Permission.TEACHER_CREATE,
        Permission.TEACHER_READ,
        Permission.TEACHER_UPDATE,
        Permission.TEACHER_DELETE,
        Permission.TEACHER_LIST,
        Permission.TEACHER_SCHEDULE,
        
        # Class Management
        Permission.CLASS_CREATE,
        Permission.CLASS_READ,
        Permission.CLASS_UPDATE,
        Permission.CLASS_DELETE,
        Permission.CLASS_LIST,
        Permission.CLASS_ASSIGN_TEACHER,
        
        # Fee Management
        Permission.FEE_CREATE,
        Permission.FEE_READ,
        Permission.FEE_UPDATE,
        Permission.FEE_DELETE,
        Permission.FEE_LIST,
        Permission.FEE_PAYMENT,
        
        # Reports and Analytics
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EXPORT,
        Permission.ANALYTICS_VIEW,
        
        # Communication
        Permission.COMMUNICATION_SEND,
        Permission.COMMUNICATION_READ,
        Permission.COMMUNICATION_BROADCAST,
        
        # CRM
        Permission.CRM_CREATE,
        Permission.CRM_READ,
        Permission.CRM_UPDATE,
        Permission.CRM_DELETE,
        Permission.CRM_LIST,
        Permission.CRM_CONVERT_LEAD,
        
        # CMS
        Permission.CMS_CREATE,
        Permission.CMS_READ,
        Permission.CMS_UPDATE,
        Permission.CMS_DELETE,
        Permission.CMS_LIST,
        Permission.CMS_PUBLISH,
        
        # Events
        Permission.EVENT_CREATE,
        Permission.EVENT_READ,
        Permission.EVENT_UPDATE,
        Permission.EVENT_DELETE,
        Permission.EVENT_LIST,
        
        # Transport
        Permission.TRANSPORT_CREATE,
        Permission.TRANSPORT_READ,
        Permission.TRANSPORT_UPDATE,
        Permission.TRANSPORT_DELETE,
        Permission.TRANSPORT_LIST,
        
        # Hostel
        Permission.HOSTEL_CREATE,
        Permission.HOSTEL_READ,
        Permission.HOSTEL_UPDATE,
        Permission.HOSTEL_DELETE,
        Permission.HOSTEL_LIST,
        
        # Library
        Permission.LIBRARY_CREATE,
        Permission.LIBRARY_READ,
        Permission.LIBRARY_UPDATE,
        Permission.LIBRARY_DELETE,
        Permission.LIBRARY_LIST,
    },
    
    UserRole.TEACHER: {
        # Student Management (Limited)
        Permission.STUDENT_READ,
        Permission.STUDENT_LIST,
        Permission.STUDENT_GRADES,
        Permission.STUDENT_ATTENDANCE,
        
        # Class Management (Limited)
        Permission.CLASS_READ,
        Permission.CLASS_LIST,
        
        # Assignment Management
        Permission.ASSIGNMENT_CREATE,
        Permission.ASSIGNMENT_READ,
        Permission.ASSIGNMENT_UPDATE,
        Permission.ASSIGNMENT_DELETE,
        Permission.ASSIGNMENT_LIST,
        Permission.ASSIGNMENT_GRADE,
        
        # Exam Management
        Permission.EXAM_CREATE,
        Permission.EXAM_READ,
        Permission.EXAM_UPDATE,
        Permission.EXAM_DELETE,
        Permission.EXAM_LIST,
        Permission.EXAM_GRADE,
        
        # Live Classes
        Permission.LIVE_CLASS_CREATE,
        Permission.LIVE_CLASS_READ,
        Permission.LIVE_CLASS_UPDATE,
        Permission.LIVE_CLASS_DELETE,
        Permission.LIVE_CLASS_LIST,
        Permission.LIVE_CLASS_HOST,
        
        # Communication
        Permission.COMMUNICATION_SEND,
        Permission.COMMUNICATION_READ,
        
        # Library (Limited)
        Permission.LIBRARY_READ,
        Permission.LIBRARY_LIST,
        
        # Reports (Limited)
        Permission.REPORT_VIEW,
        
        # Teacher-specific
        Permission.TEACHER_READ,
        Permission.TEACHER_SCHEDULE,
    },
    
    UserRole.STUDENT: {
        # Student self-management
        Permission.STUDENT_READ,  # Only own profile
        
        # Assignments
        Permission.ASSIGNMENT_READ,
        Permission.ASSIGNMENT_LIST,
        Permission.ASSIGNMENT_SUBMIT,
        
        # Exams
        Permission.EXAM_READ,
        Permission.EXAM_LIST,
        Permission.EXAM_TAKE,
        
        # Live Classes
        Permission.LIVE_CLASS_READ,
        Permission.LIVE_CLASS_LIST,
        Permission.LIVE_CLASS_JOIN,
        
        # Library
        Permission.LIBRARY_READ,
        Permission.LIBRARY_LIST,
        Permission.LIBRARY_BORROW,
        Permission.LIBRARY_RETURN,
        
        # Events
        Permission.EVENT_READ,
        Permission.EVENT_LIST,
        Permission.EVENT_REGISTER,
        
        # Communication
        Permission.COMMUNICATION_READ,
        
        # CMS (Public content)
        Permission.CMS_READ,
        
        # Class Information
        Permission.CLASS_READ,
        Permission.CLASS_LIST,
    },
    
    UserRole.PARENT: {
        # Student information (for their children only)
        Permission.STUDENT_READ,
        Permission.STUDENT_GRADES,
        Permission.STUDENT_ATTENDANCE,
        
        # Fee Management
        Permission.FEE_READ,
        Permission.FEE_LIST,
        Permission.FEE_PAYMENT,
        
        # Communication
        Permission.COMMUNICATION_READ,
        Permission.COMMUNICATION_SEND,
        
        # Events
        Permission.EVENT_READ,
        Permission.EVENT_LIST,
        Permission.EVENT_REGISTER,
        
        # CMS (Public content)
        Permission.CMS_READ,
        
        # Class Information
        Permission.CLASS_READ,
        Permission.CLASS_LIST,
        
        # Transport (if applicable)
        Permission.TRANSPORT_READ,
        
        # Hostel (if applicable)
        Permission.HOSTEL_READ,
    },
    
    UserRole.STAFF: {
        # Limited administrative permissions
        Permission.STUDENT_READ,
        Permission.STUDENT_LIST,
        Permission.TEACHER_READ,
        Permission.TEACHER_LIST,
        Permission.CLASS_READ,
        Permission.CLASS_LIST,
        Permission.COMMUNICATION_SEND,
        Permission.COMMUNICATION_READ,
        Permission.EVENT_READ,
        Permission.EVENT_LIST,
        Permission.CMS_READ,
    },
    
    UserRole.GUEST: {
        # Very limited permissions for public access
        Permission.CMS_READ,
        Permission.EVENT_READ,
        Permission.EVENT_LIST,
    }
}


def get_user_permissions(role: UserRole) -> Set[Permission]:
    """
    Get permissions for a specific role
    
    Args:
        role: User role
    
    Returns:
        Set of permissions for the role
    """
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(user_role: UserRole, required_permission: Permission) -> bool:
    """
    Check if a user role has a specific permission
    
    Args:
        user_role: User's role
        required_permission: Permission to check
    
    Returns:
        True if user has permission, False otherwise
    """
    user_permissions = get_user_permissions(user_role)
    return required_permission in user_permissions


def require_permission(required_permission: Permission):
    """
    Decorator factory to require specific permission
    
    Args:
        required_permission: Permission required to access the endpoint
    
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This will be used in dependency injection
            # The actual permission check will be done in the dependency
            return func(*args, **kwargs)
        
        wrapper._required_permission = required_permission
        return wrapper
    
    return decorator


def check_permission(user_role: UserRole, required_permission: Permission):
    """
    Check permission and raise HTTPException if not authorized
    
    Args:
        user_role: User's role
        required_permission: Required permission
    
    Raises:
        HTTPException: If user doesn't have required permission
    """
    if not has_permission(user_role, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {required_permission.value}"
        )


def get_accessible_student_ids(user_role: UserRole, user_id: int, children_ids: List[int] = None) -> List[int]:
    """
    Get list of student IDs that a user can access based on their role
    
    Args:
        user_role: User's role
        user_id: User's ID
        children_ids: List of children IDs (for parents)
    
    Returns:
        List of accessible student IDs
    """
    if user_role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        return []  # Empty list means access to all students
    elif user_role == UserRole.TEACHER:
        return []  # Teachers can access all students in their classes (handled in service layer)
    elif user_role == UserRole.STUDENT:
        return [user_id]  # Students can only access their own data
    elif user_role == UserRole.PARENT:
        return children_ids or []  # Parents can access their children's data
    else:
        return []  # No access for other roles


def is_resource_owner(user_id: int, resource_user_id: int, user_role: UserRole) -> bool:
    """
    Check if user is the owner of a resource or has administrative access
    
    Args:
        user_id: Current user's ID
        resource_user_id: ID of the user who owns the resource
        user_role: Current user's role
    
    Returns:
        True if user can access the resource, False otherwise
    """
    # Admins can access all resources
    if user_role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        return True
    
    # Users can access their own resources
    return user_id == resource_user_id
