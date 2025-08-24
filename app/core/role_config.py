"""
Role Configuration Service
Manages roles, permissions, and access control based on JSON configuration
"""
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class RoleConfigService:
    """Service for managing role-based access control configuration"""
    
    def __init__(self, config_path: str = "app/data/role_config.json"):
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load role configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"✅ Role configuration loaded from {self.config_path}")
            else:
                logger.warning(f"⚠️ Role config file not found: {self.config_path}")
                self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"❌ Failed to load role config: {str(e)}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file is missing"""
        return {
            "roles": {
                "super_admin": {
                    "name": "Super Administrator",
                    "description": "Full system access",
                    "permissions": ["all"],
                    "level": 100,
                    "color": "#dc2626",
                    "icon": "shield-check"
                },
                "admin": {
                    "name": "Administrator",
                    "description": "School administration",
                    "permissions": ["user_management", "academic_management"],
                    "level": 80,
                    "color": "#2563eb",
                    "icon": "academic-cap"
                },
                "teacher": {
                    "name": "Teacher",
                    "description": "Academic staff",
                    "permissions": ["class_management", "student_management"],
                    "level": 60,
                    "color": "#059669",
                    "icon": "academic-cap"
                },
                "parent": {
                    "name": "Parent",
                    "description": "Parent access",
                    "permissions": ["view_child_progress"],
                    "level": 40,
                    "color": "#7c3aed",
                    "icon": "user-group"
                },
                "student": {
                    "name": "Student",
                    "description": "Student access",
                    "permissions": ["view_assignments", "view_grades"],
                    "level": 20,
                    "color": "#ea580c",
                    "icon": "user"
                }
            },
            "modules": {},
            "default_roles": {
                "new_user": "student",
                "firebase_default": "student"
            },
            "role_hierarchy": {
                "super_admin": ["admin", "teacher", "parent", "student"],
                "admin": ["teacher", "parent", "student"],
                "teacher": ["parent", "student"],
                "parent": ["student"],
                "student": []
            }
        }
    
    def save_config(self) -> bool:
        """Save current configuration to JSON file"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Role configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save role config: {str(e)}")
            return False
    
    def get_roles(self) -> Dict[str, Any]:
        """Get all roles configuration"""
        return self._config.get("roles", {})
    
    def get_role(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Get specific role configuration"""
        return self._config.get("roles", {}).get(role_name)
    
    def get_modules(self) -> Dict[str, Any]:
        """Get all modules configuration"""
        return self._config.get("modules", {})
    
    def get_module(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get specific module configuration"""
        return self._config.get("modules", {}).get(module_name)
    
    def get_role_permissions(self, role_name: str) -> List[str]:
        """Get permissions for a specific role"""
        role = self.get_role(role_name)
        return role.get("permissions", []) if role else []
    
    def get_module_roles(self, module_name: str) -> List[str]:
        """Get roles that can access a specific module"""
        module = self.get_module(module_name)
        return module.get("roles", []) if module else []
    
    def can_access_module(self, user_role: str, module_name: str) -> bool:
        """Check if user role can access a specific module"""
        module_roles = self.get_module_roles(module_name)
        return user_role in module_roles
    
    def has_permission(self, user_role: str, permission: str) -> bool:
        """Check if user role has a specific permission"""
        role_permissions = self.get_role_permissions(user_role)
        return permission in role_permissions or "all" in role_permissions
    
    def get_default_role(self, context: str = "new_user") -> str:
        """Get default role for a context"""
        return self._config.get("default_roles", {}).get(context, "student")
    
    def get_role_for_email(self, email: str) -> str:
        """Get role for a specific email address"""
        # Check exact email mapping first
        email_mapping = self._config.get("email_role_mapping", {})
        if email in email_mapping:
            return email_mapping[email]
        
        # Check domain mapping
        domain_mapping = self._config.get("domain_role_mapping", {})
        for domain, role in domain_mapping.items():
            if email.endswith(domain):
                return role
        
        # Return default role
        return self.get_default_role("firebase_default")
    
    def get_role_hierarchy(self) -> Dict[str, List[str]]:
        """Get role hierarchy"""
        return self._config.get("role_hierarchy", {})
    
    def can_manage_role(self, manager_role: str, target_role: str) -> bool:
        """Check if manager role can manage target role"""
        hierarchy = self.get_role_hierarchy()
        manageable_roles = hierarchy.get(manager_role, [])
        return target_role in manageable_roles
    
    def update_role(self, role_name: str, role_config: Dict[str, Any]) -> bool:
        """Update role configuration (admin only)"""
        try:
            if role_name not in self._config.get("roles", {}):
                return False
            
            self._config["roles"][role_name].update(role_config)
            return self.save_config()
        except Exception as e:
            logger.error(f"❌ Failed to update role {role_name}: {str(e)}")
            return False
    
    def update_module(self, module_name: str, module_config: Dict[str, Any]) -> bool:
        """Update module configuration (admin only)"""
        try:
            if module_name not in self._config.get("modules", {}):
                return False
            
            self._config["modules"][module_name].update(module_config)
            return self.save_config()
        except Exception as e:
            logger.error(f"❌ Failed to update module {module_name}: {str(e)}")
            return False
    
    def get_role_info(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Get complete role information including permissions and access"""
        role = self.get_role(role_name)
        if not role:
            return None
        
        # Get modules this role can access
        accessible_modules = []
        for module_name, module_config in self.get_modules().items():
            if role_name in module_config.get("roles", []):
                accessible_modules.append({
                    "name": module_name,
                    "display_name": module_config.get("name", module_name),
                    "description": module_config.get("description", "")
                })
        
        return {
            **role,
            "accessible_modules": accessible_modules,
            "manageable_roles": self.get_role_hierarchy().get(role_name, [])
        }

# Global instance
role_config = RoleConfigService()
