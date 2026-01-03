"""
Shopping Cart API routes.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List

from ..auth.dependencies import get_current_user
from ..models.cart import CartItemAdd, CartItemUpdate, CartResponse, CartSummary
from ..firebase import cart_repo, product_repo

router = APIRouter(prefix="/cart", tags=["Cart"])

# Shipping settings
FREE_SHIPPING_THRESHOLD = 500.0
SHIPPING_COST = 40.0


async def get_or_create_cart(user_id: str) -> Dict[str, Any]:
    """Get user's cart or create a new one."""
    cart = await cart_repo.get_user_cart(user_id)

    if not cart:
        cart_data = {
            "user_id": user_id,
            "items": [],
        }
        cart_id = await cart_repo.create(cart_data)
        cart = await cart_repo.get_by_id(cart_id)

    return cart


async def calculate_cart_totals(items: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate cart totals. Tax is included in product prices."""
    subtotal = sum(item.get("subtotal", 0) for item in items)
    shipping = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_COST
    total = round(subtotal + shipping, 2)

    return {
        "subtotal": round(subtotal, 2),
        "shipping": shipping,
        "total": total,
    }


async def enrich_cart_items(cart_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enrich cart items with current product data."""
    enriched = []

    for item in cart_items:
        product = await product_repo.get_by_id(item["product_id"])

        if product and product.get("is_active", True):
            stock = product.get("stock_quantity", 0)
            price = product.get("price", 0)
            quantity = item.get("quantity", 1)

            enriched.append({
                "product_id": item["product_id"],
                "product_name": product.get("name", "Unknown Product"),
                "product_image": product.get("thumbnail") or (product.get("images", [None])[0] if product.get("images") else None),
                "price": price,
                "quantity": quantity,
                "subtotal": round(price * quantity, 2),
                "in_stock": stock > 0,
                "stock_quantity": stock,
            })

    return enriched


def format_cart_response(cart: Dict[str, Any], enriched_items: List[Dict[str, Any]], totals: Dict[str, float]) -> Dict[str, Any]:
    """Format cart response."""
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


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's cart.

    Returns:
        Cart with items and totals
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
    Get cart summary (for header display).

    Returns:
        Item count and total
    """
    cart = await get_or_create_cart(current_user["id"])
    items = cart.get("items", [])

    # Quick calculation without full enrichment
    item_count = sum(item.get("quantity", 0) for item in items)

    # Calculate rough total
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

    Args:
        item_data: Product ID and quantity

    Returns:
        Updated cart
    """
    # Verify product exists and is active
    product = await product_repo.get_by_id(item_data.product_id)
    if not product or not product.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Check stock
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
        # Update quantity
        new_quantity = items[existing_index]["quantity"] + item_data.quantity
        if new_quantity > stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add more. Only {stock} items available"
            )
        items[existing_index]["quantity"] = new_quantity
    else:
        # Add new item
        items.append({
            "product_id": item_data.product_id,
            "quantity": item_data.quantity,
        })

    # Update cart
    await cart_repo.update(cart["id"], {"items": items})

    # Return updated cart
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

    Args:
        product_id: Product ID
        item_data: New quantity (0 to remove)

    Returns:
        Updated cart
    """
    cart = await get_or_create_cart(current_user["id"])
    items = cart.get("items", [])

    # Find item
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
        # Remove item
        items.pop(item_index)
    else:
        # Check stock
        product = await product_repo.get_by_id(product_id)
        if product:
            stock = product.get("stock_quantity", 0)
            if item_data.quantity > stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {stock} items available in stock"
                )

        items[item_index]["quantity"] = item_data.quantity

    # Update cart
    await cart_repo.update(cart["id"], {"items": items})

    # Return updated cart
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
    Remove item from cart.

    Args:
        product_id: Product ID to remove

    Returns:
        Updated cart
    """
    cart = await get_or_create_cart(current_user["id"])
    items = cart.get("items", [])

    # Filter out the item
    new_items = [item for item in items if item["product_id"] != product_id]

    if len(new_items) == len(items):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )

    # Update cart
    await cart_repo.update(cart["id"], {"items": new_items})

    # Return updated cart
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
    """
    await cart_repo.clear_cart(current_user["id"])
