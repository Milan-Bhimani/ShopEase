"""
==============================================================================
Admin Dashboard API Routes (admin.py)
==============================================================================

PURPOSE:
--------
This module defines all admin-only API endpoints for the dashboard:
- Dashboard statistics (products, orders, users, revenue)
- Order management (view all, update status)
- User management (view all, toggle active status)
- Product management (view all including inactive, toggle visibility)

API ENDPOINTS:
--------------
Dashboard:
    GET  /admin/stats           - Dashboard statistics overview

Orders:
    GET  /admin/orders          - List all orders (paginated, filterable)
    GET  /admin/orders/{id}     - Get order details with customer info
    PUT  /admin/orders/{id}/status - Update order status

Users:
    GET  /admin/users           - List all users (paginated, searchable)
    GET  /admin/users/{id}      - Get user details with order stats
    PUT  /admin/users/{id}/status - Toggle user active status

Products:
    GET  /admin/products        - List all products (including inactive)
    PUT  /admin/products/{id}/toggle-active - Toggle product visibility

SECURITY:
---------
All endpoints require admin authentication via get_admin_user dependency.
This dependency:
1. Checks for valid JWT token
2. Verifies user exists
3. Confirms user has is_admin=True

Non-admins receive 403 Forbidden response.

PAGINATION:
-----------
List endpoints use offset-based pagination:
- page: Page number (1-indexed, default 1)
- per_page: Items per page (default 20, max 100)

Response includes:
- total: Total items matching query
- page: Current page
- per_page: Items per page
- has_more: Whether more pages exist
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, List, Optional

from ..auth.dependencies import get_admin_user
from ..models.admin import (
    AdminStatsResponse,
    AdminOrderResponse,
    AdminOrderListResponse,
    AdminOrderUser,
    AdminOrderItem,
    OrderStatusUpdate,
    AdminUserResponse,
    AdminUserListResponse,
    UserStatusUpdate,
    ProductToggleResponse,
)
from ..firebase import product_repo, order_repo, user_repo

# Create router with prefix and tag for OpenAPI docs
router = APIRouter(prefix="/admin", tags=["Admin"])


# ==============================================================================
# DASHBOARD STATISTICS
# ==============================================================================

@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    admin: dict = Depends(get_admin_user)
) -> AdminStatsResponse:
    """
    Get dashboard statistics overview.

    Returns counts and totals for the admin dashboard home page.
    All counts are calculated on-demand from Firestore.

    Requires admin authentication.

    Returns:
        AdminStatsResponse with:
        - total_products: Total products in database
        - active_products: Products with is_active=True
        - total_orders: Total orders placed
        - total_users: Total registered users
        - active_users: Users with is_active=True
        - total_revenue: Sum of completed order totals (INR)
        - orders_by_status: Count per status
        - recent_orders: Orders in last 7 days
    """
    # Fetch all stats in parallel would be more efficient,
    # but for simplicity we fetch sequentially
    total_products = await product_repo.get_product_count()
    active_products = await product_repo.get_active_product_count()
    total_orders = await order_repo.get_order_count()
    total_users = await user_repo.get_user_count()
    active_users = await user_repo.get_active_user_count()
    total_revenue = await order_repo.get_total_revenue()
    orders_by_status = await order_repo.get_order_count_by_status()
    recent_orders = await order_repo.get_recent_orders_count(days=7)

    return AdminStatsResponse(
        total_products=total_products,
        active_products=active_products,
        total_orders=total_orders,
        total_users=total_users,
        active_users=active_users,
        total_revenue=total_revenue,
        orders_by_status=orders_by_status,
        recent_orders=recent_orders,
    )


# ==============================================================================
# ORDER MANAGEMENT
# ==============================================================================

@router.get("/orders", response_model=AdminOrderListResponse)
async def get_admin_orders(
    admin: dict = Depends(get_admin_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    search: Optional[str] = Query(None, description="Search by order number or email"),
) -> AdminOrderListResponse:
    """
    List all orders for admin dashboard.

    Supports pagination, status filtering, and search.
    Results are sorted by creation date (newest first).

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        status: Optional filter by order status
        search: Optional search term (order number or email)

    Returns:
        AdminOrderListResponse with paginated orders
    """
    # Get orders based on filters
    if search:
        all_orders = await order_repo.search_orders(search, limit=500)
    elif status:
        all_orders = await order_repo.get_all_orders(status=status, limit=500)
    else:
        all_orders = await order_repo.get_all_orders(limit=500)

    # Calculate pagination
    total = len(all_orders)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_orders = all_orders[start:end]
    has_more = end < total

    # Transform to response model
    order_responses = []
    for order in paginated_orders:
        # Fetch user info for each order
        user_info = None
        user_id = order.get("user_id")
        if user_id:
            user_data = await user_repo.get_by_id(user_id)
            if user_data:
                user_info = AdminOrderUser(
                    id=user_data.get("id", ""),
                    email=user_data.get("email", ""),
                    first_name=user_data.get("first_name", ""),
                    last_name=user_data.get("last_name", ""),
                    phone=user_data.get("phone"),
                )

        # Transform order items
        items = []
        for item in order.get("items", []):
            items.append(AdminOrderItem(
                product_id=item.get("product_id", ""),
                product_name=item.get("product_name", item.get("name", "")),
                product_image=item.get("product_image", item.get("image", item.get("thumbnail"))),
                price=float(item.get("price", 0)),
                quantity=int(item.get("quantity", 0)),
                subtotal=float(item.get("subtotal", item.get("price", 0) * item.get("quantity", 0))),
            ))

        order_responses.append(AdminOrderResponse(
            id=order.get("id", ""),
            order_number=order.get("order_number", ""),
            user=user_info,
            items=items,
            shipping_address=order.get("shipping_address"),
            status=order.get("status", "pending"),
            payment_method=order.get("payment_method"),
            payment_status=order.get("payment_status"),
            subtotal=float(order.get("subtotal", 0)),
            shipping_cost=float(order.get("shipping_cost", 0)),
            discount=float(order.get("discount", 0)),
            total=float(order.get("total", 0)),
            notes=order.get("notes"),
            created_at=order.get("created_at"),
            updated_at=order.get("updated_at"),
        ))

    return AdminOrderListResponse(
        orders=order_responses,
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.get("/orders/{order_id}", response_model=AdminOrderResponse)
async def get_admin_order(
    order_id: str,
    admin: dict = Depends(get_admin_user),
) -> AdminOrderResponse:
    """
    Get detailed order information including customer data.

    Args:
        order_id: Order document ID

    Returns:
        AdminOrderResponse with full order and customer details

    Raises:
        404: Order not found
    """
    order = await order_repo.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Fetch user info
    user_info = None
    user_id = order.get("user_id")
    if user_id:
        user_data = await user_repo.get_by_id(user_id)
        if user_data:
            user_info = AdminOrderUser(
                id=user_data.get("id", ""),
                email=user_data.get("email", ""),
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                phone=user_data.get("phone"),
            )

    # Transform order items
    items = []
    for item in order.get("items", []):
        items.append(AdminOrderItem(
            product_id=item.get("product_id", ""),
            product_name=item.get("product_name", item.get("name", "")),
            product_image=item.get("product_image", item.get("image", item.get("thumbnail"))),
            price=float(item.get("price", 0)),
            quantity=int(item.get("quantity", 0)),
            subtotal=float(item.get("subtotal", item.get("price", 0) * item.get("quantity", 0))),
        ))

    return AdminOrderResponse(
        id=order.get("id", ""),
        order_number=order.get("order_number", ""),
        user=user_info,
        items=items,
        shipping_address=order.get("shipping_address"),
        status=order.get("status", "pending"),
        payment_method=order.get("payment_method"),
        payment_status=order.get("payment_status"),
        subtotal=float(order.get("subtotal", 0)),
        shipping_cost=float(order.get("shipping_cost", 0)),
        discount=float(order.get("discount", 0)),
        total=float(order.get("total", 0)),
        notes=order.get("notes"),
        created_at=order.get("created_at"),
        updated_at=order.get("updated_at"),
    )


@router.put("/orders/{order_id}/status", response_model=AdminOrderResponse)
async def update_order_status(
    order_id: str,
    update: OrderStatusUpdate,
    admin: dict = Depends(get_admin_user),
) -> AdminOrderResponse:
    """
    Update order status.

    Admins can update status and optionally add notes.
    Status transitions are not strictly enforced but recommended:
    - pending -> confirmed, cancelled
    - confirmed -> processing, cancelled
    - processing -> shipped
    - shipped -> out_for_delivery
    - out_for_delivery -> delivered
    - delivered -> returned (if applicable)

    Args:
        order_id: Order document ID
        update: OrderStatusUpdate with new status and optional notes

    Returns:
        Updated AdminOrderResponse

    Raises:
        404: Order not found
    """
    # Verify order exists
    order = await order_repo.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Prepare update data
    update_data = {"status": update.status}
    if update.notes:
        # Append to existing notes or create new
        existing_notes = order.get("notes", "")
        if existing_notes:
            update_data["notes"] = f"{existing_notes}\n\n[{update.status}] {update.notes}"
        else:
            update_data["notes"] = f"[{update.status}] {update.notes}"

    # Update order
    await order_repo.update(order_id, update_data)

    # Return updated order
    return await get_admin_order(order_id, admin)


# ==============================================================================
# USER MANAGEMENT
# ==============================================================================

@router.get("/users", response_model=AdminUserListResponse)
async def get_admin_users(
    admin: dict = Depends(get_admin_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: active, inactive, admin"),
) -> AdminUserListResponse:
    """
    List all users for admin dashboard.

    Supports pagination and search.
    Results are sorted by registration date (newest first).

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        search: Optional search term (name or email)
        status_filter: Optional filter (active, inactive, admin)

    Returns:
        AdminUserListResponse with paginated users
    """
    # Get users based on filters
    if search:
        all_users = await user_repo.search_users(search, limit=500)
    else:
        all_users = await user_repo.get_all_users(limit=500)

    # Apply status filter
    if status_filter:
        if status_filter == "active":
            all_users = [u for u in all_users if u.get("is_active", True)]
        elif status_filter == "inactive":
            all_users = [u for u in all_users if not u.get("is_active", True)]
        elif status_filter == "admin":
            all_users = [u for u in all_users if u.get("is_admin", False)]

    # Calculate pagination
    total = len(all_users)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_users = all_users[start:end]
    has_more = end < total

    # Transform to response model with order stats
    user_responses = []
    for user in paginated_users:
        # Fetch order stats for user
        user_orders = await order_repo.get_user_orders(user.get("id", ""), limit=1000)
        order_count = len(user_orders)
        total_spent = sum(float(o.get("total", 0)) for o in user_orders)

        user_responses.append(AdminUserResponse(
            id=user.get("id", ""),
            email=user.get("email", ""),
            first_name=user.get("first_name", ""),
            last_name=user.get("last_name", ""),
            phone=user.get("phone"),
            is_active=user.get("is_active", True),
            is_admin=user.get("is_admin", False),
            order_count=order_count,
            total_spent=total_spent,
            created_at=user.get("created_at"),
            last_login=user.get("last_login"),
        ))

    return AdminUserListResponse(
        users=user_responses,
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_admin_user_detail(
    user_id: str,
    admin: dict = Depends(get_admin_user),
) -> AdminUserResponse:
    """
    Get detailed user information including order stats.

    Args:
        user_id: User document ID

    Returns:
        AdminUserResponse with user profile and order statistics

    Raises:
        404: User not found
    """
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Fetch order stats
    user_orders = await order_repo.get_user_orders(user_id, limit=1000)
    order_count = len(user_orders)
    total_spent = sum(float(o.get("total", 0)) for o in user_orders)

    return AdminUserResponse(
        id=user.get("id", ""),
        email=user.get("email", ""),
        first_name=user.get("first_name", ""),
        last_name=user.get("last_name", ""),
        phone=user.get("phone"),
        is_active=user.get("is_active", True),
        is_admin=user.get("is_admin", False),
        order_count=order_count,
        total_spent=total_spent,
        created_at=user.get("created_at"),
        last_login=user.get("last_login"),
    )


@router.put("/users/{user_id}/status", response_model=AdminUserResponse)
async def update_user_status(
    user_id: str,
    update: UserStatusUpdate,
    admin: dict = Depends(get_admin_user),
) -> AdminUserResponse:
    """
    Toggle user active status.

    Admins can activate or deactivate user accounts.
    Deactivated users cannot log in but their data is preserved.

    Security notes:
    - Admin users cannot be deactivated by other admins
    - Admins cannot deactivate themselves

    Args:
        user_id: User document ID
        update: UserStatusUpdate with new is_active status

    Returns:
        Updated AdminUserResponse

    Raises:
        400: Cannot deactivate admin user
        403: Cannot modify own account
        404: User not found
    """
    # Verify user exists
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from modifying their own status
    if user_id == admin.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify your own account status",
        )

    # Prevent deactivating other admins
    if user.get("is_admin", False) and not update.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate admin users",
        )

    # Update user status
    await user_repo.update(user_id, {"is_active": update.is_active})

    # Return updated user
    return await get_admin_user_detail(user_id, admin)


# ==============================================================================
# PRODUCT MANAGEMENT (Admin Extensions)
# ==============================================================================

@router.get("/products")
async def get_admin_products(
    admin: dict = Depends(get_admin_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by product name"),
    category: Optional[str] = Query(None, description="Filter by category"),
) -> Dict[str, Any]:
    """
    List all products including inactive ones.

    Unlike the public product listing which only shows active products,
    this endpoint returns ALL products for admin management.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        search: Optional search term
        category: Optional category filter

    Returns:
        Paginated product list with:
        - products: List of product objects
        - total: Total products matching query
        - page: Current page
        - per_page: Items per page
        - has_more: Whether more pages exist
    """
    # Get products based on filters
    if search:
        all_products = await product_repo.search_products_admin(
            search,
            category=category,
            limit=500
        )
    elif category:
        # Get by category, then include inactive
        all_products = await product_repo.get_all_with_inactive(limit=500)
        all_products = [p for p in all_products if p.get("category") == category]
    else:
        all_products = await product_repo.get_all_with_inactive(limit=500)

    # Calculate pagination
    total = len(all_products)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_products = all_products[start:end]
    has_more = end < total

    return {
        "products": paginated_products,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": has_more,
    }


@router.put("/products/{product_id}/toggle-active", response_model=ProductToggleResponse)
async def toggle_product_active(
    product_id: str,
    admin: dict = Depends(get_admin_user),
) -> ProductToggleResponse:
    """
    Toggle product visibility (active/inactive).

    Inactive products are hidden from the public catalog
    but preserved in the database for order history.

    Args:
        product_id: Product document ID

    Returns:
        ProductToggleResponse with new status

    Raises:
        404: Product not found
    """
    # Verify product exists
    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Toggle is_active
    current_status = product.get("is_active", True)
    new_status = not current_status
    await product_repo.update(product_id, {"is_active": new_status})

    # Return response
    status_text = "activated" if new_status else "deactivated"
    return ProductToggleResponse(
        id=product_id,
        is_active=new_status,
        message=f"Product {status_text} successfully",
    )
