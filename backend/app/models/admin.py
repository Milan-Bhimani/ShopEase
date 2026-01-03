"""
==============================================================================
Admin Dashboard Models (admin.py)
==============================================================================

PURPOSE:
--------
Pydantic models for admin-specific API operations.
These models handle dashboard statistics, order management with customer
details, and user management functionality.

MODELS:
-------
1. AdminStatsResponse - Dashboard statistics (counts, revenue)
2. AdminOrderUser - Customer info embedded in orders
3. AdminOrderItem - Order line item with product details
4. AdminOrderResponse - Full order with customer info
5. AdminOrderListResponse - Paginated order list
6. OrderStatusUpdate - Request to update order status
7. AdminUserResponse - User profile with order stats
8. AdminUserListResponse - Paginated user list
9. UserStatusUpdate - Request to toggle user active status

USAGE:
------
These models are used exclusively by admin endpoints in routes/admin.py.
All endpoints require admin authentication via get_admin_user dependency.

    from app.models.admin import AdminStatsResponse, OrderStatusUpdate

    @router.get("/admin/stats", response_model=AdminStatsResponse)
    async def get_stats(admin: dict = Depends(get_admin_user)):
        ...
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .order import OrderStatus, PaymentStatus, PaymentMethod


# ==============================================================================
# DASHBOARD STATISTICS
# ==============================================================================

class AdminStatsResponse(BaseModel):
    """
    Dashboard overview statistics.

    Provides counts and totals for the admin dashboard home page.
    All counts are calculated on-demand from Firestore.

    Attributes:
        total_products: Total number of products in database
        active_products: Products with is_active=True
        total_orders: Total number of orders placed
        total_users: Total registered users
        active_users: Users with is_active=True
        total_revenue: Sum of completed order totals (in INR)
        orders_by_status: Count of orders per status
        recent_orders: Number of orders in last 7 days

    Example Response:
        {
            "total_products": 50,
            "active_products": 48,
            "total_orders": 125,
            "total_users": 89,
            "active_users": 85,
            "total_revenue": 458750.00,
            "orders_by_status": {
                "pending": 5,
                "confirmed": 10,
                "processing": 8,
                "shipped": 15,
                "delivered": 80,
                "cancelled": 7
            },
            "recent_orders": 12
        }
    """
    total_products: int = Field(..., description="Total number of products")
    active_products: int = Field(..., description="Active products count")
    total_orders: int = Field(..., description="Total number of orders")
    total_users: int = Field(..., description="Total registered users")
    active_users: int = Field(..., description="Active users count")
    total_revenue: float = Field(..., description="Total revenue from completed orders (INR)")
    orders_by_status: Dict[str, int] = Field(
        default_factory=dict,
        description="Order count grouped by status"
    )
    recent_orders: int = Field(0, description="Orders placed in last 7 days")


# ==============================================================================
# ADMIN ORDER MODELS
# ==============================================================================

class AdminOrderUser(BaseModel):
    """
    Customer information embedded in admin order response.

    Provides essential customer details for order management
    without exposing sensitive data like password hashes.

    Attributes:
        id: User's Firestore document ID
        email: Customer's email address
        first_name: Customer's first name
        last_name: Customer's last name
        phone: Customer's phone number (optional)
    """
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="Customer email")
    first_name: str = Field(..., description="Customer first name")
    last_name: str = Field(..., description="Customer last name")
    phone: Optional[str] = Field(None, description="Customer phone")


class AdminOrderItem(BaseModel):
    """
    Order line item with product details.

    Represents a single product in an order with quantity and pricing.

    Attributes:
        product_id: Reference to product document
        product_name: Product name at time of order
        product_image: Product thumbnail URL
        price: Unit price at time of order (INR)
        quantity: Number of units ordered
        subtotal: price * quantity (INR)
    """
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_image: Optional[str] = Field(None, description="Product image URL")
    price: float = Field(..., description="Unit price (INR)")
    quantity: int = Field(..., description="Quantity ordered")
    subtotal: float = Field(..., description="Line subtotal (INR)")


class AdminOrderResponse(BaseModel):
    """
    Full order details for admin view.

    Includes customer information that regular users don't see.
    Used for order management and customer support.

    Attributes:
        id: Order document ID
        order_number: Human-readable order number (ORD-YYYYMMDD-XXXXX)
        user: Customer information
        items: List of order line items
        shipping_address: Delivery address details
        status: Current order status
        payment_method: Payment method used
        payment_status: Payment completion status
        subtotal: Sum of item subtotals (INR)
        shipping_cost: Delivery charges (INR)
        discount: Discount applied (INR)
        total: Final order total (INR)
        notes: Admin notes about the order
        created_at: Order placement timestamp
        updated_at: Last modification timestamp

    Example:
        {
            "id": "abc123",
            "order_number": "ORD-20240115-A1B2C",
            "user": {"id": "user123", "email": "customer@example.com", ...},
            "items": [...],
            "status": "processing",
            "total": 2999.00
        }
    """
    id: str = Field(..., description="Order ID")
    order_number: str = Field(..., description="Order number")
    user: Optional[AdminOrderUser] = Field(None, description="Customer info")
    items: List[AdminOrderItem] = Field(default_factory=list, description="Order items")
    shipping_address: Optional[Dict[str, Any]] = Field(None, description="Shipping address")
    status: str = Field(..., description="Order status")
    payment_method: Optional[str] = Field(None, description="Payment method")
    payment_status: Optional[str] = Field(None, description="Payment status")
    subtotal: float = Field(0, description="Subtotal (INR)")
    shipping_cost: float = Field(0, description="Shipping cost (INR)")
    discount: float = Field(0, description="Discount applied (INR)")
    total: float = Field(..., description="Order total (INR)")
    notes: Optional[str] = Field(None, description="Admin notes")
    created_at: Optional[str] = Field(None, description="Order creation time")
    updated_at: Optional[str] = Field(None, description="Last update time")


class AdminOrderListResponse(BaseModel):
    """
    Paginated list of orders for admin view.

    Attributes:
        orders: List of order summaries
        total: Total number of orders matching query
        page: Current page number
        per_page: Items per page
        has_more: Whether more pages exist
    """
    orders: List[AdminOrderResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total order count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(20, description="Items per page")
    has_more: bool = Field(False, description="More pages available")


class OrderStatusUpdate(BaseModel):
    """
    Request body for updating order status.

    Admins can update order status and optionally add notes.

    Attributes:
        status: New order status
        notes: Optional notes about the status change

    Example:
        {
            "status": "shipped",
            "notes": "Shipped via BlueDart, tracking: BD123456"
        }

    Valid Status Transitions:
        pending -> confirmed, cancelled
        confirmed -> processing, cancelled
        processing -> shipped
        shipped -> out_for_delivery
        out_for_delivery -> delivered
        delivered -> returned (if applicable)
    """
    status: str = Field(..., description="New order status")
    notes: Optional[str] = Field(None, description="Notes about status change")


# ==============================================================================
# ADMIN USER MODELS
# ==============================================================================

class AdminUserResponse(BaseModel):
    """
    User profile for admin view.

    Includes order statistics not available in regular user profile.
    Sensitive data (password_hash) is never exposed.

    Attributes:
        id: User document ID
        email: User's email address
        first_name: User's first name
        last_name: User's last name
        phone: User's phone number
        is_active: Account active status
        is_admin: Admin privilege flag
        order_count: Total number of orders placed
        total_spent: Total amount spent (INR)
        created_at: Account creation timestamp
        last_login: Last login timestamp (if tracked)

    Example:
        {
            "id": "user123",
            "email": "customer@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": true,
            "is_admin": false,
            "order_count": 5,
            "total_spent": 15000.00
        }
    """
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field("", description="First name")
    last_name: str = Field("", description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    is_active: bool = Field(True, description="Account active status")
    is_admin: bool = Field(False, description="Admin privileges")
    order_count: int = Field(0, description="Number of orders")
    total_spent: float = Field(0.0, description="Total amount spent (INR)")
    created_at: Optional[str] = Field(None, description="Account creation time")
    last_login: Optional[str] = Field(None, description="Last login time")


class AdminUserListResponse(BaseModel):
    """
    Paginated list of users for admin view.

    Attributes:
        users: List of user profiles
        total: Total number of users matching query
        page: Current page number
        per_page: Items per page
        has_more: Whether more pages exist
    """
    users: List[AdminUserResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total user count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(20, description="Items per page")
    has_more: bool = Field(False, description="More pages available")


class UserStatusUpdate(BaseModel):
    """
    Request body for updating user active status.

    Admins can activate or deactivate user accounts.
    Deactivated users cannot log in but their data is preserved.

    Attributes:
        is_active: New active status (True = active, False = deactivated)

    Example:
        {"is_active": false}

    Note:
        - Admin users cannot be deactivated by other admins
        - Deactivation is a soft action - account can be reactivated
        - User data and order history are preserved
    """
    is_active: bool = Field(..., description="New active status")


# ==============================================================================
# ADMIN PRODUCT MODELS
# ==============================================================================

class ProductToggleResponse(BaseModel):
    """
    Response after toggling product active status.

    Attributes:
        id: Product ID
        is_active: New active status
        message: Confirmation message
    """
    id: str = Field(..., description="Product ID")
    is_active: bool = Field(..., description="New active status")
    message: str = Field(..., description="Status message")
