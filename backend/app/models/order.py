"""
==============================================================================
Order Models (order.py)
==============================================================================

PURPOSE:
--------
This module defines Pydantic models for order management:
- Order creation and placement
- Order status tracking
- Payment information
- Order history display

ORDER LIFECYCLE:
----------------
1. PENDING: Order created, awaiting payment confirmation
2. CONFIRMED: Payment received, preparing for fulfillment
3. PROCESSING: Order being packed/prepared
4. SHIPPED: Handed to courier/delivery partner
5. OUT_FOR_DELIVERY: Last mile, on delivery vehicle
6. DELIVERED: Successfully delivered to customer
7. CANCELLED: Order cancelled (before shipping)
8. RETURNED: Customer returned the product
9. REFUNDED: Refund processed for cancelled/returned order

PAYMENT METHODS (India):
------------------------
- CARD: Credit/Debit card (via payment gateway)
- UPI: Unified Payment Interface (PhonePe, GPay, Paytm)
- NET_BANKING: Internet banking transfer
- WALLET: Digital wallets (Paytm, PhonePe wallet)
- COD: Cash on Delivery (pay when delivered)

IMPORTANT NOTES:
----------------
1. Never store real card numbers - only last 4 digits for reference
2. Actual payment processing would use Razorpay/Stripe
3. This app simulates payment (no real transactions)
4. GST is included in product prices (no separate tax calculation)

ORDER NUMBER FORMAT:
--------------------
SE-YYYYMMDD-XXXX
- SE: ShopEase prefix
- YYYYMMDD: Order date
- XXXX: Sequential counter

Example: SE-20240115-0042
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum


# ==============================================================================
# ENUMERATIONS
# ==============================================================================
class OrderStatus(str, Enum):
    """
    Order status enumeration.

    Inherits from str for JSON serialization.
    These values are stored in Firestore and displayed in UI.
    """
    PENDING = "pending"                    # Just created
    CONFIRMED = "confirmed"                # Payment verified
    PROCESSING = "processing"              # Being prepared
    SHIPPED = "shipped"                    # Handed to courier
    OUT_FOR_DELIVERY = "out_for_delivery"  # On the way
    DELIVERED = "delivered"                # Complete
    CANCELLED = "cancelled"                # User cancelled
    RETURNED = "returned"                  # Product returned
    REFUNDED = "refunded"                  # Money refunded


class PaymentMethod(str, Enum):
    """
    Payment method enumeration.

    Represents the payment methods available in the app.
    These match the checkout form options.
    """
    CARD = "card"              # Credit/Debit card
    UPI = "upi"                # UPI payment
    NET_BANKING = "net_banking"  # Internet banking
    WALLET = "wallet"          # Digital wallet
    COD = "cod"                # Cash on Delivery


class PaymentStatus(str, Enum):
    """
    Payment status enumeration.

    Tracks the payment lifecycle separate from order status.
    An order can be CONFIRMED but payment still PROCESSING.
    """
    PENDING = "pending"        # Awaiting payment
    PROCESSING = "processing"  # Payment being processed
    COMPLETED = "completed"    # Payment successful
    FAILED = "failed"          # Payment failed
    REFUNDED = "refunded"      # Payment refunded
    CANCELLED = "cancelled"    # Payment cancelled


# ==============================================================================
# PAYMENT INFO MODEL
# ==============================================================================
class PaymentInfo(BaseModel):
    """
    Model for payment information.

    Captures the payment method and related details.
    IMPORTANT: Never store sensitive card data!

    Example JSON (Card):
        {
            "method": "card",
            "card_last_four": "4242",
            "card_brand": "Visa"
        }

    Example JSON (UPI):
        {
            "method": "upi",
            "upi_id": "user@upi"
        }

    Example JSON (COD):
        {
            "method": "cod"
        }
    """

    # Payment method (required)
    method: PaymentMethod = Field(..., description="Payment method")

    # Card details (only for card payments)
    # WARNING: Never store full card numbers!
    card_last_four: Optional[str] = Field(
        None,
        max_length=4,
        description="Last 4 digits of card (for reference only)"
    )
    card_brand: Optional[str] = Field(
        None,
        description="Card brand (Visa, Mastercard, RuPay, etc.)"
    )

    # UPI details
    upi_id: Optional[str] = Field(
        None,
        description="UPI ID (e.g., user@upi, 9876543210@paytm)"
    )

    # Transaction details (set after payment processing)
    transaction_id: Optional[str] = Field(
        None,
        description="Payment gateway transaction ID"
    )

    @field_validator("card_last_four")
    @classmethod
    def validate_card_last_four(cls, v: Optional[str]) -> Optional[str]:
        """Ensure card last four is exactly 4 digits."""
        if v is not None and (len(v) != 4 or not v.isdigit()):
            raise ValueError("Card last four must be exactly 4 digits")
        return v


# ==============================================================================
# ORDER ITEM MODELS
# ==============================================================================
class OrderItemCreate(BaseModel):
    """
    Model for order item in creation request.

    Used when creating order with specific items
    (alternative to using cart contents).
    """

    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(
        ...,
        ge=1,    # At least 1
        le=100,  # Maximum 100
        description="Quantity to order"
    )


class OrderItemResponse(BaseModel):
    """
    Model for order item in response.

    Contains snapshot of product data at time of order.
    Price is locked at order time (not affected by later changes).

    Example JSON:
        {
            "product_id": "prod123",
            "product_name": "iPhone 15 Pro",
            "product_image": "https://...",
            "price": 129900,
            "quantity": 1,
            "subtotal": 129900
        }
    """

    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(
        ...,
        description="Product name (snapshot at order time)"
    )
    product_image: Optional[str] = Field(
        None,
        description="Product image URL"
    )
    price: float = Field(
        ...,
        description="Unit price at time of order (locked)"
    )
    quantity: int = Field(..., description="Quantity ordered")
    subtotal: float = Field(
        ...,
        description="Line total (price * quantity)"
    )


# ==============================================================================
# SHIPPING ADDRESS MODEL
# ==============================================================================
class ShippingAddress(BaseModel):
    """
    Model for shipping address in order.

    Embedded in order document as snapshot.
    Changes to user's addresses don't affect past orders.

    Example JSON:
        {
            "full_name": "John Doe",
            "phone": "9876543210",
            "address_line1": "123 Main Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "country": "India"
        }
    """

    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str


# ==============================================================================
# ORDER CREATE MODEL
# ==============================================================================
class OrderCreate(BaseModel):
    """
    Model for creating a new order.

    The order is typically created from cart contents,
    but items can be specified directly.

    Example JSON:
        {
            "address_id": "addr123",
            "payment": {
                "method": "upi",
                "upi_id": "user@upi"
            },
            "notes": "Please call before delivery"
        }
    """

    address_id: str = Field(
        ...,
        description="Shipping address ID (from user's saved addresses)"
    )
    payment: PaymentInfo = Field(
        ...,
        description="Payment method and details"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Order notes/special instructions"
    )
    # Items are typically taken from cart, but can be specified directly
    items: Optional[List[OrderItemCreate]] = Field(
        None,
        description="Order items (if not using cart contents)"
    )


# ==============================================================================
# ORDER RESPONSE MODEL
# ==============================================================================
class OrderResponse(BaseModel):
    """
    Model for order response.

    Complete order details including items, address, and totals.
    Used for order confirmation page, order details page, and email.

    Example JSON:
        {
            "id": "order123",
            "order_number": "SE-20240115-0042",
            "user_id": "user456",
            "items": [...],
            "shipping_address": {...},
            "status": "confirmed",
            "payment_method": "upi",
            "payment_status": "completed",
            "subtotal": 129900,
            "shipping_cost": 0,
            "discount": 0,
            "total": 129900,
            "estimated_delivery": "January 20, 2024"
        }
    """

    # Order identification
    id: str = Field(..., description="Order ID (Firestore document ID)")
    order_number: str = Field(
        ...,
        description="Human-readable order number (SE-YYYYMMDD-XXXX)"
    )
    user_id: str = Field(..., description="User who placed the order")

    # Order contents
    items: List[OrderItemResponse] = Field(
        ...,
        description="Ordered items with price snapshots"
    )
    shipping_address: ShippingAddress = Field(
        ...,
        description="Delivery address snapshot"
    )

    # Status
    status: OrderStatus = Field(..., description="Current order status")
    payment_method: PaymentMethod = Field(
        ...,
        description="Payment method used"
    )
    payment_status: PaymentStatus = Field(
        ...,
        description="Payment processing status"
    )

    # Pricing
    subtotal: float = Field(
        ...,
        description="Sum of item subtotals (GST included)"
    )
    shipping_cost: float = Field(
        0.0,
        description="Shipping charges (0 for free shipping)"
    )
    discount: float = Field(
        0.0,
        description="Discount applied (from coupons, promotions)"
    )
    total: float = Field(
        ...,
        description="Grand total (subtotal + shipping - discount)"
    )

    # Additional info
    notes: Optional[str] = Field(None, description="Customer notes")
    created_at: Optional[str] = Field(None, description="Order placed date")
    updated_at: Optional[str] = Field(None, description="Last status update")
    estimated_delivery: Optional[str] = Field(
        None,
        description="Estimated delivery date (formatted string)"
    )


# ==============================================================================
# ORDER LIST RESPONSE (Paginated)
# ==============================================================================
class OrderListResponse(BaseModel):
    """
    Model for paginated order list.

    Used for order history page.

    Example JSON:
        {
            "orders": [...],
            "total": 15,
            "page": 1,
            "per_page": 10
        }
    """

    orders: List[OrderResponse] = Field(..., description="Orders on page")
    total: int = Field(..., description="Total orders for user")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(10, description="Orders per page")


# ==============================================================================
# PAYMENT CONFIRMATION MODEL
# ==============================================================================
class PaymentConfirmation(BaseModel):
    """
    Model for payment confirmation response.

    Returned after successful payment processing.
    Used for the order confirmation page.

    Example JSON:
        {
            "success": true,
            "order_id": "order123",
            "order_number": "SE-20240115-0042",
            "transaction_id": "txn_abc123",
            "payment_method": "upi",
            "amount": 129900,
            "message": "Payment successful! Your order has been placed."
        }
    """

    success: bool = Field(..., description="Whether payment succeeded")
    order_id: str = Field(..., description="Order ID")
    order_number: str = Field(..., description="Order number for display")
    transaction_id: str = Field(
        ...,
        description="Payment transaction ID for reference"
    )
    payment_method: PaymentMethod = Field(..., description="Method used")
    amount: float = Field(..., description="Amount paid")
    message: str = Field(
        ...,
        description="Confirmation message for display"
    )
