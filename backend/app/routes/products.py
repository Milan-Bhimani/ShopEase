"""
==============================================================================
Product API Routes (products.py)
==============================================================================

PURPOSE:
--------
This module defines all product-related API endpoints:
- Product listing with filters (category, search, price range)
- Product detail retrieval
- Featured products for homepage
- Category listing with product counts
- Admin CRUD operations (create, update, delete)

API ENDPOINTS:
--------------
GET  /products              - List products with filters and pagination
GET  /products/featured     - Get featured products for homepage
GET  /products/categories   - Get category list with counts
GET  /products/{id}         - Get single product details

Admin only (requires authentication):
POST   /products            - Create new product
PUT    /products/{id}       - Update product
DELETE /products/{id}       - Soft delete product

FILTERING STRATEGY:
-------------------
Products can be filtered by:
1. Category: Exact match on category name
2. Search: Case-insensitive search on name_lower field
3. Price range: min_price and max_price bounds
4. Featured: Boolean flag for homepage display

Firestore doesn't support complex queries (OR, full-text search),
so we fetch more data and filter in Python. This is acceptable
for catalogs under 10,000 products.

PAGINATION:
-----------
Uses offset-based pagination:
- page: Page number (1-indexed)
- per_page: Items per page (default 20, max 100)
- has_more: Boolean indicating more pages available

DISCOUNT CALCULATION:
---------------------
Discount is calculated from original_price and current price:
    discount = (original - current) / original * 100

Example: ₹1000 -> ₹800 = 20% off

SOFT DELETE:
------------
Products are never actually deleted from Firestore.
Instead, is_active is set to False.
This preserves order history that references the product.
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

# Create router with prefix and tag for OpenAPI docs
router = APIRouter(prefix="/products", tags=["Products"])


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def calculate_discount(price: float, original_price: Optional[float]) -> Optional[int]:
    """
    Calculate discount percentage from original and current price.

    Formula: ((original - current) / original) * 100, rounded to integer

    Args:
        price: Current selling price
        original_price: Original price before discount

    Returns:
        Discount percentage (0-100) or None if no discount

    Example:
        calculate_discount(800, 1000) -> 20  (20% off)
        calculate_discount(1000, 1000) -> None (no discount)
    """
    if original_price and original_price > price:
        return int(((original_price - price) / original_price) * 100)
    return None


def format_product_response(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format raw Firestore product data for API response.

    Transforms database document into ProductResponse-compatible dict.
    Calculates derived fields: discount_percentage, in_stock.
    Falls back to first image if thumbnail not set.

    Args:
        product: Raw product document from Firestore

    Returns:
        Formatted product dict matching ProductResponse schema

    Note:
        This function is called for every product in listings,
        so it should be fast. Avoid database calls here.
    """
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
        "in_stock": stock > 0,  # Derived from stock_quantity
        "images": product.get("images", []),
        # Fallback: use first image if no thumbnail
        "thumbnail": product.get("thumbnail") or (product.get("images", [None])[0] if product.get("images") else None),
        "specifications": product.get("specifications"),
        "is_featured": product.get("is_featured", False),
        "tags": product.get("tags", []),
        "rating": product.get("rating"),
        "review_count": product.get("review_count", 0),
        "created_at": product.get("created_at"),
    }


