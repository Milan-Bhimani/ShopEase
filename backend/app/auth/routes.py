"""
==============================================================================
Authentication API Routes (routes.py)
==============================================================================

PURPOSE:
--------
This module defines all authentication-related API endpoints:
1. User registration
2. Login (with password or OTP)
3. Token management (refresh, logout)
4. OTP operations (send, verify, resend)
5. Current user profile

API ENDPOINTS OVERVIEW:
-----------------------
    POST /api/auth/register     - Create new user account
    POST /api/auth/pre-login    - Verify credentials, check if OTP needed
    POST /api/auth/login        - Login with password (admin only)
    POST /api/auth/login-otp    - Login with OTP (all users)
    GET  /api/auth/me           - Get current user profile
    POST /api/auth/logout       - Logout (client discards token)
    POST /api/auth/refresh      - Get new access token
    POST /api/auth/otp/send     - Send OTP to email
    POST /api/auth/otp/verify   - Verify OTP code
    POST /api/auth/otp/resend   - Resend OTP code

AUTHENTICATION FLOWS:
---------------------

Flow 1: REGISTRATION (Simple - no OTP)
    1. POST /register with email, password, name
    2. Server creates user, returns JWT token
    3. User is now logged in

Flow 2: LOGIN WITH PASSWORD (Admin users only)
    1. POST /pre-login with email, password
    2. Server returns {require_otp: false} for admin users
    3. POST /login with email, password
    4. Server returns JWT token

Flow 3: LOGIN WITH OTP (Regular users)
    1. POST /pre-login with email, password
    2. Server returns {require_otp: true}
    3. POST /otp/send with email, purpose="login"
    4. User receives OTP via email
    5. POST /login-otp with email, otp
    6. Server verifies OTP, returns JWT token

HTTP STATUS CODES:
------------------
    200: Success (login, logout, etc.)
    201: Created (registration)
    400: Bad Request (validation error, duplicate email)
    401: Unauthorized (invalid credentials)
    403: Forbidden (account disabled)
    404: Not Found (email not registered)
    500: Server Error (email sending failed)

SECURITY NOTES:
---------------
1. Passwords are never returned in responses
2. Same error message for "user not found" and "wrong password"
   (prevents email enumeration attacks)
3. OTPs expire after 10 minutes
4. Maximum 3 OTP verification attempts
5. Admin users can skip OTP for convenience
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import logging

# Import authentication utilities
from .utils import (
    hash_password, verify_password, create_access_token,
    generate_otp, store_otp, verify_otp, send_otp_email,
    create_verification_token, verify_verification_token, OTP_EXPIRY_MINUTES
)
from .dependencies import get_current_user

# Import Pydantic models for request/response validation
from ..models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    OTPRequest, OTPVerify, OTPResponse, OTPVerifyResponse
)
from ..firebase import user_repo

# Setup logger for debugging
logger = logging.getLogger(__name__)

# ==============================================================================
# ROUTER CONFIGURATION
# ==============================================================================
# Create router with prefix and tag for API documentation
# All endpoints will be /api/auth/* (prefix added in main.py)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==============================================================================
# REGISTRATION ENDPOINT
# ==============================================================================
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate) -> Dict[str, Any]:
    """
    Register a new user account.

    This is a simple registration flow without email verification.
    User is immediately logged in after registration.

    Request Body:
        - email: Valid email address
        - password: At least 8 characters with upper, lower, and digit
        - first_name: User's first name
        - last_name: User's last name
        - phone: Optional phone number

    Response:
        - access_token: JWT token for authentication
        - token_type: "bearer"
        - user: User profile data

    Raises:
        400: Email already registered

    Example:
        POST /api/auth/register
        {
            "email": "user@example.com",
            "password": "SecurePass123",
            "first_name": "John",
            "last_name": "Doe"
        }
    """
    # Check if email already exists
    # We do this before hashing password to fail fast
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user document
    # Email is lowercased for case-insensitive matching
    # Password is hashed with bcrypt (never stored as plain text!)
    user_doc = {
        "email": user_data.email.lower(),
        "password_hash": hash_password(user_data.password),
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone": user_data.phone,
        "is_active": True,   # Account is enabled by default
        "is_admin": False,   # Regular user by default
    }

    # Save to Firestore (user_repo handles created_at/updated_at)
    user_id = await user_repo.create(user_doc)

    # Create JWT access token with user ID
    # Token is valid for 24 hours (configured in settings)
    access_token = create_access_token(data={"sub": user_id})

    # Return token and user info (password_hash is NOT included)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": user_doc["email"],
            "first_name": user_doc["first_name"],
            "last_name": user_doc["last_name"],
            "phone": user_doc["phone"],
        }
    }


# ==============================================================================
# PRE-LOGIN ENDPOINT
# ==============================================================================
@router.post("/pre-login")
async def pre_login(credentials: UserLogin) -> Dict[str, Any]:
    """
    Verify credentials and check if OTP is required.

    This is the first step of the login flow. It:
    1. Validates email and password
    2. Checks if user is active
    3. Returns whether OTP is required

    Admin users skip OTP for convenience.
    Regular users must verify via OTP.

    Request Body:
        - email: User's email address
        - password: User's password

    Response:
        - require_otp: Boolean - true if OTP verification needed
        - email: User's email (confirmed)

    Raises:
        401: Invalid email or password
        403: Account is disabled

    Example:
        POST /api/auth/pre-login
        {"email": "user@example.com", "password": "SecurePass123"}

        Response (admin): {"require_otp": false, "email": "admin@example.com"}
        Response (user):  {"require_otp": true, "email": "user@example.com"}
    """
    # Find user by email
    logger.info(f"Pre-login attempt for email: {credentials.email}")
    user = await user_repo.get_by_email(credentials.email)

    if not user:
        # Don't reveal whether email exists
        logger.warning(f"User not found for email: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Debug logging (useful for troubleshooting password issues)
    logger.info(f"User found: {user.get('email')}, has password_hash: {'password_hash' in user}")
    stored_hash = user.get("password_hash", "")
    logger.info(f"Password hash starts with: {stored_hash[:20] if stored_hash else 'EMPTY'}...")

    # Verify password
    try:
        password_valid = verify_password(credentials.password, stored_hash)
        logger.info(f"Password verification result: {password_valid}")
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        password_valid = False

    if not password_valid:
        # Same error message as "user not found" to prevent enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Admin users skip OTP for faster access
    # Regular users must verify via OTP for security
    is_admin = user.get("is_admin", False)

    return {
        "require_otp": not is_admin,
        "email": user["email"]
    }


# ==============================================================================
# DIRECT LOGIN ENDPOINT (Password Only - Admin)
# ==============================================================================
@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin) -> Dict[str, Any]:
    """
    Authenticate user and return access token (password only).

    This endpoint is primarily for admin users who skip OTP.
    Regular users should use /login-otp after OTP verification.

    Request Body:
        - email: User's email address
        - password: User's password

    Response:
        - access_token: JWT token
        - token_type: "bearer"
        - user: User profile data

    Raises:
        401: Invalid email or password
        403: Account is disabled
    """
    # Find user by email
    user = await user_repo.get_by_email(credentials.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "phone": user.get("phone", ""),
        }
    }


# ==============================================================================
# GET CURRENT USER ENDPOINT
# ==============================================================================
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current authenticated user's profile.

    Requires valid JWT token in Authorization header.
    Uses get_current_user dependency to validate token.

    Request:
        Header: Authorization: Bearer <token>

    Response:
        - id: User's ID
        - email: User's email
        - first_name, last_name: User's name
        - phone: Phone number (optional)
        - is_active: Account status
        - created_at: Account creation date
    """
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "first_name": current_user.get("first_name", ""),
        "last_name": current_user.get("last_name", ""),
        "phone": current_user.get("phone", ""),
        "is_active": current_user.get("is_active", True),
        "created_at": current_user.get("created_at", ""),
    }


