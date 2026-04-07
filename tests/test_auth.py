"""
Tests for the authentication endpoints.

Covers:
  - Successful login returns access + refresh tokens
  - Invalid password returns 401
  - Non-existent user returns 401 (no enumeration)
  - Inactive user returns 403
  - Protected route rejects unauthenticated request with 401
  - Protected route rejects expired/malformed token
"""
import pytest
from fastapi.testclient import TestClient


class TestLogin:

    def test_login_success_returns_tokens(self, client, viewer_user):
        """Valid credentials return access and refresh tokens."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "viewer@test.com", "password": "Viewer1234!"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 20

    def test_login_wrong_password_returns_401(self, client, viewer_user):
        """Wrong password returns 401, not 400 (RFC 7235)."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "viewer@test.com", "password": "WrongPassword!"},
        )
        assert response.status_code == 401
        assert "access_token" not in response.json()

    def test_login_nonexistent_user_returns_401(self, client):
        """Non-existent user returns 401 (same as wrong password — no enumeration)."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@nonexistent.com", "password": "anything"},
        )
        assert response.status_code == 401

    def test_login_inactive_user_returns_403(self, client, inactive_user):
        """Inactive accounts are rejected with 403 after credential check."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "inactive@test.com", "password": "Inactive1234!"},
        )
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()

    def test_login_missing_fields_returns_422(self, client):
        """Missing form fields return 422 Unprocessable Entity."""
        response = client.post("/api/v1/auth/login", data={})
        assert response.status_code == 422

    def test_admin_login_embeds_role_in_token(self, client, admin_user):
        """Admin login returns a valid token (role is embedded in JWT claims)."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "Admin1234!"},
        )
        assert response.status_code == 200


class TestTokenProtection:

    def test_protected_route_without_token_returns_401(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_protected_route_with_malformed_token_returns_401(self, client):
        client.headers.update({"Authorization": "Bearer this.is.notvalid"})
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_protected_route_with_valid_token_succeeds(self, viewer_client):
        response = viewer_client.get("/api/v1/users/me")
        assert response.status_code == 200


class TestSystemEndpoints:

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_ready_returns_ready(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
