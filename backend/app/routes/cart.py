"""
==============================================================================
Shopping Cart API Routes (cart.py)
==============================================================================

PURPOSE:
--------
This module defines all shopping cart API endpoints:
- View cart contents with real-time product data
- Add items to cart
- Update item quantities
- Remove items from cart
- Clear entire cart

API ENDPOINTS:
--------------
GET    /cart           - Get full cart with items and totals
GET    /cart/summary   - Get cart count and total (for header badge)
POST   /cart/items     - Add item to cart
PUT    /cart/items/{id} - Update item quantity
DELETE /cart/items/{id} - Remove item from cart
DELETE /cart           - Clear entire cart

CART ARCHITECTURE:
------------------
Each user has ONE cart document in Firestore:
    carts/{cart_id}:
        user_id: "user123"
        items: [
            {product_id: "prod1", quantity: 2},
            {product_id: "prod2", quantity: 1}
        ]
        updated_at: timestamp

The cart stores minimal data (product_id, quantity).
Product details (name, price, image) are fetched at response time.
This ensures cart always reflects current prices.

PRICING LOGIC:
--------------
- Subtotal: Sum of (price * quantity) for all items
- Shipping: Free if subtotal >= ₹500, otherwise ₹40
- Total: Subtotal + Shipping
- Tax: Included in product prices (GST inclusive)

WHY ENRICH AT RESPONSE TIME?
----------------------------
Cart items are "enriched" with current product data each time:
1. Prices may change - customer sees current price
2. Products may be discontinued - removed from cart
3. Stock may change - warnings shown if low
4. Images may be updated - customer sees latest

STOCK VALIDATION:
-----------------
- Adding items: Check if stock >= requested quantity
- Updating quantity: Validate against current stock
- At checkout: Final stock validation before order
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List

from ..auth.dependencies import get_current_user
from ..models.cart import CartItemAdd, CartItemUpdate, CartResponse, CartSummary
from ..firebase import cart_repo, product_repo

# Create router with prefix and tag for OpenAPI docs
router = APIRouter(prefix="/cart", tags=["Cart"])

# ==============================================================================
# SHIPPING CONFIGURATION
# ==============================================================================
# Free shipping for orders above this amount (in INR)
FREE_SHIPPING_THRESHOLD = 500.0
# Flat shipping rate for orders below threshold
SHIPPING_COST = 40.0


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

async def get_or_create_cart(user_id: str) -> Dict[str, Any]:
    """
    Get user's cart or create a new empty cart.

    Each user has exactly one cart. If it doesn't exist,
    we create it on first access (lazy initialization).

    Args:
        user_id: User ID

    Returns:
        Cart document with id, user_id, items

    Note:
        This is called on every cart operation to ensure
        the cart exists before modifying it.
    """
    cart = await cart_repo.get_user_cart(user_id)

    if not cart:
        # Create empty cart for new user
        cart_data = {
            "user_id": user_id,
            "items": [],
        }
        cart_id = await cart_repo.create(cart_data)
        cart = await cart_repo.get_by_id(cart_id)

    return cart


async def calculate_cart_totals(items: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate cart totals from enriched items.

    Pricing breakdown:
    - subtotal: Sum of all item subtotals
    - shipping: Free if subtotal >= ₹500, else ₹40
    - total: subtotal + shipping

    Note: Tax (GST) is already included in product prices.
    India uses inclusive pricing, so no separate tax line.

    Args:
        items: List of enriched cart items with subtotal

    Returns:
        Dict with subtotal, shipping, and total
    """
    subtotal = sum(item.get("subtotal", 0) for item in items)
    # Free shipping above threshold
    shipping = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_COST
    total = round(subtotal + shipping, 2)

    return {
        "subtotal": round(subtotal, 2),
        "shipping": shipping,
        "total": total,
    }


