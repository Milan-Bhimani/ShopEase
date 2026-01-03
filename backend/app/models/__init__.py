"""
==============================================================================
Models Package (models/__init__.py)
==============================================================================

PURPOSE:
--------
This package contains all Pydantic models for request/response validation.
Models are the data contracts between the frontend and backend.

WHAT ARE PYDANTIC MODELS?
-------------------------
Pydantic models provide:
1. **Automatic Validation**: Invalid data raises helpful errors
2. **Type Coercion**: Converts strings to ints, etc. when possible
3. **JSON Serialization**: Easy conversion to/from JSON
4. **Documentation**: Models appear in OpenAPI/Swagger docs

WHY USE SEPARATE MODEL FILES?
-----------------------------
- **Organization**: Related models grouped together
- **Maintainability**: Easy to find and update models
- **Reusability**: Models can import from each other
- **Testing**: Models can be tested independently

MODEL CATEGORIES:
-----------------
1. **User Models** (user.py)
   - UserCreate: Registration data
   - UserLogin: Login credentials
   - UserResponse: Public user profile
   - TokenResponse: Authentication token
   - OTP models: For email verification

2. **Product Models** (product.py)
   - ProductCreate/Update: Admin CRUD operations
   - ProductResponse: Product details for display
   - CategoryResponse: Product categories

3. **Cart Models** (cart.py)
   - CartItemAdd: Adding items to cart
   - CartItemUpdate: Changing quantities
   - CartResponse: Full cart with totals

4. **Order Models** (order.py)
   - OrderCreate: Placing an order
   - OrderResponse: Order details
   - PaymentInfo: Payment details
   - OrderStatus: Order state machine

5. **Address Models** (address.py)
   - AddressCreate/Update: Shipping addresses
   - AddressResponse: Address details

NAMING CONVENTIONS:
------------------
- *Create: For creating new resources (POST)
- *Update: For updating resources (PUT/PATCH)
- *Response: For returning data (GET, response bodies)
- *Request: For specific request payloads

USAGE EXAMPLE:
--------------
    from app.models import UserCreate, TokenResponse

    @router.post("/register", response_model=TokenResponse)
    async def register(user_data: UserCreate):
        # user_data is automatically validated
        # Response is automatically serialized to TokenResponse format
        pass
"""

# =============================================================================
# USER MODELS
# =============================================================================
# Models for user registration, authentication, and profile management
from .user import (
    UserCreate,          # Registration form data
    UserLogin,           # Login credentials (email + password)
    UserResponse,        # Public user profile (no password)
    UserUpdate,          # Profile update form
    TokenResponse,       # JWT token + user data
    OTPRequest,          # Request to send OTP
    OTPVerify,           # OTP verification request
    OTPResponse,         # OTP send confirmation
    OTPVerifyResponse,   # OTP verification result
)

# =============================================================================
# PRODUCT MODELS
# =============================================================================
# Models for product catalog and categories
from .product import (
    ProductCreate,       # Create product (admin)
    ProductUpdate,       # Update product (admin)
    ProductResponse,     # Product details for display
    CategoryResponse,    # Category information
)

# =============================================================================
# CART MODELS
# =============================================================================
# Models for shopping cart operations
from .cart import (
    CartItemAdd,         # Add item to cart
    CartItemUpdate,      # Update cart item quantity
    CartResponse,        # Full cart with all items
    CartItemResponse,    # Single cart item details
)

# =============================================================================
# ORDER MODELS
# =============================================================================
# Models for order placement and management
from .order import (
    OrderCreate,         # Place new order
    OrderResponse,       # Order details
    OrderItemResponse,   # Order line item
    PaymentInfo,         # Payment method and details
    OrderStatus,         # Order status enum
)

# =============================================================================
# ADDRESS MODELS
# =============================================================================
# Models for shipping address management
from .address import (
    AddressCreate,       # Create new address
    AddressUpdate,       # Update existing address
    AddressResponse,     # Address details
)

# =============================================================================
# PUBLIC EXPORTS
# =============================================================================
# List of all models available when importing from app.models
# Usage: from app.models import UserCreate, TokenResponse
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