# ==============================================================================
# PUBLIC ENDPOINTS - No authentication required
# ==============================================================================

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
    List products with optional filters and pagination.

    This is the main product listing endpoint used by:
    - Homepage (featured=True)
    - Category pages (category="Electronics")
    - Search results (search="iPhone")
    - Shop all page (no filters)

    Query Parameters:
        category: Filter by exact category name
        search: Search in product name (case-insensitive)
        featured: Only show featured products
        min_price: Minimum price filter
        max_price: Maximum price filter
        page: Page number (1-indexed)
        per_page: Products per page (1-100)

    Returns:
        ProductListResponse with products, total count, and pagination info

    Example:
        GET /products?category=Electronics&min_price=1000&page=1

    Note:
        Only active products (is_active=True) are returned.
        Inactive products are hidden from customers.
    """
    # Get products based on primary filter
    # Only one primary filter is applied at a time (priority order)
    if featured:
        products = await product_repo.get_featured(limit=per_page)
    elif category:
        products = await product_repo.get_by_category(category, limit=100)
    elif search:
        products = await product_repo.search(search, limit=100)
    else:
        products = await product_repo.get_all(limit=100)

    # Filter by active status (hide deactivated products)
    products = [p for p in products if p.get("is_active", True)]

    # Apply price range filters in Python
    # (Firestore doesn't support multiple range queries)
    if min_price is not None:
        products = [p for p in products if p.get("price", 0) >= min_price]
    if max_price is not None:
        products = [p for p in products if p.get("price", 0) <= max_price]

    # Calculate pagination
    total = len(products)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = products[start:end]

    return {
        "products": [format_product_response(p) for p in paginated],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": end < total,  # True if more pages available
    }


@router.get("/featured", response_model=List[ProductResponse])
async def get_featured_products(
    limit: int = Query(10, ge=1, le=50, description="Number of products")
) -> List[Dict[str, Any]]:
    """
    Get featured products for homepage display.

    Featured products are manually curated by admin (is_featured=True).
    Used for homepage hero section and promotional displays.

    Query Parameters:
        limit: Maximum number of products to return (1-50)

    Returns:
        List of featured products

    Example:
        GET /products/featured?limit=8
    """
    products = await product_repo.get_featured(limit=limit)
    return [format_product_response(p) for p in products if p.get("is_active", True)]


@router.get("/categories")
async def get_categories() -> List[Dict[str, Any]]:
    """
    Get list of product categories with product counts.

    Categories are derived from product data (not a separate collection).
    Each category includes a count of active products.

    Returns:
        List of categories sorted alphabetically

    Response Format:
        [
            {"id": "electronics", "name": "Electronics", "slug": "electronics", "product_count": 25},
            {"id": "fashion", "name": "Fashion", "slug": "fashion", "product_count": 15},
            ...
        ]

    Note:
        - Categories are computed dynamically from products
        - Empty categories (0 products) are not returned
        - slug is generated from name (lowercase, spaces to dashes)
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

    # Format response with URL-friendly slugs
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

    Used for product detail page.
    Returns full product information including description,
    specifications, images, and stock status.

    Path Parameters:
        product_id: Firestore document ID

    Returns:
        Complete product details

    Raises:
        404: Product not found or inactive

    Example:
        GET /products/abc123xyz
    """
    product = await product_repo.get_by_id(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Treat inactive products as not found for customers
    if not product.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return format_product_response(product)


# ==============================================================================
# ADMIN ENDPOINTS - Requires authentication + admin role
# ==============================================================================

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> Dict[str, Any]:
    """
    Create a new product (admin only).

    Creates a new product in the Firestore products collection.
    Automatically generates name_lower for search indexing.

    Request Body:
        ProductCreate model with name, description, price, etc.

    Returns:
        Created product with generated ID

    Authorization:
        Requires admin user (get_admin_user dependency)

    Example:
        POST /products
        {
            "name": "iPhone 15 Pro",
            "description": "Latest Apple smartphone...",
            "price": 129900,
            "category": "Electronics",
            "stock_quantity": 50
        }
    """
    # Convert Pydantic model to dict
    product_dict = product_data.model_dump()

    # Generate lowercase name for search (Firestore case-insensitive workaround)
    product_dict["name_lower"] = product_data.name.lower()

    # Create in Firestore
    product_id = await product_repo.create(product_dict)

    # Return created product
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

    Partial update - only provided fields are changed.
    If name is updated, name_lower is regenerated for search.

    Path Parameters:
        product_id: Product ID to update

    Request Body:
        ProductUpdate model with optional fields

    Returns:
        Updated product

    Raises:
        404: Product not found

    Example:
        PUT /products/abc123
        {"price": 119900, "stock_quantity": 45}
    """
    # Verify product exists
    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Build update dict with only non-None values
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

    # Update search index if name changed
    if "name" in update_dict:
        update_dict["name_lower"] = update_dict["name"].lower()

    # Apply update
    if update_dict:
        await product_repo.update(product_id, update_dict)

    # Return updated product
    updated = await product_repo.get_by_id(product_id)
    return format_product_response(updated)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> None:
    """
    Delete a product (admin only - soft delete).

    Products are soft-deleted by setting is_active=False.
    This preserves historical data (orders that reference this product).
    Soft-deleted products are hidden from listings but still exist.

    Path Parameters:
        product_id: Product ID to delete

    Raises:
        404: Product not found

    Example:
        DELETE /products/abc123

    Note:
        To permanently delete, use Firestore console.
        Soft delete is reversible by setting is_active=True.
    """
    # Verify product exists
    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Soft delete - just mark as inactive
    await product_repo.update(product_id, {"is_active": False})
