"""
==============================================================================
Cart Models (cart.py)
==============================================================================

PURPOSE:
--------
This module defines Pydantic models for shopping cart operations:
- Adding items to cart
- Updating item quantities
- Cart display and totals

CART ARCHITECTURE:
------------------
Each user has one cart stored in Firestore:
    carts/{cart_id}:
        user_id: "user123"
        items: [
            {product_id: "prod1", quantity: 2, ...},
            {product_id: "prod2", quantity: 1, ...}
        ]
        updated_at: "2024-01-15T10:30:00"

CART OPERATIONS:
----------------
1. Add Item: Adds product with quantity (or increases existing)
2. Update Item: Changes quantity (0 = remove)
3. Remove Item: Deletes item from cart
4. Get Cart: Returns full cart with product details
5. Clear Cart: Empties cart (after order placement)

PRICE CALCULATIONS:
-------------------
Calculations happen on the backend for consistency:
- subtotal (per item): price * quantity
- subtotal (cart): sum of all item subtotals
- shipping: Free over threshold, otherwise flat rate
- total: subtotal + shipping

Frontend displays these values but never calculates them.
This prevents price manipulation attacks.

STOCK CHECKING:
---------------
When displaying cart:
- Fetch current product data
- Check if in_stock is still true
- If stock_quantity < cart quantity, show warning
- At checkout, validate stock before order creation
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ==============================================================================
# CART ITEM ADD MODEL
# ==============================================================================
class CartItemAdd(BaseModel):
    """
    Model for adding item to cart.

    Used when user clicks "Add to Cart" on product page.
    If product already in cart, quantity is increased.

    Example JSON:
        {
            "product_id": "abc123",
            "quantity": 1
        }
    """

    product_id: str = Field(
        ...,
        description="Product ID to add to cart"
    )
    quantity: int = Field(
        1,               # Default to 1 item
        ge=1,            # Minimum 1 (can't add 0 items)
        le=100,          # Maximum 100 per line item
        description="Quantity to add"
    )


# ==============================================================================
# CART ITEM UPDATE MODEL
# ==============================================================================
class CartItemUpdate(BaseModel):
    """
    Model for updating cart item quantity.

    Used when user changes quantity in cart page.
    Setting quantity to 0 removes the item from cart.

    Example JSON (change quantity):
        {"quantity": 3}

    Example JSON (remove item):
        {"quantity": 0}
    """

    quantity: int = Field(
        ...,
        ge=0,           # 0 means remove item
        le=100,         # Maximum 100 per line item
        description="New quantity (0 to remove)"
    )


# ==============================================================================
# CART ITEM RESPONSE MODEL
# ==============================================================================
class CartItemResponse(BaseModel):
    """
    Model for cart item in response.

    Each item includes product details (fetched at response time)
    so frontend doesn't need separate product API calls.

    Includes stock information for inventory warnings.

    Example JSON:
        {
            "product_id": "abc123",
            "product_name": "iPhone 15 Pro",
            "product_image": "https://...",
            "price": 129900,
            "quantity": 2,
            "subtotal": 259800,
            "in_stock": true,
            "stock_quantity": 50
        }
    """

    # Product identification
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name for display")
    product_image: Optional[str] = Field(
        None,
        description="Product thumbnail image"
    )

    # Pricing
    price: float = Field(
        ...,
        description="Current unit price (at time of display)"
    )
    quantity: int = Field(..., description="Quantity in cart")
    subtotal: float = Field(
        ...,
        description="Line total (price * quantity)"
    )

    # Stock information
    in_stock: bool = Field(
        True,
        description="Whether product is still available"
    )
    stock_quantity: int = Field(
        0,
        description="Current available stock (for inventory warnings)"
    )


# ==============================================================================
# CART RESPONSE MODEL
# ==============================================================================
class CartResponse(BaseModel):
    """
    Model for full cart response.

    Returned when fetching cart details.
    Includes all items with totals calculated.

    Example JSON:
        {
            "id": "cart123",
            "user_id": "user456",
            "items": [...],
            "item_count": 3,
            "subtotal": 159700,
            "shipping": 0,
            "total": 159700,
            "updated_at": "2024-01-15T10:30:00"
        }

    Note: Prices are in paise (INR * 100) for some systems,
    but this app uses INR directly (no decimal issues with
    JSON floats for display purposes).
    """

    # Cart identification
    id: str = Field(..., description="Cart ID (Firestore document ID)")
    user_id: str = Field(..., description="Owner user ID")

    # Items
    items: List[CartItemResponse] = Field(
        default_factory=list,
        description="List of items in cart"
    )
    item_count: int = Field(
        0,
        description="Total number of items (sum of quantities)"
    )

    # Totals
    subtotal: float = Field(
        0.0,
        description="Sum of all item subtotals (tax included in India)"
    )
    shipping: float = Field(
        0.0,
        description="Shipping cost (0 for free shipping)"
    )
    total: float = Field(
        0.0,
        description="Grand total (subtotal + shipping)"
    )

    # Metadata
    updated_at: Optional[str] = Field(
        None,
        description="Last update timestamp"
    )


# ==============================================================================
# CART SUMMARY MODEL
# ==============================================================================
class CartSummary(BaseModel):
    """
    Model for cart summary (header display).

    Lightweight cart info for showing in navbar cart icon.
    Avoids loading full cart data just to show item count.

    Example JSON:
        {
            "item_count": 3,
            "total": 159700
        }
    """

    item_count: int = Field(
        0,
        description="Total number of items in cart"
    )
    total: float = Field(
        0.0,
        description="Cart total for badge display"
    )
