"""
User-related Pydantic models for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


class UserCreate(BaseModel):
    """Model for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    phone: Optional[str] = Field(None, max_length=15, description="Phone number")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Ensure password meets security requirements."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v
        # Remove spaces and dashes
        cleaned = re.sub(r"[\s\-]", "", v)
        if not re.match(r"^\+?[\d]{10,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned


class UserLogin(BaseModel):
    """Model for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Model for user response data (excludes sensitive info)."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    is_active: bool = Field(True, description="Account active status")
    created_at: Optional[str] = Field(None, description="Account creation timestamp")


class UserUpdate(BaseModel):
    """Model for updating user profile."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=15)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v
        cleaned = re.sub(r"[\s\-]", "", v)
        if not re.match(r"^\+?[\d]{10,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned


class PasswordChange(BaseModel):
    """Model for password change request."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Ensure new password meets security requirements."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class TokenResponse(BaseModel):
    """Model for authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    user: UserResponse = Field(..., description="User data")


class OTPRequest(BaseModel):
    """Model for OTP request."""

    email: EmailStr = Field(..., description="Email address to send OTP")
    purpose: str = Field(..., description="Purpose: 'register' or 'login'")

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        """Ensure purpose is valid."""
        if v not in ["register", "login"]:
            raise ValueError("Purpose must be 'register' or 'login'")
        return v


class OTPVerify(BaseModel):
    """Model for OTP verification."""

    email: EmailStr = Field(..., description="Email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    purpose: str = Field(..., description="Purpose: 'register' or 'login'")

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        """Ensure OTP is 6 digits."""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("OTP must be exactly 6 digits")
        return v


class OTPResponse(BaseModel):
    """Model for OTP send response."""

    message: str = Field(..., description="Status message")
    email: str = Field(..., description="Email address OTP was sent to")
    expires_in: int = Field(..., description="OTP expiry time in seconds")


class OTPVerifyResponse(BaseModel):
    """Model for OTP verification response."""

    verified: bool = Field(..., description="Whether OTP was verified")
    message: str = Field(..., description="Status message")
    verification_token: Optional[str] = Field(None, description="Token for subsequent auth")
