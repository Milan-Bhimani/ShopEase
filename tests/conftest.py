"""
Pytest configuration and fixtures for e-commerce API tests.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Mock Firebase before importing app
mock_firestore = MagicMock()
mock_firebase_admin = MagicMock()

with patch.dict('sys.modules', {
    'firebase_admin': mock_firebase_admin,
    'firebase_admin.credentials': MagicMock(),
    'firebase_admin.firestore': mock_firestore,
    'google.cloud.firestore_v1': MagicMock(),
}):
    from app.main import app
    from app.auth.utils import hash_password, create_access_token


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "password_hash": hash_password("TestPass123"),
        "first_name": "Test",
        "last_name": "User",
        "phone": "9876543210",
        "is_active": True,
        "is_admin": False,
        "created_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def auth_token(mock_user):
    """Create authentication token for testing."""
    return create_access_token(data={"sub": mock_user["id"]})


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def mock_product():
    """Create a mock product for testing."""
    return {
        "id": "prod-123",
        "name": "Test Product",
        "name_lower": "test product",
        "description": "A test product description",
        "price": 999.00,
        "original_price": 1299.00,
        "category": "Electronics",
        "brand": "TestBrand",
        "stock_quantity": 50,
        "images": ["http://example.com/image1.jpg"],
        "thumbnail": "http://example.com/image1.jpg",
        "is_active": True,
        "is_featured": True,
        "tags": ["test", "electronics"],
        "rating": 4.5,
        "review_count": 100,
        "created_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_cart(mock_user, mock_product):
    """Create a mock cart for testing."""
    return {
        "id": "cart-123",
        "user_id": mock_user["id"],
        "items": [
            {
                "product_id": mock_product["id"],
                "quantity": 2,
            }
        ],
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_address(mock_user):
    """Create a mock address for testing."""
    return {
        "id": "addr-123",
        "user_id": mock_user["id"],
        "full_name": "Test User",
        "phone": "9876543210",
        "address_line1": "123 Test Street",
        "address_line2": "Apt 4B",
        "landmark": "Near Test Park",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001",
        "country": "India",
        "address_type": "home",
        "is_default": True,
        "created_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_order(mock_user, mock_product, mock_address):
    """Create a mock order for testing."""
    return {
        "id": "order-123",
        "order_number": "ORD-20240101-ABC123",
        "user_id": mock_user["id"],
        "items": [
            {
                "product_id": mock_product["id"],
                "product_name": mock_product["name"],
                "product_image": mock_product["thumbnail"],
                "price": mock_product["price"],
                "quantity": 2,
                "subtotal": mock_product["price"] * 2,
            }
        ],
        "shipping_address": {
            "full_name": mock_address["full_name"],
            "phone": mock_address["phone"],
            "address_line1": mock_address["address_line1"],
            "city": mock_address["city"],
            "state": mock_address["state"],
            "pincode": mock_address["pincode"],
            "country": mock_address["country"],
        },
        "status": "confirmed",
        "payment_method": "card",
        "payment_status": "completed",
        "transaction_id": "TXN-ABC123",
        "subtotal": mock_product["price"] * 2,
        "tax": mock_product["price"] * 2 * 0.18,
        "shipping_cost": 0,
        "discount": 0,
        "total": mock_product["price"] * 2 * 1.18,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "estimated_delivery": "2024-01-08",
    }
