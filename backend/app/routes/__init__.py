"""
==============================================================================
API Routes Package (routes/__init__.py)
==============================================================================

PURPOSE:
--------
This package contains all API route modules for the ShopEase e-commerce app.
Each module handles a specific domain of the API.

ROUTE MODULES:
--------------
1. products.py  - Product catalog (list, search, detail, admin CRUD)
2. cart.py      - Shopping cart operations (add, update, remove, clear)
3. orders.py    - Order management (create, list, cancel, track)
4. addresses.py - Shipping addresses (CRUD, default management)
5. users.py     - User profile (view, update, password change)

Note: Authentication routes are in auth/routes.py, not here.

HOW ROUTES ARE REGISTERED:
--------------------------
Routes are registered in main.py using app.include_router():
    from app.routes import products, cart, orders, addresses, users

    app.include_router(products.router, prefix="/api")
    app.include_router(cart.router, prefix="/api")
    ...

This gives endpoints like:
    /api/products
    /api/cart
    /api/orders
    /api/addresses
    /api/users

AUTHENTICATION:
---------------
Most routes require authentication via the get_current_user dependency.
Public routes (like product listing) use get_current_user_optional.
Admin routes (like product creation) use get_admin_user.

API DOCUMENTATION:
------------------
FastAPI auto-generates OpenAPI docs at /api/docs (Swagger UI)
and /api/redoc (ReDoc). The "tags" parameter on each router
groups endpoints in the documentation.
"""