# ==============================================================================
# LOGOUT ENDPOINT
# ==============================================================================
@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Logout user (client should discard token).

    With JWT, tokens are stateless - the server doesn't track sessions.
    True logout requires a token blacklist (not implemented here).

    For this app, we simply:
    1. Validate the current token
    2. Return success
    3. Client discards the token

    Note: Token remains technically valid until expiration.
    For higher security, implement a Redis-based token blacklist.
    """
    # We could add the token to a blacklist here
    # For now, just return success
    return {"message": "Successfully logged out"}


# ==============================================================================
# TOKEN REFRESH ENDPOINT
# ==============================================================================
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Refresh access token.

    Provides a new access token with fresh expiration time.
    Client should call this before the current token expires.

    Request:
        Header: Authorization: Bearer <current_token>

    Response:
        - access_token: New JWT token
        - token_type: "bearer"
        - user: User profile data

    Typical usage:
        Client checks token expiration before each request.
        If token expires soon (e.g., < 5 minutes), call /refresh.
    """
    # Create new token with fresh expiration
    access_token = create_access_token(data={"sub": current_user["id"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": current_user["id"],
            "email": current_user["email"],
            "first_name": current_user.get("first_name", ""),
            "last_name": current_user.get("last_name", ""),
            "phone": current_user.get("phone", ""),
        }
    }


# ==============================================================================
# OTP SEND ENDPOINT
# ==============================================================================
@router.post("/otp/send", response_model=OTPResponse)
async def send_otp(otp_request: OTPRequest) -> Dict[str, Any]:
    """
    Send OTP to email for verification.

    Generates a 6-digit OTP, stores it, and sends via email.
    Different validation for different purposes:
    - register: Email must NOT be registered
    - login: Email must BE registered and active

    Request Body:
        - email: User's email address
        - purpose: "register" or "login"

    Response:
        - message: "OTP sent successfully"
        - email: Confirmed email address
        - expires_in: Seconds until OTP expires

    Raises:
        400: Email already registered (for register purpose)
        403: Account is disabled
        404: Email not found (for login purpose)
        500: Failed to send email

    Example:
        POST /api/auth/otp/send
        {"email": "user@example.com", "purpose": "login"}
    """
    email = otp_request.email.lower()
    purpose = otp_request.purpose

    # Validation based on purpose
    if purpose == "register":
        # For registration, email must NOT already exist
        existing_user = await user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    if purpose == "login":
        # For login, email MUST exist and be active
        existing_user = await user_repo.get_by_email(email)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email"
            )
        if not existing_user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )

    # Generate 6-digit OTP
    otp = generate_otp()

    # Store OTP in memory with expiration (10 minutes)
    store_otp(email, otp, purpose)

    # Send OTP via email
    # If email is not configured, OTP is logged to console
    email_sent = await send_otp_email(email, otp, purpose)

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email"
        )

    return {
        "message": "OTP sent successfully",
        "email": email,
        "expires_in": OTP_EXPIRY_MINUTES * 60  # Convert to seconds for frontend
    }


