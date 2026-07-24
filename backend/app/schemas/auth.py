"""Authentication schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")
    remember_me: bool = Field(default=False, description="Extend session duration")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequest(BaseModel):
    email: str = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class UserMeResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    permissions: list[str]
    avatar_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True