async def enrich_cart_items(cart_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich cart items with current product data.

    Cart items only store product_id and quantity.
    This function fetches current product info (name, price, image, stock)
    to build the complete response.

    Products that are inactive or deleted are silently removed.

    Args:
        cart_items: List of {product_id, quantity}

    Returns:
        List of enriched items with full product details

    Note:
        This makes N database calls (one per item).
        For large carts, consider batch fetching.
    """
    enriched = []

    for item in cart_items:
        product = await product_repo.get_by_id(item["product_id"])

        # Only include active products (inactive ones are silently removed)
        if product and product.get("is_active", True):
            stock = product.get("stock_quantity", 0)
            price = product.get("price", 0)
            quantity = item.get("quantity", 1)

            enriched.append({
                "product_id": item["product_id"],
                "product_name": product.get("name", "Unknown Product"),
                "product_image": product.get("thumbnail") or (product.get("images", [None])[0] if product.get("images") else None),
                "price": price,  # Current price (may differ from when added)
                "quantity": quantity,
                "subtotal": round(price * quantity, 2),
                "in_stock": stock > 0,
                "stock_quantity": stock,  # For inventory warnings
            })

    return enriched


def format_cart_response(cart: Dict[str, Any], enriched_items: List[Dict[str, Any]], totals: Dict[str, float]) -> Dict[str, Any]:
    """
    Format cart data for API response.

    Combines cart metadata, enriched items, and calculated totals
    into a single response matching CartResponse schema.

    Args:
        cart: Raw cart document
        enriched_items: Items with product details
        totals: Calculated subtotal, shipping, total

    Returns:
        Complete CartResponse-compatible dict
    """
    return {
        "id": cart["id"],
        "user_id": cart["user_id"],
        "items": enriched_items,
        "item_count": sum(item["quantity"] for item in enriched_items),
        "subtotal": totals["subtotal"],
        "shipping": totals["shipping"],
        "total": totals["total"],
        "updated_at": cart.get("updated_at"),
    }


# ==============================================================================
# CART ENDPOINTS - All require authentication
# ==============================================================================

@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's cart with full details.

    Returns complete cart including:
    - All items with current product data
    - Calculated subtotal, shipping, and total
    - Stock information for inventory warnings

    Returns:
        CartResponse with items and totals

    Authorization:
        Requires authenticated user

    Example Response:
        {
            "id": "cart123",
            "items": [...],
            "item_count": 3,
            "subtotal": 1500,
            "shipping": 0,
            "total": 1500
        }
    """
    cart = await get_or_create_cart(current_user["id"])
    enriched_items = await enrich_cart_items(cart.get("items", []))
    totals = await calculate_cart_totals(enriched_items)

    return format_cart_response(cart, enriched_items, totals)


@router.get("/summary", response_model=CartSummary)
async def get_cart_summary(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get cart summary for header badge display.

    Lightweight endpoint returning only count and total.
    Used by navbar to show cart icon badge.

    Returns:
        CartSummary with item_count and total

    Note:
        This is slightly more expensive than a simple count
        because we need to fetch product prices for the total.
        Consider caching if this becomes a bottleneck.
    """
    cart = await get_or_create_cart(current_user["id"])
    items = cart.get("items", [])

    # Sum quantities for item count
    item_count = sum(item.get("quantity", 0) for item in items)

    # Calculate total by fetching current prices
    total = 0.0
    for item in items:
        product = await product_repo.get_by_id(item["product_id"])
        if product:
            total += product.get("price", 0) * item.get("quantity", 1)

    return {
        "item_count": item_count,
        "total": round(total, 2),
    }


@router.post("/items", response_model=CartResponse)
async def add_to_cart(
    item_data: CartItemAdd,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Add item to cart.

    If product already in cart, quantity is increased.
    Validates stock before adding.

    Request Body:
        {
            "product_id": "prod123",
            "quantity": 2
        }

    Returns:
        Updated cart with all items

    Raises:
        404: Product not found or inactive
        400: Insufficient stock

    Example:
        POST /cart/items
        {"product_id": "abc123", "quantity": 1}
    """
    # Verify product exists and is active
    product = await product_repo.get_by_id(item_data.product_id)
    if not product or not product.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Check stock availability
    stock = product.get("stock_quantity", 0)
    if stock < item_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {stock} items available in stock"
        )

    # Get or create cart
    cart = await get_or_create_cart(current_user["id"])
    items = cart.get("items", [])

    # Check if product already in cart
    existing_index = next(
        (i for i, item in enumerate(items) if item["product_id"] == item_data.product_id),
        None
    )

    if existing_index is not None:
        # Product already in cart - increase quantity
        new_quantity = items[existing_index]["quantity"] + item_data.quantity
        if new_quantity > stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add more. Only {stock} items available"
            )
        items[existing_index]["quantity"] = new_quantity
    else:
        # New product - add to cart
        items.append({
            "product_id": item_data.product_id,
            "quantity": item_data.quantity,
        })

    # Save updated cart
    await cart_repo.update(cart["id"], {"items": items})

    # Return updated cart with enriched data
    cart = await cart_repo.get_by_id(cart["id"])
    enriched_items = await enrich_cart_items(cart.get("items", []))
    totals = await calculate_cart_totals(enriched_items)

    return format_cart_response(cart, enriched_items, totals)


