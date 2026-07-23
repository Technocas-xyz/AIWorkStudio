"""Authentication tests."""

import pytest
from app.services.auth_service import AuthService


class TestAuthService:
    """Test authentication service."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)
        assert hashed != password
        assert AuthService.verify_password(password, hashed)

    def test_verify_wrong_password(self):
        """Test verification with wrong password."""
        hashed = AuthService.hash_password("CorrectPassword")
        assert not AuthService.verify_password("WrongPassword", hashed)

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "test-user-id"
        token = AuthService.create_access_token(user_id)
        assert token is not None
        assert len(token) > 0

    def test_decode_access_token(self):
        """Test token decoding."""
        user_id = "test-user-id"
        token = AuthService.create_access_token(user_id)
        payload = AuthService.decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "test-user-id"
        token = AuthService.create_refresh_token(user_id)
        payload = AuthService.decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        payload = AuthService.decode_token("invalid-token")
        assert payload is None


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
