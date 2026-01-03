"""
Order and Payment API routes.
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])

# Shipping settings (tax is included in product prices)
FREE_SHIPPING_THRESHOLD = 500.0
SHIPPING_COST = 40.0


def generate_order_number() -> str:
    """Generate a human-readable order number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"ORD-{timestamp}-{unique_id}"


def generate_transaction_id() -> str:
    """Generate a transaction ID for payment."""
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"


async def build_order_items(cart_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build order items from cart items with current product data."""
    order_items = []

    for item in cart_items:
        product = await product_repo.get_by_id(item["product_id"])
        if not product or not product.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {item['product_id']} is no longer available"
            )

        stock = product.get("stock_quantity", 0)
        if stock < item["quantity"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product.get('name')}. Only {stock} available."
            )

        price = product.get("price", 0)
        order_items.append({
            "product_id": item["product_id"],
            "product_name": product.get("name", "Unknown"),
            "product_image": product.get("thumbnail") or (product.get("images", [None])[0] if product.get("images") else None),
            "price": price,
            "quantity": item["quantity"],
            "subtotal": round(price * item["quantity"], 2),
        })

    return order_items


async def update_product_stock(order_items: List[Dict[str, Any]]) -> None:
    """Reduce product stock after order placement."""
    for item in order_items:
        product = await product_repo.get_by_id(item["product_id"])
        if product:
            new_stock = max(0, product.get("stock_quantity", 0) - item["quantity"])
            await product_repo.update(item["product_id"], {"stock_quantity": new_stock})


def format_order_response(order: Dict[str, Any]) -> Dict[str, Any]:
    """Format order for response."""
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


@router.get("", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all orders for current user.

    Returns:
        Paginated list of orders
    """
    orders = await order_repo.get_user_orders(current_user["id"])

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
    Get a specific order.

    Args:
        order_id: Order ID

    Returns:
        Order details
    """
    order = await order_repo.get_by_id(order_id)

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
    Create a new order from cart.

    Args:
        order_data: Order details (address, payment info)

    Returns:
        Payment confirmation with order details
    """
    # Get shipping address
    address = await address_repo.get_by_id(order_data.address_id)
    if not address or address.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid shipping address"
        )

    # Get cart items
    if order_data.items:
        # Use specified items
        cart_items = [{"product_id": i.product_id, "quantity": i.quantity} for i in order_data.items]
    else:
        # Use cart items
        cart = await cart_repo.get_user_cart(current_user["id"])
        if not cart or not cart.get("items"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        cart_items = cart.get("items", [])

    # Build order items and validate stock
    order_items = await build_order_items(cart_items)

    if not order_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid items in order"
        )

    # Calculate totals (tax included in prices)
    subtotal = sum(item["subtotal"] for item in order_items)
    shipping = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_COST
    total = round(subtotal + shipping, 2)

    # Generate identifiers
    order_number = generate_order_number()
    transaction_id = generate_transaction_id()

    # Determine payment status based on method
    if order_data.payment.method == PaymentMethod.COD:
        payment_status = PaymentStatus.PENDING
    else:
        # For card/UPI, simulate successful payment
        payment_status = PaymentStatus.COMPLETED

    # Prepare shipping address
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

    # Estimate delivery (5-7 business days)
    estimated_delivery = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")

    # Create order document
    order_doc = {
        "order_number": order_number,
        "user_id": current_user["id"],
        "items": order_items,
        "shipping_address": shipping_address,
        "status": OrderStatus.CONFIRMED,  # All orders confirmed immediately upon placement
        "payment_method": order_data.payment.method,
        "payment_status": payment_status,
        "transaction_id": transaction_id,
        "subtotal": subtotal,
        "shipping_cost": shipping,
        "discount": 0,
        "total": total,
        "notes": order_data.notes,
        "estimated_delivery": estimated_delivery,
    }

    # Save order
    order_id = await order_repo.create(order_doc)

    # Update product stock
    await update_product_stock(order_items)

    # Clear cart if order was from cart
    if not order_data.items:
        await cart_repo.clear_cart(current_user["id"])

    # Send order confirmation email
    try:
        order_doc["id"] = order_id
        user_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip() or 'Customer'
        email_service.send_order_confirmation(
            to_email=current_user.get('email', ''),
            order=order_doc,
            user_name=user_name
        )
    except Exception as e:
        logger.error(f"Failed to send order confirmation email: {e}")

    # Return payment confirmation
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
    Cancel an order (only if pending or confirmed).

    Args:
        order_id: Order ID

    Returns:
        Success message
    """
    order = await order_repo.get_by_id(order_id)

    if not order or order.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    current_status = order.get("status")
    if current_status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status: {current_status}"
        )

    # Update order status
    await order_repo.update(order_id, {
        "status": OrderStatus.CANCELLED,
        "payment_status": PaymentStatus.CANCELLED,
    })

    # Restore product stock
    for item in order.get("items", []):
        product = await product_repo.get_by_id(item["product_id"])
        if product:
            new_stock = product.get("stock_quantity", 0) + item["quantity"]
            await product_repo.update(item["product_id"], {"stock_quantity": new_stock})

    # Send order cancellation email
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

    Args:
        order_id: Order ID

    Returns:
        Tracking details
    """
    order = await order_repo.get_by_id(order_id)

    if not order or order.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    status = order.get("status", OrderStatus.PENDING)

    # Build tracking timeline
    timeline = [
        {
            "status": OrderStatus.PENDING,
            "label": "Order Placed",
            "completed": True,
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
            "timestamp": None,
        },
        {
            "status": OrderStatus.SHIPPED,
            "label": "Shipped",
            "completed": status in [OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED],
            "timestamp": None,
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
            "timestamp": None,
        },
    ]

    return {
        "order_id": order_id,
        "order_number": order.get("order_number"),
        "current_status": status,
        "estimated_delivery": order.get("estimated_delivery"),
        "timeline": timeline,
    }
