"""Authentication schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.permissions import UserRole

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: Optional[UserRole] = UserRole.STUDENT

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    firebase_uid: Optional[str] = None

    class Config:
        from_attributes = True

class RoleUpdateRequest(BaseModel):
    role: str

class FirebaseTokenRequest(BaseModel):
    idToken: str

class FirebaseAuthResponse(BaseModel):
    success: bool
    user: dict
    message: Optional[str] = None
