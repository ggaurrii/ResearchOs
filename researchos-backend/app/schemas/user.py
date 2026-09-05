import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["student", "researcher", "mentor", "admin"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=150)
    role: Literal["student", "researcher", "mentor"] = "student"
    institution: Optional[str] = Field(default=None, max_length=200)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v) or not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter and one digit.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: Role
    institution: Optional[str] = None
    status: str
    email_verified_at: Optional[datetime] = None
    created_at: datetime


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    institution: Optional[str] = Field(default=None, max_length=200)


class RoleChangeRequest(BaseModel):
    role: Role


class StatusChangeRequest(BaseModel):
    status: Literal["active", "locked", "deactivated"]
