"""
==============================================================================
User Profile API Routes (users.py)
==============================================================================

PURPOSE:
--------
This module defines user profile management endpoints:
- View profile information
- Update profile details
- Change password
- Delete (deactivate) account

API ENDPOINTS:
--------------
GET    /users/profile         - Get current user's profile
PUT    /users/profile         - Update profile info
POST   /users/change-password - Change password
DELETE /users/account         - Deactivate account

PROFILE VS AUTH:
----------------
This module handles PROFILE operations (viewing/updating info).
Authentication operations (login, register, OTP) are in auth/routes.py.

Separation benefits:
- Clear responsibility boundaries
- Auth routes can be rate-limited differently
- Profile updates are less sensitive than auth operations

PASSWORD CHANGE:
----------------
Requires current password for verification.
This is a security measure - even with a valid token,
a stolen session can't change the password without knowing
the current one.

ACCOUNT DELETION:
-----------------
We use SOFT DELETE (is_active = False):
- User can't log in
- Data is preserved for audit/legal purposes
- Can be restored by admin if needed
- Orders, addresses, etc. remain intact

For GDPR compliance, a separate data export/deletion
process would be needed.

SECURITY:
---------
All endpoints require authentication.
Users can only access/modify their own profile.
Password hashes are never returned to the client.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from ..auth.dependencies import get_current_user
from ..auth.utils import hash_password, verify_password
from ..models.user import UserUpdate, UserResponse, PasswordChange
from ..firebase import user_repo

# Create router with prefix and tag for OpenAPI docs
router = APIRouter(prefix="/users", tags=["Users"])


# ==============================================================================
# USER PROFILE ENDPOINTS - All require authentication
# ==============================================================================

@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's profile.

    Returns user information excluding sensitive data
    (password hash is never returned).

    Returns:
        UserResponse with id, email, name, phone, status

    Example:
        GET /users/profile

    Response:
        {
            "id": "user123",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "9876543210",
            "is_active": true,
            "created_at": "2024-01-15T10:30:00"
        }
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


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update current user's profile.

    Partial update - only provided fields are changed.
    Email changes require separate verification flow.
    Password changes use the /change-password endpoint.

    Request Body:
        UserUpdate with optional first_name, last_name, phone

    Returns:
        Updated user profile

    Example:
        PUT /users/profile
        {"first_name": "Jane", "phone": "9123456789"}

    Note:
        Email cannot be changed through this endpoint.
        Email changes would require re-verification.
    """
    # Build update dictionary with only provided fields
    update_dict = {}
    if update_data.first_name is not None:
        update_dict["first_name"] = update_data.first_name
    if update_data.last_name is not None:
        update_dict["last_name"] = update_data.last_name
    if update_data.phone is not None:
        update_dict["phone"] = update_data.phone

    # Apply updates if any
    if update_dict:
        await user_repo.update(current_user["id"], update_dict)

    # Fetch and return updated user
    updated_user = await user_repo.get_by_id(current_user["id"])

    return {
        "id": updated_user["id"],
        "email": updated_user["email"],
        "first_name": updated_user.get("first_name", ""),
        "last_name": updated_user.get("last_name", ""),
        "phone": updated_user.get("phone", ""),
        "is_active": updated_user.get("is_active", True),
        "created_at": updated_user.get("created_at", ""),
    }


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Change user's password.

    Requires current password for verification.
    This prevents password changes with a stolen token.

    Request Body:
        {
            "current_password": "OldPass123",
            "new_password": "NewSecure456"
        }

    Returns:
        Success message

    Raises:
        400: Current password is incorrect

    Security:
        - Current password verification required
        - New password must meet strength requirements
        - Password is hashed with bcrypt before storage

    Note:
        After password change, existing tokens remain valid.
        To invalidate all sessions, implement token blacklisting.
    """
    # Verify current password matches stored hash
    if not verify_password(password_data.current_password, current_user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash new password and update
    new_hash = hash_password(password_data.new_password)
    await user_repo.update(current_user["id"], {"password_hash": new_hash})

    return {"message": "Password updated successfully"}


@router.delete("/account")
async def delete_account(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete user account (soft delete).

    Marks account as inactive (is_active = False).
    User will not be able to log in after this.
    Data is preserved for audit purposes.

    Returns:
        Success message

    Example:
        DELETE /users/account

    Note:
        This is a SOFT delete - data is not removed.
        For GDPR "right to be forgotten", additional
        data deletion would be required.

    Recovery:
        Account can be reactivated by admin by setting
        is_active = True in Firestore.
    """
    await user_repo.update(current_user["id"], {"is_active": False})
    return {"message": "Account has been deactivated"}
