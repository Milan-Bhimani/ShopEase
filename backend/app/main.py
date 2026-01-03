"""
==============================================================================
Main Application Module (main.py)
==============================================================================

PURPOSE:
--------
This is the entry point for the FastAPI application. It:
1. Creates and configures the FastAPI application instance
2. Sets up middleware (CORS, error handling)
3. Registers all API routers (endpoints)
4. Handles application lifecycle (startup/shutdown)
5. Optionally serves static frontend files

WHY FASTAPI?
------------
We chose FastAPI for this e-commerce backend because:

1. **Performance**: Built on Starlette and Pydantic, it's one of the fastest
   Python frameworks available, comparable to Node.js and Go.

2. **Type Safety**: Uses Python type hints for request/response validation,
   catching errors before they reach production.

3. **Automatic Documentation**: Generates interactive API docs (Swagger/OpenAPI)
   automatically from code - no manual documentation needed.

4. **Async Support**: Native async/await support for handling many concurrent
   connections efficiently (important for e-commerce with many simultaneous users).

5. **Easy to Learn**: Pythonic design makes it accessible while still being
   production-ready.

HOW THE APPLICATION STARTS:
---------------------------
1. FastAPI app is created with configuration from settings
2. Lifespan handler initializes Firebase connection
3. CORS middleware is added for cross-origin requests
4. All routers (auth, products, cart, etc.) are registered
5. Static files are served if frontend directory exists
6. Uvicorn ASGI server handles incoming HTTP requests

ARCHITECTURE OVERVIEW:
----------------------
    Request → CORS Middleware → Exception Handler → Router → Handler → Response
                                                      ↓
                                                  Firebase DB
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from .config import get_settings
from .firebase import init_firebase

# ==============================================================================
# ROUTER IMPORTS
# ==============================================================================
# Each router handles a specific domain of the API:
# - auth_router: Registration, login, logout, OTP verification
# - users_router: User profile management
# - products_router: Product listing, search, categories
# - cart_router: Shopping cart operations
# - addresses_router: Shipping address management
# - orders_router: Order creation and tracking
# - admin_router: Admin dashboard and management
from .auth.routes import router as auth_router
from .routes.users import router as users_router
from .routes.products import router as products_router
from .routes.cart import router as cart_router
from .routes.addresses import router as addresses_router
from .routes.orders import router as orders_router
from .routes.admin import router as admin_router

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================
# Configure logging to show timestamps, module names, and log levels
# This helps with debugging and monitoring in production
logging.basicConfig(
    level=logging.INFO,  # INFO level shows important events without being too verbose
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==============================================================================
# APPLICATION LIFESPAN HANDLER
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.

    This is FastAPI's modern way to handle startup/shutdown (replacing the
    deprecated @app.on_event decorators). The code before `yield` runs at
    startup, and code after `yield` runs at shutdown.

    Startup tasks:
    - Initialize Firebase connection (required for all database operations)
    - Log configuration mode (DEBUG or PRODUCTION)

    Shutdown tasks:
    - Clean logging (could add connection cleanup here if needed)

    Why use lifespan instead of on_event?
    - Cleaner resource management with context managers
    - Better support for async operations
    - Recommended by FastAPI for new applications
    """
    # ===== STARTUP =====
    logger.info("Starting E-Commerce API...")

    settings = get_settings()

    # Initialize Firebase connection
    # This must happen before any database operations
    try:
        init_firebase()
        logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        # In DEBUG mode, continue without Firebase (for testing)
        # In PRODUCTION, fail fast - the app can't work without a database
        if not settings.DEBUG:
            raise

    logger.info(f"API running in {'DEBUG' if settings.DEBUG else 'PRODUCTION'} mode")

    yield  # Application is running and handling requests

    # ===== SHUTDOWN =====
    logger.info("Shutting down E-Commerce API...")


# ==============================================================================
# FASTAPI APPLICATION INSTANCE
# ==============================================================================
settings = get_settings()

