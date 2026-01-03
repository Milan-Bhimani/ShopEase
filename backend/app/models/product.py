"""
Product-related Pydantic models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ProductCreate(BaseModel):
    """Model for creating a new product (admin only)."""

    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: str = Field(..., max_length=5000, description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    original_price: Optional[float] = Field(None, gt=0, description="Original price before discount")
    category: str = Field(..., min_length=1, max_length=100, description="Product category")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    sku: Optional[str] = Field(None, max_length=50, description="Stock keeping unit")
    stock_quantity: int = Field(0, ge=0, description="Available stock")
    images: List[str] = Field(default_factory=list, description="Product image URLs")
    thumbnail: Optional[str] = Field(None, description="Thumbnail image URL")
    specifications: Optional[dict] = Field(None, description="Product specifications")
    is_active: bool = Field(True, description="Product visibility")
    is_featured: bool = Field(False, description="Featured product flag")
    tags: List[str] = Field(default_factory=list, description="Product tags for search")


class ProductUpdate(BaseModel):
    """Model for updating a product."""

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


class ProductResponse(BaseModel):
    """Model for product response."""

    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    name_lower: Optional[str] = Field(None, description="Lowercase name for search")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Current price")
    original_price: Optional[float] = Field(None, description="Original price")
    discount_percentage: Optional[int] = Field(None, description="Calculated discount percentage")
    category: str = Field(..., description="Product category")
    brand: Optional[str] = Field(None, description="Product brand")
    sku: Optional[str] = Field(None, description="SKU")
    stock_quantity: int = Field(0, description="Available stock")
    in_stock: bool = Field(True, description="Stock availability")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    specifications: Optional[dict] = Field(None, description="Specifications")
    is_featured: bool = Field(False, description="Featured flag")
    tags: List[str] = Field(default_factory=list, description="Tags")
    rating: Optional[float] = Field(None, description="Average rating")
    review_count: int = Field(0, description="Number of reviews")
    created_at: Optional[str] = Field(None, description="Creation timestamp")

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    """Model for category response."""

    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL-friendly name")
    description: Optional[str] = Field(None, description="Category description")
    image: Optional[str] = Field(None, description="Category image URL")
    product_count: int = Field(0, description="Number of products")


class ProductListResponse(BaseModel):
    """Model for paginated product list."""

    products: List[ProductResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")
    page: int = Field(1, description="Current page")
    per_page: int = Field(20, description="Items per page")
    has_more: bool = Field(False, description="More pages available")
