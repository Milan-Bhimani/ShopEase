"""
Authentication API routes.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from .utils import (
    hash_password, verify_password, create_access_token,
    generate_otp, store_otp, verify_otp, send_otp_email,
    create_verification_token, verify_verification_token, OTP_EXPIRY_MINUTES
)
from .dependencies import get_current_user
from ..models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    OTPRequest, OTPVerify, OTPResponse, OTPVerifyResponse
)
from ..firebase import user_repo

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate) -> Dict[str, Any]:
    """
    Register a new user account.

    Args:
        user_data: User registration data

    Returns:
        Access token and user info

    Raises:
        HTTPException: 400 if email already exists
    """
    # Check if email already exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user document
    user_doc = {
        "email": user_data.email.lower(),
        "password_hash": hash_password(user_data.password),
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone": user_data.phone,
        "is_active": True,
        "is_admin": False,
    }

    # Save to Firestore
    user_id = await user_repo.create(user_doc)

    # Create access token
    access_token = create_access_token(data={"sub": user_id})

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


@router.post("/pre-login")
async def pre_login(credentials: UserLogin) -> Dict[str, Any]:
    """
    Verify credentials and check if OTP is required.

    Args:
        credentials: Login credentials (email and password)

    Returns:
        Whether OTP is required for this user

    Raises:
        HTTPException: 401 if credentials invalid
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

    # Admin users skip OTP
    is_admin = user.get("is_admin", False)

    return {
        "require_otp": not is_admin,
        "email": user["email"]
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin) -> Dict[str, Any]:
    """
    Authenticate user and return access token.

    Args:
        credentials: Login credentials (email and password)

    Returns:
        Access token and user info

    Raises:
        HTTPException: 401 if credentials invalid
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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current authenticated user's profile.

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        User profile data
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


@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Logout user (client should discard token).

    Note: With JWT, actual invalidation requires a token blacklist.
    For simplicity, we return success and let client discard the token.

    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Refresh access token.

    Args:
        current_user: Current authenticated user

    Returns:
        New access token
    """
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


# OTP Routes

@router.post("/otp/send", response_model=OTPResponse)
async def send_otp(otp_request: OTPRequest) -> Dict[str, Any]:
    """
    Send OTP to email for verification.

    Args:
        otp_request: OTP request with email and purpose

    Returns:
        Success message with expiry time

    Raises:
        HTTPException: 400 if email already registered (for register purpose)
        HTTPException: 404 if email not found (for login purpose)
    """
    email = otp_request.email.lower()
    purpose = otp_request.purpose

    # For registration, check if email is already registered
    if purpose == "register":
        existing_user = await user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # For login, check if email exists
    if purpose == "login":
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

    # Generate and store OTP
    otp = generate_otp()
    store_otp(email, otp, purpose)

    # Send OTP email
    email_sent = await send_otp_email(email, otp, purpose)

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email"
        )

    return {
        "message": "OTP sent successfully",
        "email": email,
        "expires_in": OTP_EXPIRY_MINUTES * 60  # in seconds
    }


@router.post("/otp/verify", response_model=OTPVerifyResponse)
async def verify_otp_endpoint(otp_data: OTPVerify) -> Dict[str, Any]:
    """
    Verify OTP code.

    Args:
        otp_data: OTP verification data

    Returns:
        Verification status and token

    Raises:
        HTTPException: 400 if OTP is invalid or expired
    """
    email = otp_data.email.lower()
    otp = otp_data.otp
    purpose = otp_data.purpose

    # Verify OTP
    is_valid = verify_otp(email, otp, purpose)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    # Create verification token
    verification_token = create_verification_token(email, purpose)

    return {
        "verified": True,
        "message": "OTP verified successfully",
        "verification_token": verification_token
    }


@router.post("/otp/resend", response_model=OTPResponse)
async def resend_otp(otp_request: OTPRequest) -> Dict[str, Any]:
    """
    Resend OTP to email.

    This is essentially the same as send_otp but makes intent clearer.

    Args:
        otp_request: OTP request with email and purpose

    Returns:
        Success message with expiry time
    """
    return await send_otp(otp_request)
