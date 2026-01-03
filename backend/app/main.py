"""
E-Commerce API - Main FastAPI Application

A RESTful API for e-commerce operations including:
- User authentication (JWT-based)
- Product catalog management
- Shopping cart operations
- Order processing with multiple payment methods
- Address management

Designed to work with Google Firebase Firestore as the database.
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

# Import routers
from .auth.routes import router as auth_router
from .routes.users import router as users_router
from .routes.products import router as products_router
from .routes.cart import router as cart_router
from .routes.addresses import router as addresses_router
from .routes.orders import router as orders_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting E-Commerce API...")

    settings = get_settings()

    # Initialize Firebase
    try:
        init_firebase()
        logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        # In development, we can continue without Firebase
        if not settings.DEBUG:
            raise

    logger.info(f"API running in {'DEBUG' if settings.DEBUG else 'PRODUCTION'} mode")

    yield

    # Shutdown
    logger.info("Shutting down E-Commerce API...")


# Create FastAPI application
settings = get_settings()

app = FastAPI(
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
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
    )


# Health check endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }


# Register API routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(addresses_router, prefix="/api")
app.include_router(orders_router, prefix="/api")


# Serve static files (frontend) if the directory exists
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


# Root redirect to docs when no frontend
@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation."""
    return {"message": "Welcome to E-Commerce API", "docs": "/api/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
