"""
Order and Payment related Pydantic models.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CARD = "card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    WALLET = "wallet"
    COD = "cod"  # Cash on Delivery


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentInfo(BaseModel):
    """Model for payment information."""

    method: PaymentMethod = Field(..., description="Payment method")
    # Card details (dummy - never store real card data)
    card_last_four: Optional[str] = Field(None, max_length=4, description="Last 4 digits of card")
    card_brand: Optional[str] = Field(None, description="Card brand (Visa, Mastercard, etc.)")
    # UPI details
    upi_id: Optional[str] = Field(None, description="UPI ID for UPI payments")
    # Transaction details
    transaction_id: Optional[str] = Field(None, description="Payment transaction ID")

    @field_validator("card_last_four")
    @classmethod
    def validate_card_last_four(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (len(v) != 4 or not v.isdigit()):
            raise ValueError("Card last four must be exactly 4 digits")
        return v


class OrderItemCreate(BaseModel):
    """Model for order item in creation request."""

    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(..., ge=1, le=100, description="Quantity")


class OrderCreate(BaseModel):
    """Model for creating a new order."""

    address_id: str = Field(..., description="Shipping address ID")
    payment: PaymentInfo = Field(..., description="Payment information")
    notes: Optional[str] = Field(None, max_length=500, description="Order notes")
    # Items are typically taken from cart, but can be specified directly
    items: Optional[List[OrderItemCreate]] = Field(None, description="Order items (if not from cart)")


class OrderItemResponse(BaseModel):
    """Model for order item in response."""

    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_image: Optional[str] = Field(None, description="Product image")
    price: float = Field(..., description="Unit price at time of order")
    quantity: int = Field(..., description="Quantity ordered")
    subtotal: float = Field(..., description="Line total")


class ShippingAddress(BaseModel):
    """Model for shipping address in order."""

    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str


class OrderResponse(BaseModel):
    """Model for order response."""

    id: str = Field(..., description="Order ID")
    order_number: str = Field(..., description="Human-readable order number")
    user_id: str = Field(..., description="User ID")
    items: List[OrderItemResponse] = Field(..., description="Order items")
    shipping_address: ShippingAddress = Field(..., description="Shipping address")
    status: OrderStatus = Field(..., description="Order status")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    payment_status: PaymentStatus = Field(..., description="Payment status")
    subtotal: float = Field(..., description="Items subtotal (tax included)")
    shipping_cost: float = Field(0.0, description="Shipping cost")
    discount: float = Field(0.0, description="Discount applied")
    total: float = Field(..., description="Grand total")
    notes: Optional[str] = Field(None, description="Order notes")
    created_at: Optional[str] = Field(None, description="Order creation time")
    updated_at: Optional[str] = Field(None, description="Last update time")
    estimated_delivery: Optional[str] = Field(None, description="Estimated delivery date")


class OrderListResponse(BaseModel):
    """Model for paginated order list."""

    orders: List[OrderResponse] = Field(..., description="List of orders")
    total: int = Field(..., description="Total orders")
    page: int = Field(1, description="Current page")
    per_page: int = Field(10, description="Items per page")


class PaymentConfirmation(BaseModel):
    """Model for payment confirmation response."""

    success: bool = Field(..., description="Payment success status")
    order_id: str = Field(..., description="Order ID")
    order_number: str = Field(..., description="Order number")
    transaction_id: str = Field(..., description="Transaction ID")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    amount: float = Field(..., description="Amount paid")
    message: str = Field(..., description="Confirmation message")
