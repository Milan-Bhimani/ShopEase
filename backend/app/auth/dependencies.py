"""
==============================================================================
Authentication Dependencies (dependencies.py)
==============================================================================

PURPOSE:
--------
This module provides FastAPI dependency injection functions for authentication.
These dependencies can be added to any route to:
1. Require authentication (get_current_user)
2. Optionally check authentication (get_current_user_optional)
3. Require admin privileges (get_admin_user)

WHAT ARE FASTAPI DEPENDENCIES?
------------------------------
Dependencies are reusable functions that:
- Run before the route handler
- Can inject data into the handler (like the current user)
- Can raise exceptions to block the request

By using Depends(), we avoid repeating authentication logic in every route.

AUTHENTICATION FLOW:
--------------------
1. Client includes "Authorization: Bearer <token>" header
2. HTTPBearer security scheme extracts the token
3. Dependency function decodes and validates the JWT
4. User is fetched from database to ensure they exist and are active
5. User data is passed to the route handler

EXAMPLE USAGE:
--------------
    from app.auth.dependencies import get_current_user, get_admin_user

    # Require any authenticated user
    @router.get("/profile")
    async def get_profile(current_user: dict = Depends(get_current_user)):
        return {"email": current_user["email"]}

    # Require admin user
    @router.delete("/users/{user_id}")
    async def delete_user(
        user_id: str,
        admin: dict = Depends(get_admin_user)
    ):
        # Only admins can reach this code
        pass

    # Optional authentication (works for both guests and logged-in users)
    @router.get("/products")
    async def list_products(
        user: dict | None = Depends(get_current_user_optional)
    ):
        if user:
            # Show personalized products
            pass
        else:
            # Show generic products
            pass

HTTP STATUS CODES:
------------------
- 401 Unauthorized: Not authenticated or invalid token
- 403 Forbidden: Authenticated but not authorized (e.g., not admin)
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .utils import decode_access_token
from ..firebase import user_repo

# ==============================================================================
# SECURITY SCHEME
# ==============================================================================
# HTTPBearer extracts the token from "Authorization: Bearer <token>" header
#
# auto_error=False means:
# - If header is missing, return None instead of raising 401
# - This allows us to have optional authentication routes
# - We handle the error ourselves for better error messages
security = HTTPBearer(auto_error=False)


# ==============================================================================
# REQUIRED AUTHENTICATION DEPENDENCY
# ==============================================================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user.

    This is the most commonly used auth dependency. It ensures:
    1. Request has a valid Bearer token
    2. Token can be decoded and hasn't expired
    3. User exists in the database
    4. User account is active (not disabled)

    Args:
        credentials: Automatically extracted from Authorization header
                    by the HTTPBearer security scheme

    Returns:
        User data dictionary from Firestore, including:
        - id: User's document ID
        - email: User's email address
        - first_name, last_name: User's name
        - is_admin: Whether user has admin privileges
        - is_active: Whether account is enabled
        - etc.

    Raises:
        HTTPException 401: If any authentication step fails
        HTTPException 403: If user account is disabled

    Example:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"message": f"Hello {user['email']}"}
    """
    # Check if Authorization header was provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},  # Standard OAuth2 header
        )

    # Extract token from "Bearer <token>"
    token = credentials.credentials

    # Decode and validate JWT
    # Returns None if token is invalid, expired, or malformed
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token payload
    # "sub" (subject) is the standard JWT claim for user identifier
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    # This ensures the user still exists (might have been deleted after token was issued)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active
    # Disabled accounts should not be able to access the API
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


# ==============================================================================
# OPTIONAL AUTHENTICATION DEPENDENCY
# ==============================================================================
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Dependency to optionally get the current user.

    Unlike get_current_user, this doesn't raise an exception if the user
    isn't authenticated. It returns None instead, allowing routes to
    handle both authenticated and unauthenticated requests.

    Use cases:
    - Show personalized content for logged-in users, generic for guests
    - Cart page that works for both guests and logged-in users
    - Product pages that show "Add to Wishlist" only for logged-in users

    Args:
        credentials: Optional bearer token from Authorization header

    Returns:
        User data dictionary if authenticated, None if not

    Example:
        @router.get("/products")
        async def list_products(
            user: dict | None = Depends(get_current_user_optional)
        ):
            if user:
                # Show products sorted by user's preferences
                return get_personalized_products(user)
            else:
                # Show default product listing
                return get_default_products()
    """
    # No token provided - user is not logged in
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)

    # Invalid token - treat as not authenticated (don't expose error details)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # Fetch user from database
    user = await user_repo.get_by_id(user_id)
    return user  # Can be None if user was deleted


# ==============================================================================
# ADMIN AUTHENTICATION DEPENDENCY
# ==============================================================================
async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to ensure the current user is an admin.

    This chains with get_current_user - first verifying authentication,
    then checking admin status. This is a clean pattern for layered
    authorization requirements.

    Use this for admin-only routes like:
    - Managing products (create, update, delete)
    - Viewing all orders
    - Managing users

    Args:
        current_user: Automatically injected from get_current_user dependency
                     (this happens before our code runs)

    Returns:
        User data if user is admin

    Raises:
        HTTPException 401: If not authenticated (from get_current_user)
        HTTPException 403: If user is not an admin

    Example:
        @router.post("/products")
        async def create_product(
            product: ProductCreate,
            admin: dict = Depends(get_admin_user)
        ):
            # Only admins can reach here
            return await product_repo.create(product.dict())
    """
    # Check if user has admin flag
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
