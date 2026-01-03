"""
Product API routes.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, List, Optional

from ..auth.dependencies import get_current_user_optional, get_admin_user
from ..models.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
)
from ..firebase import product_repo

router = APIRouter(prefix="/products", tags=["Products"])


def calculate_discount(price: float, original_price: Optional[float]) -> Optional[int]:
    """Calculate discount percentage."""
    if original_price and original_price > price:
        return int(((original_price - price) / original_price) * 100)
    return None


def format_product_response(product: Dict[str, Any]) -> Dict[str, Any]:
    """Format product data for response."""
    price = product.get("price", 0)
    original_price = product.get("original_price")
    stock = product.get("stock_quantity", 0)

    return {
        "id": product["id"],
        "name": product.get("name", ""),
        "name_lower": product.get("name_lower", ""),
        "description": product.get("description", ""),
        "price": price,
        "original_price": original_price,
        "discount_percentage": calculate_discount(price, original_price),
        "category": product.get("category", ""),
        "brand": product.get("brand"),
        "sku": product.get("sku"),
        "stock_quantity": stock,
        "in_stock": stock > 0,
        "images": product.get("images", []),
        "thumbnail": product.get("thumbnail") or (product.get("images", [None])[0] if product.get("images") else None),
        "specifications": product.get("specifications"),
        "is_featured": product.get("is_featured", False),
        "tags": product.get("tags", []),
        "rating": product.get("rating"),
        "review_count": product.get("review_count", 0),
        "created_at": product.get("created_at"),
    }


@router.get("", response_model=ProductListResponse)
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search query"),
    featured: bool = Query(False, description="Show only featured products"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
) -> Dict[str, Any]:
    """
    List products with optional filters.

    Returns:
        Paginated list of products
    """
    # Get products based on filters
    if featured:
        products = await product_repo.get_featured(limit=per_page)
    elif category:
        products = await product_repo.get_by_category(category, limit=100)
    elif search:
        products = await product_repo.search(search, limit=100)
    else:
        products = await product_repo.get_all(limit=100)

    # Filter by active status
    products = [p for p in products if p.get("is_active", True)]

    # Filter by price range
    if min_price is not None:
        products = [p for p in products if p.get("price", 0) >= min_price]
    if max_price is not None:
        products = [p for p in products if p.get("price", 0) <= max_price]

    # Pagination
    total = len(products)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = products[start:end]

    return {
        "products": [format_product_response(p) for p in paginated],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": end < total,
    }


@router.get("/featured", response_model=List[ProductResponse])
async def get_featured_products(
    limit: int = Query(10, ge=1, le=50, description="Number of products")
) -> List[Dict[str, Any]]:
    """
    Get featured products for homepage.

    Returns:
        List of featured products
    """
    products = await product_repo.get_featured(limit=limit)
    return [format_product_response(p) for p in products if p.get("is_active", True)]


@router.get("/categories")
async def get_categories() -> List[Dict[str, Any]]:
    """
    Get list of product categories.

    Returns:
        List of categories with product counts
    """
    # Get all active products
    products = await product_repo.get_all(limit=500)
    products = [p for p in products if p.get("is_active", True)]

    # Count products per category
    category_counts = {}
    for product in products:
        cat = product.get("category", "Other")
        if cat in category_counts:
            category_counts[cat] += 1
        else:
            category_counts[cat] = 1

    # Format response
    categories = [
        {
            "id": cat.lower().replace(" ", "-"),
            "name": cat,
            "slug": cat.lower().replace(" ", "-"),
            "product_count": count,
        }
        for cat, count in sorted(category_counts.items())
    ]

    return categories


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str) -> Dict[str, Any]:
    """
    Get a single product by ID.

    Args:
        product_id: Product ID

    Returns:
        Product details
    """
    product = await product_repo.get_by_id(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if not product.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return format_product_response(product)


# ============================================================
# Admin routes
# ============================================================

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> Dict[str, Any]:
    """
    Create a new product (admin only).

    Args:
        product_data: Product data

    Returns:
        Created product
    """
    product_dict = product_data.model_dump()
    product_dict["name_lower"] = product_data.name.lower()

    product_id = await product_repo.create(product_dict)

    product = await product_repo.get_by_id(product_id)
    return format_product_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    update_data: ProductUpdate,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> Dict[str, Any]:
    """
    Update a product (admin only).

    Args:
        product_id: Product ID
        update_data: Fields to update

    Returns:
        Updated product
    """
    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

    if "name" in update_dict:
        update_dict["name_lower"] = update_dict["name"].lower()

    if update_dict:
        await product_repo.update(product_id, update_dict)

    updated = await product_repo.get_by_id(product_id)
    return format_product_response(updated)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> None:
    """
    Delete a product (admin only - soft delete).

    Args:
        product_id: Product ID
    """
    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Soft delete
    await product_repo.update(product_id, {"is_active": False})
