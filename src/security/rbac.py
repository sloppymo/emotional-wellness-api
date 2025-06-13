"""
Role-Based Access Control (RBAC) module for the Emotional Wellness API

This module implements:
- Role hierarchy and inheritance
- Permission management
- User-role assignment
- Access control verification
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """
    System permissions defining granular access capabilities
    """
    # Data access permissions
    READ_OWN_DATA = "read:own_data"
    READ_PATIENT_DATA = "read:patient_data"
    READ_ALL_DATA = "read:all_data"
    WRITE_OWN_DATA = "write:own_data"
    WRITE_PATIENT_DATA = "write:patient_data"
    
    # Clinical permissions
    VIEW_CLINICAL_DASHBOARD = "view:clinical_dashboard"
    PROVIDE_CLINICAL_NOTES = "write:clinical_notes"
    MANAGE_TREATMENT_PLANS = "manage:treatment_plans"
    
    # Administrative permissions
    MANAGE_USERS = "manage:users"
    MANAGE_ROLES = "manage:roles"
    MANAGE_SYSTEM_CONFIG = "manage:system_config"
    VIEW_AUDIT_LOGS = "view:audit_logs"
    
    # Crisis intervention permissions
    INITIATE_CRISIS_PROTOCOL = "initiate:crisis_protocol"
    MANAGE_CRISIS_CASES = "manage:crisis_cases"
    VIEW_CRISIS_DASHBOARD = "view:crisis_dashboard"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view:analytics"
    GENERATE_REPORTS = "generate:reports"
    EXPORT_DATA = "export:data"


class Role(BaseModel):
    """
    Role definition with associated permissions and hierarchy
    """
    id: str
    name: str
    description: str
    permissions: Set[Permission] = Field(default_factory=set)
    parent_roles: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserRole(BaseModel):
    """
    User-role assignment
    """
    user_id: str
    role_id: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class RoleManager:
    """
    Role management system for RBAC
    """
    def __init__(self):
        """Initialize with predefined system roles"""
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, List[UserRole]] = {}
        
        # Initialize system roles
        self._init_system_roles()
    
    def _init_system_roles(self):
        """Create default system roles with proper hierarchy"""
        # Base role with minimal permissions
        self.create_role(
            id="patient",
            name="Patient",
            description="Basic patient role with access to own data only",
            permissions={
                Permission.READ_OWN_DATA,
                Permission.WRITE_OWN_DATA
            }
        )
        
        # Therapist role
        self.create_role(
            id="therapist",
            name="Therapist",
            description="Clinical therapist with patient data access",
            permissions={
                Permission.READ_PATIENT_DATA,
                Permission.WRITE_PATIENT_DATA,
                Permission.VIEW_CLINICAL_DASHBOARD,
                Permission.PROVIDE_CLINICAL_NOTES,
                Permission.MANAGE_TREATMENT_PLANS,
                Permission.INITIATE_CRISIS_PROTOCOL,
                Permission.VIEW_CRISIS_DASHBOARD,
                Permission.VIEW_ANALYTICS,
                Permission.GENERATE_REPORTS
            }
        )
        
        # Clinical supervisor with expanded permissions
        self.create_role(
            id="clinical_supervisor",
            name="Clinical Supervisor",
            description="Senior clinical role with oversight capabilities",
            permissions={
                Permission.MANAGE_CRISIS_CASES,
                Permission.EXPORT_DATA
            },
            parent_roles=["therapist"]
        )
        
        # Admin role with system management
        self.create_role(
            id="admin",
            name="Administrator",
            description="System administrator with user management",
            permissions={
                Permission.MANAGE_USERS,
                Permission.MANAGE_ROLES,
                Permission.MANAGE_SYSTEM_CONFIG,
                Permission.VIEW_AUDIT_LOGS
            }
        )
        
        # Super admin with all permissions
        self.create_role(
            id="super_admin",
            name="Super Administrator",
            description="Complete system access with all permissions",
            permissions=set(Permission),
            parent_roles=["admin", "clinical_supervisor"]
        )
    
    def create_role(self, id: str, name: str, description: str,
                    permissions: Set[Permission], parent_roles: List[str] = None) -> Role:
        """
        Create a new role
        
        Args:
            id: Unique role identifier
            name: Human-readable role name
            description: Role description
            permissions: Set of permissions directly assigned to this role
            parent_roles: List of parent role IDs for permission inheritance
            
        Returns:
            The created role
        """
        if id in self.roles:
            raise ValueError(f"Role with ID {id} already exists")
            
        role = Role(
            id=id,
            name=name,
            description=description,
            permissions=permissions,
            parent_roles=parent_roles or []
        )
        
        self.roles[id] = role
        logger.info(f"Created role: {id} ({name})")
        return role
    
    def assign_role_to_user(self, user_id: str, role_id: str, 
                          assigned_by: Optional[str] = None,
                          expires_at: Optional[datetime] = None) -> UserRole:
        """
        Assign a role to a user
        
        Args:
            user_id: User identifier
            role_id: Role identifier
            assigned_by: ID of user who assigned this role
            expires_at: Optional expiration date for temporary role assignments
            
        Returns:
            The created user-role assignment
        """
        if role_id not in self.roles:
            raise ValueError(f"Role {role_id} does not exist")
            
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at
        )
        
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
            
        self.user_roles[user_id].append(user_role)
        logger.info(f"Assigned role {role_id} to user {user_id}")
        return user_role
    
    def get_user_roles(self, user_id: str) -> List[Role]:
        """
        Get all roles assigned to a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of roles assigned to the user
        """
        if user_id not in self.user_roles:
            return []
            
        # Filter out expired roles
        valid_roles = []
        for user_role in self.user_roles[user_id]:
            if user_role.expires_at is None or user_role.expires_at > datetime.utcnow():
                if user_role.role_id in self.roles:
                    valid_roles.append(self.roles[user_role.role_id])
        
        return valid_roles
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        Get all permissions for a user including inherited permissions
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of all permissions the user has
        """
        roles = self.get_user_roles(user_id)
        permissions = set()
        
        for role in roles:
            # Add direct permissions
            permissions.update(role.permissions)
            
            # Add inherited permissions
            permissions.update(self._get_inherited_permissions(role.id))
        
        return permissions
    
    def _get_inherited_permissions(self, role_id: str, visited: Set[str] = None) -> Set[Permission]:
        """
        Recursively get all inherited permissions for a role
        
        Args:
            role_id: Role identifier
            visited: Set of already visited roles (for cycle detection)
            
        Returns:
            Set of all inherited permissions
        """
        if visited is None:
            visited = set()
            
        if role_id in visited or role_id not in self.roles:
            return set()
            
        visited.add(role_id)
        role = self.roles[role_id]
        permissions = set(role.permissions)
        
        # Recursively add permissions from parent roles
        for parent_id in role.parent_roles:
            parent_permissions = self._get_inherited_permissions(parent_id, visited)
            permissions.update(parent_permissions)
            
        return permissions
    
    def has_permission(self, user_id: str, required_permission: Permission) -> bool:
        """
        Check if a user has a specific permission
        
        Args:
            user_id: User identifier
            required_permission: The permission to check
            
        Returns:
            True if the user has the permission, False otherwise
        """
        user_permissions = self.get_user_permissions(user_id)
        return required_permission in user_permissions
    
    def has_any_permission(self, user_id: str, required_permissions: List[Permission]) -> bool:
        """
        Check if user has any of the specified permissions
        
        Args:
            user_id: User identifier
            required_permissions: List of permissions to check
            
        Returns:
            True if the user has any of the permissions
        """
        user_permissions = self.get_user_permissions(user_id)
        return any(perm in user_permissions for perm in required_permissions)
    
    def has_all_permissions(self, user_id: str, required_permissions: List[Permission]) -> bool:
        """
        Check if user has all of the specified permissions
        
        Args:
            user_id: User identifier
            required_permissions: List of permissions to check
            
        Returns:
            True if the user has all of the permissions
        """
        user_permissions = self.get_user_permissions(user_id)
        return all(perm in user_permissions for perm in required_permissions)
    
    def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """
        Remove a role from a user
        
        Args:
            user_id: User identifier
            role_id: Role identifier
            
        Returns:
            True if the role was removed, False if not found
        """
        if user_id not in self.user_roles:
            return False
            
        initial_count = len(self.user_roles[user_id])
        self.user_roles[user_id] = [
            ur for ur in self.user_roles[user_id] 
            if ur.role_id != role_id
        ]
        
        removed = len(self.user_roles[user_id]) < initial_count
        if removed:
            logger.info(f"Removed role {role_id} from user {user_id}")
            
        return removed


# Create a global instance for use across the application
role_manager = RoleManager()