app = FastAPI(
    # Application metadata (shown in API documentation)
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## E-Commerce REST API

    A complete e-commerce backend API built with FastAPI and Firebase.

    ### Features:
    - **Authentication**: Secure JWT-based authentication with password hashing
    - **Products**: Browse, search, and filter products
    - **Cart**: Add, update, and remove cart items
    - **Orders**: Place orders with multiple payment methods
    - **Addresses**: Manage shipping addresses

    ### Authentication:
    Most endpoints require a Bearer token. Obtain one by registering or logging in.
    """,

    # Documentation endpoints - accessible at /api/docs and /api/redoc
    # These provide interactive API documentation for developers
    docs_url="/api/docs",      # Swagger UI (interactive testing)
    redoc_url="/api/redoc",    # ReDoc (better for reading)
    openapi_url="/api/openapi.json",  # Raw OpenAPI specification

    # Attach lifespan handler for startup/shutdown
    lifespan=lifespan,
)


# ==============================================================================
# CORS MIDDLEWARE CONFIGURATION
# ==============================================================================
# CORS (Cross-Origin Resource Sharing) allows the frontend (running on a
# different domain/port) to make requests to this API.
#
# Without CORS, browsers block requests from different origins for security.
# For example:
# - Frontend at http://localhost:3000
# - Backend at http://localhost:8000
# The browser would block requests without proper CORS headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),  # Which origins can access
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],     # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],     # Allow all headers (including Authorization)
)


# ==============================================================================
# GLOBAL EXCEPTION HANDLER
# ==============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle uncaught exceptions globally.

    This is a safety net that catches any exceptions not handled by specific
    route handlers. It:
    1. Logs the full error with stack trace for debugging
    2. Returns a generic error message to the client (doesn't expose internals)

    Why hide internal errors from clients?
    - Security: Error details might reveal system architecture
    - Professionalism: Users shouldn't see stack traces
    - Consistency: All errors have the same format

    In DEBUG mode, you might want to show more details.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
    )


# ==============================================================================
# HEALTH CHECK ENDPOINT
# ==============================================================================
@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring.

    This endpoint is used by:
    - Load balancers to check if the service is running
    - Monitoring systems (like UptimeRobot) to track uptime
    - Container orchestrators (like Kubernetes) for liveness probes

    It should be fast and not depend on external services (database, etc.)
    to give accurate service status.

    Returns:
        dict: Status and version information
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }


# ==============================================================================
# ROUTER REGISTRATION
# ==============================================================================
# Register all API routers with /api prefix
# Each router is a collection of related endpoints
# The prefix ensures all API endpoints start with /api/...
#
# Router organization:
# - /api/auth/*      - Authentication (login, register, OTP)
# - /api/users/*     - User profile management
# - /api/products/*  - Product catalog
# - /api/cart/*      - Shopping cart
# - /api/addresses/* - Shipping addresses
# - /api/orders/*    - Order management
# - /api/admin/*     - Admin dashboard (requires admin privileges)
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(addresses_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


# ==============================================================================
# STATIC FILE SERVING
# ==============================================================================
# Serve the frontend static files if they exist
# This allows running the entire application from a single server
#
# In production, you might use:
# - Nginx to serve static files (more efficient)
# - A CDN like Cloudflare or Firebase Hosting
# - Separate frontend deployment (Vercel, Netlify)
#
# The path calculation:
# __file__ = app/main.py
# dirname(__file__) = app/
# dirname again = backend/
# .. = project root
# /frontend = frontend directory
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend")
if os.path.exists(frontend_path):
    # html=True enables serving index.html for directory requests
    # This makes /products/ serve /products/index.html (SPA routing)
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


# ==============================================================================
# ROOT ENDPOINT (Fallback)
# ==============================================================================
@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint - redirects to API documentation.

    This is a fallback when:
    - Frontend is not available (served separately)
    - Someone accesses the API directly

    include_in_schema=False hides this from API documentation.
    """
    return {"message": "Welcome to E-Commerce API", "docs": "/api/docs"}


# ==============================================================================
# DIRECT EXECUTION (Development)
# ==============================================================================
# This block only runs when executing main.py directly:
#   python -m app.main
#
# In production, use: uvicorn app.main:app --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",           # Import path to app instance
        host=settings.HOST,        # Bind address (0.0.0.0 for all interfaces)
        port=settings.PORT,        # Port number (default 8000)
        reload=settings.DEBUG,     # Auto-reload on code changes (development only)
    )
