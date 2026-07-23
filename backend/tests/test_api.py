"""API endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = await client.post("/api/auth/login", json={
        "email": "nonexistent@test.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    """Test that protected endpoints require authentication."""
    response = await client.get("/api/projects")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_me_without_token(client):
    """Test get current user without token."""
    response = await client.get("/api/auth/me")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_dashboard_stats_without_token(client):
    """Test dashboard stats require auth."""
    response = await client.get("/api/dashboard/stats")
    assert response.status_code in [401, 403]