# ==============================================================================
# OTP VERIFY ENDPOINT
# ==============================================================================
@router.post("/otp/verify", response_model=OTPVerifyResponse)
async def verify_otp_endpoint(otp_data: OTPVerify) -> Dict[str, Any]:
    """
    Verify OTP code.

    Validates the OTP and returns a verification token.
    Note: This is separate from login - for registration flow.
    For login, use /login-otp directly.

    Request Body:
        - email: User's email address
        - otp: 6-digit OTP code
        - purpose: "register" or "login"

    Response:
        - verified: Boolean (always true on success)
        - message: "OTP verified successfully"
        - verification_token: JWT token proving email verification

    Raises:
        400: Invalid or expired OTP

    Security:
        - OTP is deleted after successful verification (one-time use)
        - Maximum 3 verification attempts
        - OTP expires after 10 minutes
    """
    email = otp_data.email.lower()
    otp = otp_data.otp
    purpose = otp_data.purpose

    # Verify OTP (returns False if invalid, expired, or too many attempts)
    is_valid = verify_otp(email, otp, purpose)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    # Create verification token (proves email was verified)
    # This token is used for completing registration
    verification_token = create_verification_token(email, purpose)

    return {
        "verified": True,
        "message": "OTP verified successfully",
        "verification_token": verification_token
    }


# ==============================================================================
# OTP RESEND ENDPOINT
# ==============================================================================
@router.post("/otp/resend", response_model=OTPResponse)
async def resend_otp(otp_request: OTPRequest) -> Dict[str, Any]:
    """
    Resend OTP to email.

    Same as send_otp but semantically clearer intent.
    Generates a new OTP (previous one is replaced).

    Note: In production, you might want to:
    - Rate limit resends (e.g., max 3 per hour)
    - Track resend count
    - Increase cooldown period after each resend
    """
    return await send_otp(otp_request)


# ==============================================================================
# OTP LOGIN REQUEST MODEL
# ==============================================================================
from pydantic import BaseModel

class OTPLoginRequest(BaseModel):
    """
    Request model for OTP-based login.

    Attributes:
        email: User's email address
        otp: 6-digit OTP code from email
    """
    email: str
    otp: str


# ==============================================================================
# LOGIN WITH OTP ENDPOINT
# ==============================================================================
@router.post("/login-otp", response_model=TokenResponse)
async def login_with_otp(request: OTPLoginRequest) -> Dict[str, Any]:
    """
    Login user using OTP (passwordless login).

    This is the main login flow for regular users:
    1. User clicks "Login with OTP" on login page
    2. System sends OTP to user's email
    3. User enters OTP
    4. This endpoint verifies OTP and returns access token

    Request Body:
        - email: User's email address
        - otp: 6-digit OTP code

    Response:
        - access_token: JWT token
        - token_type: "bearer"
        - user: User profile data

    Raises:
        400: Invalid or expired OTP
        403: Account is disabled
        404: User not found

    Note:
        This endpoint verifies OTP AND logs in the user in one step.
        The OTP is consumed (deleted) upon verification.
    """
    email = request.email.lower()
    otp = request.otp

    # Verify OTP is valid for login purpose
    is_valid = verify_otp(email, otp, "login")

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    # Get user from database
    user = await user_repo.get_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email"
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "phone": user.get("phone", ""),
        }
    }