@router.put("/items/{product_id}", response_model=CartResponse)
async def update_cart_item(
    product_id: str,
    item_data: CartItemUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update cart item quantity.

    Set quantity to 0 to remove the item.
    Validates stock before updating.

    Path Parameters:
        product_id: Product ID in cart

    Request Body:
        {"quantity": 3}  or  {"quantity": 0} to remove

    Returns:
        Updated cart

    Raises:
        404: Item not in cart
        400: Insufficient stock

    Example:
        PUT /cart/items/abc123
        {"quantity": 5}
    """
    cart = await get_or_create_cart(current_user["id"])
    items = cart.get("items", [])

    # Find item in cart
    item_index = next(
        (i for i, item in enumerate(items) if item["product_id"] == product_id),
        None
    )

    if item_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )

    if item_data.quantity == 0:
        # Quantity 0 = remove item from cart
        items.pop(item_index)
    else:
        # Validate new quantity against stock
        product = await product_repo.get_by_id(product_id)
        if product:
            stock = product.get("stock_quantity", 0)
            if item_data.quantity > stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {stock} items available in stock"
                )

        items[item_index]["quantity"] = item_data.quantity

    # Save updated cart
    await cart_repo.update(cart["id"], {"items": items})

    # Return updated cart with enriched data
    cart = await cart_repo.get_by_id(cart["id"])
    enriched_items = await enrich_cart_items(cart.get("items", []))
    totals = await calculate_cart_totals(enriched_items)

    return format_cart_response(cart, enriched_items, totals)


@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_from_cart(
    product_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Remove item from cart completely.

    Unlike PUT with quantity=0, this is explicit removal.
    Returns updated cart after removal.

    Path Parameters:
        product_id: Product ID to remove

    Returns:
        Updated cart

    Raises:
        404: Item not in cart

    Example:
        DELETE /cart/items/abc123
    """
    cart = await get_or_create_cart(current_user["id"])
    items = cart.get("items", [])

    # Filter out the item
    new_items = [item for item in items if item["product_id"] != product_id]

    # Check if anything was actually removed
    if len(new_items) == len(items):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )

    # Save updated cart
    await cart_repo.update(cart["id"], {"items": new_items})

    # Return updated cart with enriched data
    cart = await cart_repo.get_by_id(cart["id"])
    enriched_items = await enrich_cart_items(cart.get("items", []))
    totals = await calculate_cart_totals(enriched_items)

    return format_cart_response(cart, enriched_items, totals)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    Clear all items from cart.

    Used after successful order placement or manual clear.
    Returns 204 No Content on success.

    Example:
        DELETE /cart

    Note:
        The cart document is not deleted, only items are cleared.
        This preserves the cart ID for future use.
    """
    await cart_repo.clear_cart(current_user["id"])
