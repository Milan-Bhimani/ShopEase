"""
==============================================================================
Product Models (product.py)
==============================================================================

PURPOSE:
--------
This module defines Pydantic models for product-related operations:
- Product creation and updates (admin)
- Product listings and details
- Category management

E-COMMERCE PRODUCT DATA:
------------------------
Products in this app have:
- Basic info: name, description, price
- Inventory: stock quantity, SKU
- Media: images, thumbnail
- Classification: category, brand, tags
- Pricing: current price, original price, discount
- Display: featured flag, rating, reviews

PRICING LOGIC:
--------------
- price: Current selling price
- original_price: Price before discount (strikethrough price)
- discount_percentage: Calculated as (original - current) / original * 100

Example:
    original_price: 1000
    price: 800
    discount_percentage: 20

SEARCH OPTIMIZATION:
--------------------
The name_lower field is used for case-insensitive search.
When a product is created, name_lower = name.lower() is stored.
Firestore doesn't support native case-insensitive queries,
so we pre-compute the lowercase version.

STOCK MANAGEMENT:
-----------------
- stock_quantity: Number of items available
- in_stock: Boolean derived from stock_quantity > 0
- Frontend uses in_stock for quick UI decisions
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# ==============================================================================
# PRODUCT CREATE MODEL (Admin)
# ==============================================================================
class ProductCreate(BaseModel):
    """
    Model for creating a new product (admin only).

    Used by admin panel to add new products to the catalog.
    Contains all product attributes that can be set at creation.

    Example JSON:
        {
            "name": "iPhone 15 Pro",
            "description": "Latest Apple smartphone with titanium design...",
            "price": 129900,
            "original_price": 149900,
            "category": "Electronics",
            "brand": "Apple",
            "stock_quantity": 50,
            "images": ["https://..."],
            "is_featured": true
        }
    """

    # Basic product information
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Product name"
    )
    description: str = Field(
        ...,
        max_length=5000,
        description="Product description (supports markdown/HTML)"
    )

    # Pricing
    price: float = Field(
        ...,
        gt=0,  # Greater than 0 (no free or negative prices)
        description="Current selling price in INR"
    )
    original_price: Optional[float] = Field(
        None,
        gt=0,
        description="Original price before discount (for strikethrough display)"
    )

    # Classification
    category: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Product category (e.g., 'Electronics', 'Clothing')"
    )
    brand: Optional[str] = Field(
        None,
        max_length=100,
        description="Brand name"
    )

    # Inventory
    sku: Optional[str] = Field(
        None,
        max_length=50,
        description="Stock Keeping Unit for inventory tracking"
    )
    stock_quantity: int = Field(
        0,
        ge=0,  # Greater than or equal to 0
        description="Available stock count"
    )

    # Media
    images: List[str] = Field(
        default_factory=list,
        description="List of product image URLs"
    )
    thumbnail: Optional[str] = Field(
        None,
        description="Thumbnail image URL for listings"
    )

    # Additional details
    specifications: Optional[dict] = Field(
        None,
        description="Key-value pairs for product specs (RAM, storage, etc.)"
    )

    # Display flags
    is_active: bool = Field(
        True,
        description="Whether product is visible in catalog"
    )
    is_featured: bool = Field(
        False,
        description="Whether product appears in featured section"
    )

    # Search and filtering
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for search and filtering"
    )


# ==============================================================================
# PRODUCT UPDATE MODEL (Admin)
# ==============================================================================
class ProductUpdate(BaseModel):
    """
    Model for updating a product.

    All fields are optional - only provided fields are updated.
    This allows partial updates without resending all data.

    Example JSON (updating just price and stock):
        {
            "price": 119900,
            "stock_quantity": 45
        }
    """

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=50)
    stock_quantity: Optional[int] = Field(None, ge=0)
    images: Optional[List[str]] = None
    thumbnail: Optional[str] = None
    specifications: Optional[dict] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    tags: Optional[List[str]] = None


# ==============================================================================
# PRODUCT RESPONSE MODEL
# ==============================================================================
class ProductResponse(BaseModel):
    """
    Model for product response.

    Returned from product list and detail endpoints.
    Includes computed fields like discount_percentage and in_stock.

    Example JSON:
        {
            "id": "abc123",
            "name": "iPhone 15 Pro",
            "price": 129900,
            "original_price": 149900,
            "discount_percentage": 13,
            "in_stock": true,
            "stock_quantity": 50,
            ...
        }
    """

    # Identification
    id: str = Field(..., description="Product ID (Firestore document ID)")

    # Basic info
    name: str = Field(..., description="Product name")
    name_lower: Optional[str] = Field(
        None,
        description="Lowercase name for search (internal use)"
    )
    description: str = Field(..., description="Product description")

    # Pricing with discount info
    price: float = Field(..., description="Current price in INR")
    original_price: Optional[float] = Field(
        None,
        description="Original price (shown with strikethrough)"
    )
    discount_percentage: Optional[int] = Field(
        None,
        description="Calculated discount percentage"
    )

    # Classification
    category: str = Field(..., description="Product category")
    brand: Optional[str] = Field(None, description="Brand name")
    sku: Optional[str] = Field(None, description="SKU")

    # Inventory
    stock_quantity: int = Field(0, description="Available stock")
    in_stock: bool = Field(True, description="Whether product is available")

    # Media
    images: List[str] = Field(
        default_factory=list,
        description="Product images"
    )
    thumbnail: Optional[str] = Field(None, description="Thumbnail image")

    # Details
    specifications: Optional[dict] = Field(None, description="Product specs")

    # Display
    is_featured: bool = Field(False, description="Featured product flag")
    tags: List[str] = Field(default_factory=list, description="Search tags")

    # Reviews (aggregated data)
    rating: Optional[float] = Field(
        None,
        description="Average rating (1-5)"
    )
    review_count: int = Field(0, description="Number of reviews")

    # Timestamps
    created_at: Optional[str] = Field(None, description="Creation date")

    class Config:
        """Pydantic configuration."""
        # Enable from_attributes for ORM-style instantiation
        from_attributes = True


# ==============================================================================
# CATEGORY RESPONSE MODEL
# ==============================================================================
class CategoryResponse(BaseModel):
    """
    Model for category response.

    Categories organize products into logical groups.
    Used for category filters and navigation.

    Example JSON:
        {
            "id": "electronics",
            "name": "Electronics",
            "slug": "electronics",
            "description": "Phones, laptops, and gadgets",
            "image": "https://...",
            "product_count": 150
        }
    """

    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Display name")
    slug: str = Field(
        ...,
        description="URL-friendly name (lowercase, hyphens)"
    )
    description: Optional[str] = Field(
        None,
        description="Category description"
    )
    image: Optional[str] = Field(
        None,
        description="Category banner/icon image"
    )
    product_count: int = Field(
        0,
        description="Number of products in category"
    )


# ==============================================================================
# PRODUCT LIST RESPONSE (Paginated)
# ==============================================================================
class ProductListResponse(BaseModel):
    """
    Model for paginated product list.

    Used for product listing pages with pagination.
    Frontend uses has_more to show "Load More" button.

    Example JSON:
        {
            "products": [...],
            "total": 150,
            "page": 1,
            "per_page": 20,
            "has_more": true
        }
    """

    products: List[ProductResponse] = Field(
        ...,
        description="List of products on current page"
    )
    total: int = Field(
        ...,
        description="Total products matching filters"
    )
    page: int = Field(1, description="Current page number (1-indexed)")
    per_page: int = Field(20, description="Products per page")
    has_more: bool = Field(
        False,
        description="Whether more products are available"
    )
