"""
==============================================================================
Order and Payment API Routes (orders.py)
==============================================================================

PURPOSE:
--------
This module defines all order-related API endpoints:
- Create order from cart (checkout flow)
- List user's orders (order history)
- Get order details
- Cancel orders
- Track order status

API ENDPOINTS:
--------------
GET  /orders           - List user's orders (paginated)
GET  /orders/{id}      - Get order details
POST /orders           - Create new order (checkout)
POST /orders/{id}/cancel - Cancel an order
GET  /orders/{id}/track  - Get order tracking info

ORDER FLOW:
-----------
1. User adds items to cart
2. User selects shipping address
3. User selects payment method
4. POST /orders creates order:
   a. Validate cart items and stock
   b. Lock prices at order time
   c. Create order document
   d. Reduce product stock
   e. Clear user's cart
   f. Send confirmation email
5. Return PaymentConfirmation

PAYMENT SIMULATION:
-------------------
This app SIMULATES payment processing:
- Card/UPI: Instantly marked as COMPLETED
- COD: Marked as PENDING (collected on delivery)
- No real payment gateway integration

In production, you would:
1. Integrate Razorpay/Stripe/PayU
2. Create order with PENDING status
3. Redirect to payment gateway
4. Handle webhook for payment confirmation
5. Update order status on success

ORDER STATUSES:
---------------
PENDING -> CONFIRMED -> PROCESSING -> SHIPPED -> OUT_FOR_DELIVERY -> DELIVERED
                                   \-> CANCELLED (before shipping)
                                   \-> RETURNED -> REFUNDED

STOCK MANAGEMENT:
-----------------
- Stock is reduced immediately on order creation
- If order is cancelled, stock is restored
- This prevents overselling but may hold inventory

EMAIL NOTIFICATIONS:
--------------------
- Order confirmation: Sent on successful order
- Order cancellation: Sent when order is cancelled
- (Future: Shipping updates, delivery confirmation)
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid

from ..auth.dependencies import get_current_user
from ..models.order import (
    OrderCreate,
    OrderResponse,
    OrderListResponse,
    PaymentConfirmation,
    OrderStatus,
    PaymentStatus,
    PaymentMethod,
)
from ..firebase import order_repo, cart_repo, product_repo, address_repo, user_repo
from ..email import email_service
import logging

# Logger for error tracking
logger = logging.getLogger(__name__)

# Create router with prefix and tag for OpenAPI docs
router = APIRouter(prefix="/orders", tags=["Orders"])

# ==============================================================================
# SHIPPING CONFIGURATION
# ==============================================================================
# Same as cart.py - keep in sync
FREE_SHIPPING_THRESHOLD = 500.0
SHIPPING_COST = 40.0


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def generate_order_number() -> str:
    """
    Generate a human-readable order number.

    Format: ORD-YYYYMMDD-XXXXXXXX
    - ORD: Prefix for easy identification
    - YYYYMMDD: Order date
    - XXXXXXXX: 8 random hex chars for uniqueness

    Example: ORD-20240115-A3F2B1C9

    Returns:
        Unique order number string
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"ORD-{timestamp}-{unique_id}"


def generate_transaction_id() -> str:
    """
    Generate a transaction ID for payment.

    Format: TXN-XXXXXXXXXXXX (12 hex chars)
    Used for simulated payment tracking.

    In production, this would come from the payment gateway.

    Returns:
        Unique transaction ID string
    """
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"


