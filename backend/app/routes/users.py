"""
User profile API routes.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from ..auth.dependencies import get_current_user
from ..auth.utils import hash_password, verify_password
from ..models.user import UserUpdate, UserResponse, PasswordChange
from ..firebase import user_repo

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's profile.

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


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update current user's profile.

    Args:
        update_data: Fields to update

    Returns:
        Updated user profile
    """
    # Build update dictionary with only provided fields
    update_dict = {}
    if update_data.first_name is not None:
        update_dict["first_name"] = update_data.first_name
    if update_data.last_name is not None:
        update_dict["last_name"] = update_data.last_name
    if update_data.phone is not None:
        update_dict["phone"] = update_data.phone

    if update_dict:
        await user_repo.update(current_user["id"], update_dict)

    # Fetch updated user
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

    Args:
        password_data: Current and new password

    Returns:
        Success message
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash and update new password
    new_hash = hash_password(password_data.new_password)
    await user_repo.update(current_user["id"], {"password_hash": new_hash})

    return {"message": "Password updated successfully"}


@router.delete("/account")
async def delete_account(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete user account (soft delete - marks as inactive).

    Returns:
        Success message
    """
    await user_repo.update(current_user["id"], {"is_active": False})
    return {"message": "Account has been deactivated"}
