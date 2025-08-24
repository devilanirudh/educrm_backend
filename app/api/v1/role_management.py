"""
Role Management API
Admin interface for managing roles, permissions, and access control
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.core.role_config import role_config
from app.core.permissions import UserRole
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/roles")
async def get_all_roles(
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get all roles configuration (admin only)
    """
    try:
        roles = role_config.get_roles()
        return {
            "success": True,
            "roles": roles
        }
    except Exception as e:
        logger.error(f"❌ Failed to get roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get roles configuration"
        )

@router.get("/roles/{role_name}")
async def get_role_info(
    role_name: str,
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get specific role information (admin only)
    """
    try:
        role_info = role_config.get_role_info(role_name)
        if not role_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found"
            )
        
        return {
            "success": True,
            "role": role_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get role info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get role information"
        )

@router.put("/roles/{role_name}")
async def update_role(
    role_name: str,
    role_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Update role configuration (admin only)
    """
    try:
        # Check if admin can manage this role
        if not role_config.can_manage_role(current_admin.role.value, role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You cannot manage role '{role_name}'"
            )
        
        success = role_config.update_role(role_name, role_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update role '{role_name}'"
            )
        
        logger.info(f"✅ Role '{role_name}' updated by admin {current_admin.email}")
        
        return {
            "success": True,
            "message": f"Role '{role_name}' updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role"
        )

@router.get("/modules")
async def get_all_modules(
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get all modules configuration (admin only)
    """
    try:
        modules = role_config.get_modules()
        return {
            "success": True,
            "modules": modules
        }
    except Exception as e:
        logger.error(f"❌ Failed to get modules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get modules configuration"
        )

@router.put("/modules/{module_name}")
async def update_module(
    module_name: str,
    module_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Update module configuration (admin only)
    """
    try:
        success = role_config.update_module(module_name, module_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update module '{module_name}'"
            )
        
        logger.info(f"✅ Module '{module_name}' updated by admin {current_admin.email}")
        
        return {
            "success": True,
            "message": f"Module '{module_name}' updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update module: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update module"
        )

@router.get("/permissions/{role_name}")
async def get_role_permissions(
    role_name: str,
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get permissions for a specific role (admin only)
    """
    try:
        permissions = role_config.get_role_permissions(role_name)
        return {
            "success": True,
            "role": role_name,
            "permissions": permissions
        }
    except Exception as e:
        logger.error(f"❌ Failed to get role permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get role permissions"
        )

@router.get("/access/{module_name}")
async def get_module_access(
    module_name: str,
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get roles that can access a specific module (admin only)
    """
    try:
        roles = role_config.get_module_roles(module_name)
        return {
            "success": True,
            "module": module_name,
            "roles": roles
        }
    except Exception as e:
        logger.error(f"❌ Failed to get module access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get module access"
        )

@router.post("/check-access")
async def check_user_access(
    user_role: str,
    module_name: str,
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Check if a user role can access a specific module (admin only)
    """
    try:
        can_access = role_config.can_access_module(user_role, module_name)
        return {
            "success": True,
            "user_role": user_role,
            "module": module_name,
            "can_access": can_access
        }
    except Exception as e:
        logger.error(f"❌ Failed to check access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check access"
        )

@router.post("/check-permission")
async def check_user_permission(
    user_role: str,
    permission: str,
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Check if a user role has a specific permission (admin only)
    """
    try:
        has_permission = role_config.has_permission(user_role, permission)
        return {
            "success": True,
            "user_role": user_role,
            "permission": permission,
            "has_permission": has_permission
        }
    except Exception as e:
        logger.error(f"❌ Failed to check permission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check permission"
        )

@router.get("/hierarchy")
async def get_role_hierarchy(
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get role hierarchy (admin only)
    """
    try:
        hierarchy = role_config.get_role_hierarchy()
        return {
            "success": True,
            "hierarchy": hierarchy
        }
    except Exception as e:
        logger.error(f"❌ Failed to get role hierarchy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get role hierarchy"
        )

@router.post("/can-manage")
async def check_can_manage_role(
    manager_role: str,
    target_role: str,
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Check if a manager role can manage a target role (admin only)
    """
    try:
        can_manage = role_config.can_manage_role(manager_role, target_role)
        return {
            "success": True,
            "manager_role": manager_role,
            "target_role": target_role,
            "can_manage": can_manage
        }
    except Exception as e:
        logger.error(f"❌ Failed to check role management: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check role management"
        )

@router.get("/config")
async def get_full_config(
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get full role configuration (admin only)
    """
    try:
        return {
            "success": True,
            "config": {
                "roles": role_config.get_roles(),
                "modules": role_config.get_modules(),
                "hierarchy": role_config.get_role_hierarchy(),
                "defaults": role_config._config.get("default_roles", {}),
                "email_mapping": role_config._config.get("email_role_mapping", {}),
                "domain_mapping": role_config._config.get("domain_role_mapping", {})
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get full config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get configuration"
        )

@router.get("/email-mapping")
async def get_email_mapping(
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get email to role mapping (admin only)
    """
    try:
        return {
            "success": True,
            "email_mapping": role_config._config.get("email_role_mapping", {}),
            "domain_mapping": role_config._config.get("domain_role_mapping", {})
        }
    except Exception as e:
        logger.error(f"❌ Failed to get email mapping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get email mapping"
        )

@router.post("/email-mapping")
async def add_email_mapping(
    email_mapping: Dict[str, str],
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Add email to role mapping (admin only)
    """
    try:
        email = email_mapping.get("email")
        role = email_mapping.get("role")
        
        if not email or not role:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email and role are required"
            )
        
        # Validate role exists
        if role not in role_config.get_roles():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )
        
        # Add to email mapping
        if "email_role_mapping" not in role_config._config:
            role_config._config["email_role_mapping"] = {}
        
        role_config._config["email_role_mapping"][email] = role
        success = role_config.save_config()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save email mapping"
            )
        
        logger.info(f"✅ Email mapping added: {email} -> {role} by admin {current_admin.email}")
        
        return {
            "success": True,
            "message": f"Email mapping added: {email} -> {role}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to add email mapping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add email mapping"
        )

@router.delete("/email-mapping/{email}")
async def remove_email_mapping(
    email: str,
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Remove email to role mapping (admin only)
    """
    try:
        if "email_role_mapping" not in role_config._config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No email mappings found"
            )
        
        if email not in role_config._config["email_role_mapping"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email mapping not found: {email}"
            )
        
        removed_role = role_config._config["email_role_mapping"].pop(email)
        success = role_config.save_config()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save email mapping"
            )
        
        logger.info(f"✅ Email mapping removed: {email} -> {removed_role} by admin {current_admin.email}")
        
        return {
            "success": True,
            "message": f"Email mapping removed: {email} -> {removed_role}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to remove email mapping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove email mapping"
        )

@router.post("/check-email-role")
async def check_email_role(
    email_data: Dict[str, str],
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Check what role would be assigned to an email (admin only)
    """
    try:
        email = email_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email is required"
            )
        
        assigned_role = role_config.get_role_for_email(email)
        return {
            "success": True,
            "email": email,
            "assigned_role": assigned_role,
            "is_mapped": email in role_config._config.get("email_role_mapping", {})
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to check email role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check email role"
        )
