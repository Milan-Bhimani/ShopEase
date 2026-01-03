"""
==============================================================================
User Models (user.py)
==============================================================================

PURPOSE:
--------
This module defines Pydantic models for user-related operations:
- User registration and authentication
- Profile management
- OTP verification

PYDANTIC FEATURES USED:
-----------------------
1. **Field**: Define field metadata (description, min/max length, etc.)
2. **EmailStr**: Validates email format automatically
3. **field_validator**: Custom validation logic for specific fields
4. **Optional**: Fields that can be None

VALIDATION PHILOSOPHY:
----------------------
- Fail fast: Reject invalid data immediately with clear error messages
- Security first: Enforce password requirements at the model level
- Consistency: Same validation rules for creation and updates

PASSWORD REQUIREMENTS:
----------------------
We enforce strong passwords to protect user accounts:
- Minimum 8 characters (prevents short, guessable passwords)
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
These rules balance security with usability.

PHONE NUMBER FORMAT:
--------------------
Accepts various formats, normalized to digits only:
- 1234567890 (10 digits minimum)
- +91 1234567890 (with country code)
- 123-456-7890 (with dashes, removed during normalization)
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


# ==============================================================================
# USER REGISTRATION MODEL
# ==============================================================================
class UserCreate(BaseModel):
    """
    Model for user registration.

    Used when creating a new user account. All required fields
    must be provided, and passwords must meet security requirements.

    Example JSON:
        {
            "email": "user@example.com",
            "password": "SecurePass123",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "9876543210"
        }
    """

    # Email uses EmailStr for automatic format validation
    # ... means field is required (no default value)
    email: EmailStr = Field(..., description="User email address")

    # Password has length constraints and custom validation
    password: str = Field(
        ...,
        min_length=8,   # Minimum 8 characters
        max_length=128, # Maximum to prevent DoS attacks
        description="User password"
    )

    # Name fields with reasonable length limits
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="First name"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Last name"
    )

    # Phone is optional (users can add later)
    phone: Optional[str] = Field(None, max_length=15, description="Phone number")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Ensure password meets security requirements.

        Checks for:
        - At least one uppercase letter (A-Z)
        - At least one lowercase letter (a-z)
        - At least one digit (0-9)

        These requirements are enforced at the model level to ensure
        all code paths creating users follow the same rules.

        Args:
            v: Password string to validate

        Returns:
            The password if valid

        Raises:
            ValueError: If password doesn't meet requirements
        """
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
        """
        Validate and normalize phone number.

        Accepts various formats:
        - 9876543210
        - +91 9876543210
        - 987-654-3210

        Normalizes to plain digits (with optional + prefix).

        Args:
            v: Phone number string (or None)

        Returns:
            Cleaned phone number with only digits

        Raises:
            ValueError: If phone format is invalid
        """
        if v is None:
            return v
        # Remove spaces and dashes for normalization
        cleaned = re.sub(r"[\s\-]", "", v)
        # Must be 10-15 digits, optionally starting with +
        if not re.match(r"^\+?[\d]{10,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned


# ==============================================================================
# USER LOGIN MODEL
# ==============================================================================
class UserLogin(BaseModel):
    """
    Model for user login.

    Contains only the fields needed for authentication.
    Validation is minimal here - actual credential verification
    happens in the auth routes.

    Example JSON:
        {
            "email": "user@example.com",
            "password": "SecurePass123"
        }
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


# ==============================================================================
# USER RESPONSE MODEL
# ==============================================================================
class UserResponse(BaseModel):
    """
    Model for user response data.

    This is returned from API endpoints and NEVER includes
    sensitive information like password_hash.

    Used in:
    - Profile endpoints
    - Token responses (embedded user data)
    - User listings (admin)
    """

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    is_active: bool = Field(True, description="Account active status")
    created_at: Optional[str] = Field(None, description="Account creation timestamp")


# ==============================================================================
# USER UPDATE MODEL
# ==============================================================================
class UserUpdate(BaseModel):
    """
    Model for updating user profile.

    All fields are optional - only provided fields are updated.
    Email and password have separate update flows for security.

    Example JSON (partial update):
        {
            "first_name": "Jane"
        }
    """

    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=15)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (same as UserCreate)."""
        if v is None:
            return v
        cleaned = re.sub(r"[\s\-]", "", v)
        if not re.match(r"^\+?[\d]{10,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned


# ==============================================================================
# PASSWORD CHANGE MODEL
# ==============================================================================
class PasswordChange(BaseModel):
    """
    Model for password change request.

    Requires current password for verification before allowing change.
    This prevents unauthorized password changes even with a valid token.

    Example JSON:
        {
            "current_password": "OldPass123",
            "new_password": "NewSecure456"
        }
    """

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password"
    )

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


# ==============================================================================
# AUTHENTICATION TOKEN RESPONSE
# ==============================================================================
class TokenResponse(BaseModel):
    """
    Model for authentication token response.

    Returned after successful login or registration.
    Includes both the JWT token and user data to avoid
    an additional API call to get user info.

    Example JSON:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer",
            "user": {
                "id": "abc123",
                "email": "user@example.com",
                ...
            }
        }
    """

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")
    user: UserResponse = Field(..., description="User data")


# ==============================================================================
# OTP REQUEST MODEL
# ==============================================================================
class OTPRequest(BaseModel):
    """
    Model for OTP request.

    Used when requesting a new OTP to be sent to email.
    The purpose field determines validation behavior:
    - "register": Email must NOT already be registered
    - "login": Email MUST be registered

    Example JSON:
        {
            "email": "user@example.com",
            "purpose": "login"
        }
    """

    email: EmailStr = Field(..., description="Email address to send OTP")
    purpose: str = Field(..., description="Purpose: 'register' or 'login'")

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        """Ensure purpose is a valid value."""
        if v not in ["register", "login"]:
            raise ValueError("Purpose must be 'register' or 'login'")
        return v


# ==============================================================================
# OTP VERIFICATION MODEL
# ==============================================================================
class OTPVerify(BaseModel):
    """
    Model for OTP verification.

    Sent when user enters the OTP they received via email.
    The OTP must be exactly 6 digits.

    Example JSON:
        {
            "email": "user@example.com",
            "otp": "123456",
            "purpose": "login"
        }
    """

    email: EmailStr = Field(..., description="Email address")
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit OTP code"
    )
    purpose: str = Field(..., description="Purpose: 'register' or 'login'")

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        """Ensure OTP is exactly 6 digits."""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("OTP must be exactly 6 digits")
        return v


# ==============================================================================
# OTP RESPONSE MODELS
# ==============================================================================
class OTPResponse(BaseModel):
    """
    Model for OTP send response.

    Returned when OTP is successfully sent.
    Includes expiry time so frontend can show countdown timer.

    Example JSON:
        {
            "message": "OTP sent successfully",
            "email": "user@example.com",
            "expires_in": 600
        }
    """

    message: str = Field(..., description="Status message")
    email: str = Field(..., description="Email address OTP was sent to")
    expires_in: int = Field(..., description="OTP expiry time in seconds")


class OTPVerifyResponse(BaseModel):
    """
    Model for OTP verification response.

    Returned after successful OTP verification.
    Includes a verification_token that can be used for
    subsequent actions (like completing registration).

    Example JSON:
        {
            "verified": true,
            "message": "OTP verified successfully",
            "verification_token": "eyJhbGci..."
        }
    """

    verified: bool = Field(..., description="Whether OTP was verified")
    message: str = Field(..., description="Status message")
    verification_token: Optional[str] = Field(
        None,
        description="Token for subsequent authentication (used in registration flow)"
    )
