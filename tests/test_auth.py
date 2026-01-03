"""
Tests for authentication endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock


class TestAuthEndpoints:
    """Test suite for authentication endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @patch('app.firebase.user_repo.get_by_email')
    @patch('app.firebase.user_repo.create')
    def test_register_success(self, mock_create, mock_get_email, client):
        """Test successful user registration."""
        mock_get_email.return_value = AsyncMock(return_value=None)()
        mock_create.return_value = AsyncMock(return_value="new-user-123")()

        response = client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "first_name": "New",
            "last_name": "User",
        })

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post("/api/auth/register", json={
            "email": "invalid-email",
            "password": "SecurePass123",
            "first_name": "Test",
            "last_name": "User",
        })

        assert response.status_code == 422  # Validation error

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "weak",  # Too short, no uppercase, no digits
            "first_name": "Test",
            "last_name": "User",
        })

        assert response.status_code == 422

    @patch('app.firebase.user_repo.get_by_email')
    def test_register_duplicate_email(self, mock_get_email, client, mock_user):
        """Test registration with existing email."""
        mock_get_email.return_value = AsyncMock(return_value=mock_user)()

        response = client.post("/api/auth/register", json={
            "email": mock_user["email"],
            "password": "SecurePass123",
            "first_name": "Test",
            "last_name": "User",
        })

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @patch('app.firebase.user_repo.get_by_email')
    def test_login_success(self, mock_get_email, client, mock_user):
        """Test successful login."""
        mock_get_email.return_value = AsyncMock(return_value=mock_user)()

        response = client.post("/api/auth/login", json={
            "email": mock_user["email"],
            "password": "TestPass123",
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == mock_user["email"]

    @patch('app.firebase.user_repo.get_by_email')
    def test_login_wrong_password(self, mock_get_email, client, mock_user):
        """Test login with wrong password."""
        mock_get_email.return_value = AsyncMock(return_value=mock_user)()

        response = client.post("/api/auth/login", json={
            "email": mock_user["email"],
            "password": "WrongPassword123",
        })

        assert response.status_code == 401

    @patch('app.firebase.user_repo.get_by_email')
    def test_login_nonexistent_user(self, mock_get_email, client):
        """Test login with non-existent user."""
        mock_get_email.return_value = AsyncMock(return_value=None)()

        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "TestPass123",
        })

        assert response.status_code == 401

    @patch('app.firebase.user_repo.get_by_id')
    def test_get_current_user(self, mock_get_by_id, client, mock_user, auth_headers):
        """Test getting current user profile."""
        mock_get_by_id.return_value = AsyncMock(return_value=mock_user)()

        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == mock_user["email"]

    def test_get_current_user_no_auth(self, client):
        """Test getting current user without authentication."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid-token"
        })

        assert response.status_code == 401
