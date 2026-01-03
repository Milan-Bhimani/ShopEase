"""
Tests for order endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock


class TestOrderEndpoints:
    """Test suite for order endpoints."""

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.order_repo.get_user_orders')
    def test_list_orders_empty(self, mock_orders, mock_user_get, client, auth_headers, mock_user):
        """Test listing orders when user has no orders."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_orders.return_value = AsyncMock(return_value=[])()

        response = client.get("/api/orders", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["orders"] == []
        assert data["total"] == 0

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.order_repo.get_user_orders')
    def test_list_orders_with_orders(self, mock_orders, mock_user_get, client, auth_headers, mock_user, mock_order):
        """Test listing orders when user has orders."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_orders.return_value = AsyncMock(return_value=[mock_order])()

        response = client.get("/api/orders", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 1
        assert data["orders"][0]["order_number"] == mock_order["order_number"]

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.order_repo.get_by_id')
    def test_get_order(self, mock_order_get, mock_user_get, client, auth_headers, mock_user, mock_order):
        """Test getting a specific order."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_order_get.return_value = AsyncMock(return_value=mock_order)()

        response = client.get(f"/api/orders/{mock_order['id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_order["id"]

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.order_repo.get_by_id')
    def test_get_order_not_found(self, mock_order_get, mock_user_get, client, auth_headers, mock_user):
        """Test getting a non-existent order."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_order_get.return_value = AsyncMock(return_value=None)()

        response = client.get("/api/orders/nonexistent-order", headers=auth_headers)

        assert response.status_code == 404

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.address_repo.get_by_id')
    @patch('app.firebase.cart_repo.get_user_cart')
    @patch('app.firebase.product_repo.get_by_id')
    @patch('app.firebase.order_repo.create')
    @patch('app.firebase.product_repo.update')
    @patch('app.firebase.cart_repo.clear_cart')
    def test_create_order_cod(
        self, mock_clear_cart, mock_product_update, mock_order_create,
        mock_product_get, mock_cart_get, mock_address_get, mock_user_get,
        client, auth_headers, mock_user, mock_address, mock_cart, mock_product
    ):
        """Test creating an order with Cash on Delivery."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_address_get.return_value = AsyncMock(return_value=mock_address)()
        mock_cart_get.return_value = AsyncMock(return_value=mock_cart)()
        mock_product_get.return_value = AsyncMock(return_value=mock_product)()
        mock_order_create.return_value = AsyncMock(return_value="new-order-123")()
        mock_product_update.return_value = AsyncMock(return_value=True)()
        mock_clear_cart.return_value = AsyncMock(return_value=True)()

        response = client.post("/api/orders", json={
            "address_id": mock_address["id"],
            "payment": {
                "method": "cod"
            }
        }, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] == True
        assert data["payment_method"] == "cod"

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.address_repo.get_by_id')
    @patch('app.firebase.cart_repo.get_user_cart')
    @patch('app.firebase.product_repo.get_by_id')
    @patch('app.firebase.order_repo.create')
    @patch('app.firebase.product_repo.update')
    @patch('app.firebase.cart_repo.clear_cart')
    def test_create_order_card(
        self, mock_clear_cart, mock_product_update, mock_order_create,
        mock_product_get, mock_cart_get, mock_address_get, mock_user_get,
        client, auth_headers, mock_user, mock_address, mock_cart, mock_product
    ):
        """Test creating an order with card payment."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_address_get.return_value = AsyncMock(return_value=mock_address)()
        mock_cart_get.return_value = AsyncMock(return_value=mock_cart)()
        mock_product_get.return_value = AsyncMock(return_value=mock_product)()
        mock_order_create.return_value = AsyncMock(return_value="new-order-123")()
        mock_product_update.return_value = AsyncMock(return_value=True)()
        mock_clear_cart.return_value = AsyncMock(return_value=True)()

        response = client.post("/api/orders", json={
            "address_id": mock_address["id"],
            "payment": {
                "method": "card",
                "card_last_four": "4242",
                "card_brand": "Visa"
            }
        }, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] == True
        assert data["payment_method"] == "card"

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.address_repo.get_by_id')
    def test_create_order_invalid_address(self, mock_address_get, mock_user_get, client, auth_headers, mock_user):
        """Test creating order with invalid address."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_address_get.return_value = AsyncMock(return_value=None)()

        response = client.post("/api/orders", json={
            "address_id": "invalid-address",
            "payment": {"method": "cod"}
        }, headers=auth_headers)

        assert response.status_code == 400

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.order_repo.get_by_id')
    @patch('app.firebase.order_repo.update')
    @patch('app.firebase.product_repo.get_by_id')
    @patch('app.firebase.product_repo.update')
    def test_cancel_order(self, mock_product_update, mock_product_get, mock_order_update, mock_order_get, mock_user_get, client, auth_headers, mock_user, mock_order, mock_product):
        """Test canceling an order."""
        pending_order = {**mock_order, "status": "pending"}
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_order_get.return_value = AsyncMock(return_value=pending_order)()
        mock_order_update.return_value = AsyncMock(return_value=True)()
        mock_product_get.return_value = AsyncMock(return_value=mock_product)()
        mock_product_update.return_value = AsyncMock(return_value=True)()

        response = client.post(f"/api/orders/{mock_order['id']}/cancel", headers=auth_headers)

        assert response.status_code == 200
        assert "cancelled" in response.json()["message"].lower()

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.order_repo.get_by_id')
    def test_cancel_shipped_order(self, mock_order_get, mock_user_get, client, auth_headers, mock_user, mock_order):
        """Test canceling a shipped order (should fail)."""
        shipped_order = {**mock_order, "status": "shipped"}
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_order_get.return_value = AsyncMock(return_value=shipped_order)()

        response = client.post(f"/api/orders/{mock_order['id']}/cancel", headers=auth_headers)

        assert response.status_code == 400

    @patch('app.firebase.user_repo.get_by_id')
    @patch('app.firebase.order_repo.get_by_id')
    def test_track_order(self, mock_order_get, mock_user_get, client, auth_headers, mock_user, mock_order):
        """Test tracking an order."""
        mock_user_get.return_value = AsyncMock(return_value=mock_user)()
        mock_order_get.return_value = AsyncMock(return_value=mock_order)()

        response = client.get(f"/api/orders/{mock_order['id']}/track", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "timeline" in data
        assert data["order_number"] == mock_order["order_number"]
