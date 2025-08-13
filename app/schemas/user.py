"""
User-related Pydantic schemas for request/response validation
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, validator
from app.core.permissions import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: Optional[str] = None
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.STUDENT
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None and len(v.replace('+', '').replace('-', '').replace(' ', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    profile_picture: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    notes: Optional[str] = None
    language_preference: Optional[str] = None
    timezone: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    profile_picture: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    language_preference: str
    timezone: str
    
    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    """Summary schema for user listings"""
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    profile_picture: Optional[str] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[dict] = None


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None
    role: Optional[str] = None


class PasswordReset(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class EmailVerification(BaseModel):
    """Email verification schema"""
    token: str


class UserPreferenceCreate(BaseModel):
    """Schema for creating user preferences"""
    preference_key: str
    preference_value: Optional[str] = None


class UserPreferenceUpdate(BaseModel):
    """Schema for updating user preferences"""
    preference_value: Optional[str] = None


class UserPreferenceResponse(BaseModel):
    """Schema for user preference response"""
    id: int
    user_id: int
    preference_key: str
    preference_value: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ParentBase(BaseModel):
    """Base parent schema"""
    occupation: Optional[str] = None
    workplace: Optional[str] = None
    work_phone: Optional[str] = None
    relationship_to_student: Optional[str] = None
    is_primary_contact: bool = True
    can_pickup_student: bool = True
    receives_notifications: bool = True


class ParentCreate(ParentBase):
    """Schema for creating parent profile"""
    user_id: int


class ParentUpdate(ParentBase):
    """Schema for updating parent profile"""
    pass


class ParentResponse(ParentBase):
    """Schema for parent response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    user: UserSummary
    
    class Config:
        from_attributes = True


class UserSessionResponse(BaseModel):
    """Schema for user session response"""
    id: int
    user_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    is_active: bool
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for paginated user list response"""
    users: List[UserSummary]
    total: int
    page: int
    per_page: int
    pages: int


class UserStatsResponse(BaseModel):
    """Schema for user statistics response"""
    total_users: int
    active_users: int
    verified_users: int
    users_by_role: dict
    recent_registrations: int
    recent_logins: int


class BulkUserCreate(BaseModel):
    """Schema for bulk user creation"""
    users: List[UserCreate]
    send_welcome_email: bool = True


class BulkUserResponse(BaseModel):
    """Schema for bulk user creation response"""
    created_users: List[UserResponse]
    failed_users: List[dict]
    total_created: int
    total_failed: int
