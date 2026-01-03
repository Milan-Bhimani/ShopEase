"""
Cart-related Pydantic models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class CartItemAdd(BaseModel):
    """Model for adding item to cart."""

    product_id: str = Field(..., description="Product ID to add")
    quantity: int = Field(1, ge=1, le=100, description="Quantity to add")


class CartItemUpdate(BaseModel):
    """Model for updating cart item quantity."""

    quantity: int = Field(..., ge=0, le=100, description="New quantity (0 to remove)")


class CartItemResponse(BaseModel):
    """Model for cart item in response."""

    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_image: Optional[str] = Field(None, description="Product thumbnail")
    price: float = Field(..., description="Unit price")
    quantity: int = Field(..., description="Quantity in cart")
    subtotal: float = Field(..., description="Line total (price * quantity)")
    in_stock: bool = Field(True, description="Product availability")
    stock_quantity: int = Field(0, description="Available stock")


class CartResponse(BaseModel):
    """Model for full cart response."""

    id: str = Field(..., description="Cart ID")
    user_id: str = Field(..., description="User ID")
    items: List[CartItemResponse] = Field(default_factory=list, description="Cart items")
    item_count: int = Field(0, description="Total number of items")
    subtotal: float = Field(0.0, description="Cart subtotal (tax included)")
    shipping: float = Field(0.0, description="Shipping cost")
    total: float = Field(0.0, description="Grand total")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class CartSummary(BaseModel):
    """Model for cart summary (header display)."""

    item_count: int = Field(0, description="Number of items")
    total: float = Field(0.0, description="Cart total")
