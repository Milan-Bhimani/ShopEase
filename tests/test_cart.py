"""
Tests for cart endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock


class TestCartEndpoints:
    """Test suite for shopping cart endpoints."""

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.cart_repo.get_user_cart')
    @patch('app.firebase.cart_repo.create')
    @patch('app.firebase.cart_repo.get_by_id')
    def test_get_empty_cart(self, mock_cart_get, mock_create, mock_user_cart, mock_user, client, auth_headers, mock_user):
        """Test getting an empty cart."""
        mock_user.return_value = AsyncMock(return_value=mock_user)()
        mock_user_cart.return_value = AsyncMock(return_value=None)()
        mock_create.return_value = AsyncMock(return_value="new-cart-123")()
        mock_cart_get.return_value = AsyncMock(return_value={
            "id": "new-cart-123",
            "user_id": mock_user["id"],
            "items": [],
        })()

        response = client.get("/api/cart", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["item_count"] == 0

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.cart_repo.get_user_cart')
    @patch('app.firebase.product_repo.get_by_id')
    def test_get_cart_with_items(self, mock_product, mock_user_cart, mock_user_get, client, auth_headers, mock_user, mock_product, mock_cart):
        """Test getting cart with items."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_user_cart.return_value = AsyncMock(return_value=mock_cart)()
        mock_product.return_value = AsyncMock(return_value=mock_product)()

        response = client.get("/api/cart", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        assert data["item_count"] > 0

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.product_repo.get_by_id')
    @patch('app.firebase.cart_repo.get_user_cart')
    @patch('app.firebase.cart_repo.create')
    @patch('app.firebase.cart_repo.update')
    @patch('app.firebase.cart_repo.get_by_id')
    def test_add_to_cart(self, mock_cart_get, mock_update, mock_create, mock_user_cart, mock_product_get, mock_user_get, client, auth_headers, mock_user, mock_product):
        """Test adding item to cart."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_product_get.return_value = AsyncMock(return_value=mock_product)()
        mock_user_cart.return_value = AsyncMock(return_value={
            "id": "cart-123",
            "user_id": mock_user["id"],
            "items": [],
        })()
        mock_update.return_value = AsyncMock(return_value=True)()
        mock_cart_get.return_value = AsyncMock(return_value={
            "id": "cart-123",
            "user_id": mock_user["id"],
            "items": [{"product_id": mock_product["id"], "quantity": 1}],
        })()

        response = client.post("/api/cart/items", json={
            "product_id": mock_product["id"],
            "quantity": 1,
        }, headers=auth_headers)

        assert response.status_code == 200

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.product_repo.get_by_id')
    def test_add_to_cart_product_not_found(self, mock_product_get, mock_user_get, client, auth_headers, mock_user):
        """Test adding non-existent product to cart."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_product_get.return_value = AsyncMock(return_value=None)()

        response = client.post("/api/cart/items", json={
            "product_id": "nonexistent-product",
            "quantity": 1,
        }, headers=auth_headers)

        assert response.status_code == 404

    def test_add_to_cart_no_auth(self, client):
        """Test adding to cart without authentication."""
        response = client.post("/api/cart/items", json={
            "product_id": "prod-123",
            "quantity": 1,
        })

        assert response.status_code == 401

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.cart_repo.get_user_cart')
    @patch('app.firebase.product_repo.get_by_id')
    @patch('app.firebase.cart_repo.update')
    @patch('app.firebase.cart_repo.get_by_id')
    def test_update_cart_item(self, mock_cart_get, mock_update, mock_product_get, mock_user_cart, mock_user_get, client, auth_headers, mock_user, mock_product, mock_cart):
        """Test updating cart item quantity."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_user_cart.return_value = AsyncMock(return_value=mock_cart)()
        mock_product_get.return_value = AsyncMock(return_value=mock_product)()
        mock_update.return_value = AsyncMock(return_value=True)()
        mock_cart_get.return_value = AsyncMock(return_value={
            **mock_cart,
            "items": [{"product_id": mock_product["id"], "quantity": 3}],
        })()

        response = client.put(f"/api/cart/items/{mock_product['id']}", json={
            "quantity": 3,
        }, headers=auth_headers)

        assert response.status_code == 200

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.cart_repo.get_user_cart')
    @patch('app.firebase.cart_repo.update')
    @patch('app.firebase.cart_repo.get_by_id')
    def test_remove_from_cart(self, mock_cart_get, mock_update, mock_user_cart, mock_user_get, client, auth_headers, mock_user, mock_product, mock_cart):
        """Test removing item from cart."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_user_cart.return_value = AsyncMock(return_value=mock_cart)()
        mock_update.return_value = AsyncMock(return_value=True)()
        mock_cart_get.return_value = AsyncMock(return_value={
            **mock_cart,
            "items": [],
        })()

        response = client.delete(f"/api/cart/items/{mock_product['id']}", headers=auth_headers)

        assert response.status_code == 200

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.cart_repo.clear_cart')
    def test_clear_cart(self, mock_clear, mock_user_get, client, auth_headers, mock_user):
        """Test clearing cart."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_clear.return_value = AsyncMock(return_value=True)()

        response = client.delete("/api/cart", headers=auth_headers)

        assert response.status_code == 204