async def build_order_items(cart_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build order items from cart items with current product data.

    This is the critical step that:
    1. Validates all products are still available
    2. Checks stock for each item
    3. Locks current prices into the order

    Args:
        cart_items: List of {product_id, quantity}

    Returns:
        List of order items with price snapshots

    Raises:
        400: Product unavailable or insufficient stock

    Note:
        Prices are captured here and won't change even if
        product prices are updated later.
    """
    order_items = []

    for item in cart_items:
        product = await product_repo.get_by_id(item["product_id"])

        # Validate product exists and is active
        if not product or not product.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {item['product_id']} is no longer available"
            )

        # Validate stock
        stock = product.get("stock_quantity", 0)
        if stock < item["quantity"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product.get('name')}. Only {stock} available."
            )

        # Lock price at order time
        price = product.get("price", 0)
        order_items.append({
            "product_id": item["product_id"],
            "product_name": product.get("name", "Unknown"),
            "product_image": product.get("thumbnail") or (product.get("images", [None])[0] if product.get("images") else None),
            "price": price,  # Price locked at this moment
            "quantity": item["quantity"],
            "subtotal": round(price * item["quantity"], 2),
        })

    return order_items


async def update_product_stock(order_items: List[Dict[str, Any]]) -> None:
    """
    Reduce product stock after order placement.

    Called after order is successfully created.
    Stock is reduced by the quantity ordered.

    Args:
        order_items: List of order items with quantity

    Note:
        Stock can't go below 0 (max() ensures this).
        If order is cancelled, stock is restored.
    """
    for item in order_items:
        product = await product_repo.get_by_id(item["product_id"])
        if product:
            new_stock = max(0, product.get("stock_quantity", 0) - item["quantity"])
            await product_repo.update(item["product_id"], {"stock_quantity": new_stock})


def format_order_response(order: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format raw order document for API response.

    Transforms Firestore document into OrderResponse-compatible dict.
    Provides defaults for missing fields.

    Args:
        order: Raw order document from Firestore

    Returns:
        Formatted order dict matching OrderResponse schema
    """
    return {
        "id": order["id"],
        "order_number": order.get("order_number", ""),
        "user_id": order.get("user_id", ""),
        "items": order.get("items", []),
        "shipping_address": order.get("shipping_address", {}),
        "status": order.get("status", OrderStatus.PENDING),
        "payment_method": order.get("payment_method", PaymentMethod.COD),
        "payment_status": order.get("payment_status", PaymentStatus.PENDING),
        "subtotal": order.get("subtotal", 0),
        "shipping_cost": order.get("shipping_cost", 0),
        "discount": order.get("discount", 0),
        "total": order.get("total", 0),
        "notes": order.get("notes"),
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at"),
        "estimated_delivery": order.get("estimated_delivery"),
    }


# ==============================================================================
# ORDER ENDPOINTS - All require authentication
# ==============================================================================

@router.get("", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all orders for current user (order history).

    Returns paginated list of orders sorted by creation date (newest first).
    Used for the "My Orders" page in user profile.

    Query Parameters:
        page: Page number (1-indexed)
        per_page: Orders per page (1-50)

    Returns:
        OrderListResponse with orders and pagination info

    Authorization:
        Requires authenticated user

    Example:
        GET /orders?page=1&per_page=10
    """
    # Fetch all orders for this user
    orders = await order_repo.get_user_orders(current_user["id"])

    # Calculate pagination
    total = len(orders)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = orders[start:end]

    return {
        "orders": [format_order_response(o) for o in paginated],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get details of a specific order.

    Returns full order information including:
    - All ordered items with prices
    - Shipping address snapshot
    - Payment and order status
    - Pricing breakdown

    Path Parameters:
        order_id: Firestore document ID

    Returns:
        Complete order details

    Raises:
        404: Order not found or belongs to another user

    Authorization:
        Users can only access their own orders

    Example:
        GET /orders/abc123xyz
    """
    order = await order_repo.get_by_id(order_id)

    # Security: Verify order belongs to current user
    if not order or order.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return format_order_response(order)


@router.post("", response_model=PaymentConfirmation, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new order (checkout flow).

    This is the main checkout endpoint that:
    1. Validates shipping address
    2. Gets items from cart (or specified items)
    3. Validates product availability and stock
    4. Locks prices at order time
    5. Creates order document
    6. Reduces product stock
    7. Clears user's cart
    8. Sends confirmation email

    Request Body:
        {
            "address_id": "addr123",
            "payment": {"method": "upi", "upi_id": "user@upi"},
            "notes": "Please call before delivery"
        }

    Returns:
        PaymentConfirmation with order_id, order_number, transaction_id

    Raises:
        400: Invalid address, empty cart, or stock issues

    Payment Methods:
        - card: Simulated instant payment (COMPLETED)
        - upi: Simulated instant payment (COMPLETED)
        - net_banking: Simulated instant payment (COMPLETED)
        - wallet: Simulated instant payment (COMPLETED)
        - cod: Payment pending (collected on delivery)

    Note:
        In production, card/UPI payments would redirect to
        a payment gateway and use webhooks for confirmation.
    """
    # Step 1: Validate shipping address belongs to user
    address = await address_repo.get_by_id(order_data.address_id)
    if not address or address.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid shipping address"
        )

    # Step 2: Get items to order
    if order_data.items:
        # Direct order (Buy Now) - use specified items
        cart_items = [{"product_id": i.product_id, "quantity": i.quantity} for i in order_data.items]
    else:
        # Cart checkout - use cart contents
        cart = await cart_repo.get_user_cart(current_user["id"])
        if not cart or not cart.get("items"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        cart_items = cart.get("items", [])

    # Step 3: Build order items (validates stock, locks prices)
    order_items = await build_order_items(cart_items)

    if not order_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid items in order"
        )

    # Step 4: Calculate totals
    subtotal = sum(item["subtotal"] for item in order_items)
    shipping = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_COST
    total = round(subtotal + shipping, 2)

    # Step 5: Generate identifiers
    order_number = generate_order_number()
    transaction_id = generate_transaction_id()

    # Step 6: Determine payment status
    # COD = pending (pay on delivery), others = simulated success
    if order_data.payment.method == PaymentMethod.COD:
        payment_status = PaymentStatus.PENDING
    else:
        payment_status = PaymentStatus.COMPLETED

    # Step 7: Snapshot shipping address (won't change if user updates address later)
    shipping_address = {
        "full_name": address.get("full_name"),
        "phone": address.get("phone"),
        "address_line1": address.get("address_line1"),
        "address_line2": address.get("address_line2"),
        "landmark": address.get("landmark"),
        "city": address.get("city"),
        "state": address.get("state"),
        "pincode": address.get("pincode"),
        "country": address.get("country", "India"),
    }

    # Step 8: Estimate delivery (7 days from now)
    estimated_delivery = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")

    # Step 9: Create order document
    order_doc = {
        "order_number": order_number,
        "user_id": current_user["id"],
        "items": order_items,
        "shipping_address": shipping_address,
        "status": OrderStatus.CONFIRMED,  # Skip PENDING - orders confirmed immediately
        "payment_method": order_data.payment.method,
        "payment_status": payment_status,
        "transaction_id": transaction_id,
        "subtotal": subtotal,
        "shipping_cost": shipping,
        "discount": 0,  # Coupon system not implemented
        "total": total,
        "notes": order_data.notes,
        "estimated_delivery": estimated_delivery,
    }

    # Step 10: Save order to Firestore
    order_id = await order_repo.create(order_doc)

    # Step 11: Reduce product stock
    await update_product_stock(order_items)

    # Step 12: Clear cart (only if order was from cart, not Buy Now)
    if not order_data.items:
        await cart_repo.clear_cart(current_user["id"])

    # Step 13: Send confirmation email (non-blocking)
    try:
        order_doc["id"] = order_id
        user_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip() or 'Customer'
        email_service.send_order_confirmation(
            to_email=current_user.get('email', ''),
            order=order_doc,
            user_name=user_name
        )
    except Exception as e:
        # Log but don't fail the order
        logger.error(f"Failed to send order confirmation email: {e}")

    # Step 14: Return payment confirmation
    return {
        "success": True,
        "order_id": order_id,
        "order_number": order_number,
        "transaction_id": transaction_id,
        "payment_method": order_data.payment.method,
        "amount": total,
        "message": "Order placed successfully!" if payment_status == PaymentStatus.COMPLETED else "Order placed. Payment will be collected on delivery.",
    }


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Cancel an order.

    Orders can only be cancelled if status is PENDING or CONFIRMED.
    Once an order is PROCESSING, SHIPPED, or DELIVERED, it cannot be cancelled.

    Cancellation process:
    1. Validate order belongs to user
    2. Check order is cancellable (status check)
    3. Update order status to CANCELLED
    4. Restore product stock (add back quantities)
    5. Send cancellation email

    Path Parameters:
        order_id: Order ID to cancel

    Returns:
        Success message

    Raises:
        404: Order not found or belongs to another user
        400: Order cannot be cancelled (already shipped/delivered)

    Example:
        POST /orders/abc123/cancel
    """
    order = await order_repo.get_by_id(order_id)

    # Security: Verify order belongs to current user
    if not order or order.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Check if order can be cancelled
    current_status = order.get("status")
    if current_status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status: {current_status}"
        )

    # Update order and payment status
    await order_repo.update(order_id, {
        "status": OrderStatus.CANCELLED,
        "payment_status": PaymentStatus.CANCELLED,
    })

    # Restore product stock (add back the ordered quantities)
    for item in order.get("items", []):
        product = await product_repo.get_by_id(item["product_id"])
        if product:
            new_stock = product.get("stock_quantity", 0) + item["quantity"]
            await product_repo.update(item["product_id"], {"stock_quantity": new_stock})

    # Send cancellation email (non-blocking)
    try:
        user_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip() or 'Customer'
        email_service.send_order_cancellation(
            to_email=current_user.get('email', ''),
            order=order,
            user_name=user_name
        )
    except Exception as e:
        logger.error(f"Failed to send order cancellation email: {e}")

    return {"message": "Order cancelled successfully"}


@router.get("/{order_id}/track")
async def track_order(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get order tracking information.

    Returns a timeline of order statuses showing:
    - Which steps are completed
    - Current status
    - Estimated delivery date

    Path Parameters:
        order_id: Order ID to track

    Returns:
        Tracking info with timeline

    Response Format:
        {
            "order_id": "abc123",
            "order_number": "ORD-20240115-XYZ",
            "current_status": "shipped",
            "estimated_delivery": "2024-01-22",
            "timeline": [
                {"status": "pending", "label": "Order Placed", "completed": true},
                {"status": "confirmed", "label": "Order Confirmed", "completed": true},
                {"status": "processing", "label": "Processing", "completed": true},
                {"status": "shipped", "label": "Shipped", "completed": true},
                {"status": "out_for_delivery", "label": "Out for Delivery", "completed": false},
                {"status": "delivered", "label": "Delivered", "completed": false}
            ]
        }

    Note:
        In production, this would integrate with courier APIs
        (Delhivery, BlueDart, etc.) for real-time tracking.
    """
    order = await order_repo.get_by_id(order_id)

    # Security: Verify order belongs to current user
    if not order or order.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    status = order.get("status", OrderStatus.PENDING)

    # Build tracking timeline with completion status
    # Each step is marked complete if current status is at or past that step
    timeline = [
        {
            "status": OrderStatus.PENDING,
            "label": "Order Placed",
            "completed": True,  # Always complete once order exists
            "timestamp": order.get("created_at"),
        },
        {
            "status": OrderStatus.CONFIRMED,
            "label": "Order Confirmed",
            "completed": status in [OrderStatus.CONFIRMED, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED],
            "timestamp": order.get("updated_at") if status != OrderStatus.PENDING else None,
        },
        {
            "status": OrderStatus.PROCESSING,
            "label": "Processing",
            "completed": status in [OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED],
            "timestamp": None,  # Would be populated by warehouse system
        },
        {
            "status": OrderStatus.SHIPPED,
            "label": "Shipped",
            "completed": status in [OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED],
            "timestamp": None,  # Would come from courier integration
        },
        {
            "status": OrderStatus.OUT_FOR_DELIVERY,
            "label": "Out for Delivery",
            "completed": status in [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED],
            "timestamp": None,
        },
        {
            "status": OrderStatus.DELIVERED,
            "label": "Delivered",
            "completed": status == OrderStatus.DELIVERED,
            "timestamp": None,  # Would be delivery confirmation time
        },
    ]

    return {
        "order_id": order_id,
        "order_number": order.get("order_number"),
        "current_status": status,
        "estimated_delivery": order.get("estimated_delivery"),
        "timeline": timeline,
    }
