"""Pydantic models for request/response validation."""
from .user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    TokenResponse,
    OTPRequest,
    OTPVerify,
    OTPResponse,
    OTPVerifyResponse,
)
from .product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    CategoryResponse,
)
from .cart import (
    CartItemAdd,
    CartItemUpdate,
    CartResponse,
    CartItemResponse,
)
from .order import (
    OrderCreate,
    OrderResponse,
    OrderItemResponse,
    PaymentInfo,
    OrderStatus,
)
from .address import (
    AddressCreate,
    AddressUpdate,
    AddressResponse,
)

__all__ = [
    # User models
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "TokenResponse",
    "OTPRequest",
    "OTPVerify",
    "OTPResponse",
    "OTPVerifyResponse",
    # Product models
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "CategoryResponse",
    # Cart models
    "CartItemAdd",
    "CartItemUpdate",
    "CartResponse",
    "CartItemResponse",
    # Order models
    "OrderCreate",
    "OrderResponse",
    "OrderItemResponse",
    "PaymentInfo",
    "OrderStatus",
    # Address models
    "AddressCreate",
    "AddressUpdate",
    "AddressResponse",
]
