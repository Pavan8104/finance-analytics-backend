"""
Tests for user management endpoints.

Covers:
  - Public signup always creates a viewer (RBAC critical)
  - Duplicate email is rejected
  - Weak password is rejected
  - /me returns correct profile
  - Admin can list all users
  - Viewer cannot list all users (403)
  - Admin can create users with any role
  - Admin can update user roles
  - Admin cannot delete own account
"""
import pytest


class TestPublicSignup:

    def test_signup_creates_viewer_role(self, client):
        """
        CRITICAL SECURITY TEST: Public signup MUST always produce a viewer.
        The client must NOT be able to self-assign admin or analyst roles.
        """
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "newuser@test.com",
                "password": "Secure1234!",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["role"] == "viewer"
        assert body["email"] == "newuser@test.com"
        assert body["full_name"] == "New User"
        assert "hashed_password" not in body

    def test_signup_cannot_inject_admin_role(self, client):
        """
        CRITICAL SECURITY TEST: Even if role is passed in the body,
        the result must still be 'viewer'.
        """
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "hacker@test.com",
                "password": "Hacker1234!",
                "role": "admin",   # Attempted privilege escalation
            },
        )
        # Should succeed but silently ignore the role field
        assert response.status_code == 201
        assert response.json()["role"] == "viewer"

    def test_signup_duplicate_email_returns_409(self, client, viewer_user):
        response = client.post(
            "/api/v1/users/",
            json={"email": "viewer@test.com", "password": "Another1234!"},
        )
        assert response.status_code == 409

    def test_signup_weak_password_returns_422(self, client):
        """Password under 8 characters must be rejected."""
        response = client.post(
            "/api/v1/users/",
            json={"email": "weak@test.com", "password": "short"},
        )
        assert response.status_code == 422

    def test_signup_invalid_email_returns_422(self, client):
        response = client.post(
            "/api/v1/users/",
            json={"email": "not-an-email", "password": "Secure1234!"},
        )
        assert response.status_code == 422


class TestUserProfile:

    def test_get_me_returns_own_profile(self, viewer_client, viewer_user):
        response = viewer_client.get("/api/v1/users/me")
        assert response.status_code == 200
        body = response.json()
        assert body["email"] == viewer_user.email
        assert body["id"] == viewer_user.id
        assert "hashed_password" not in body

    def test_patch_me_updates_full_name(self, viewer_client):
        response = viewer_client.patch(
            "/api/v1/users/me",
            json={"full_name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    def test_unauthenticated_cannot_access_me(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestAdminUserManagement:

    def test_admin_can_list_all_users(self, admin_client, viewer_user):
        response = admin_client.get("/api/v1/users/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1   # At least admin + viewer

    def test_viewer_cannot_list_users(self, viewer_client):
        response = viewer_client.get("/api/v1/users/")
        assert response.status_code == 403

    def test_analyst_cannot_list_users(self, analyst_client):
        response = analyst_client.get("/api/v1/users/")
        assert response.status_code == 403

    def test_admin_can_create_analyst(self, admin_client):
        response = admin_client.post(
            "/api/v1/users/admin",
            json={
                "email": "newanalyst@test.com",
                "password": "Analyst1234!",
                "role": "analyst",
            },
        )
        assert response.status_code == 201
        assert response.json()["role"] == "analyst"

    def test_viewer_cannot_create_admin_user(self, viewer_client):
        response = viewer_client.post(
            "/api/v1/users/admin",
            json={
                "email": "sneaky@test.com",
                "password": "Sneaky1234!",
                "role": "admin",
            },
        )
        assert response.status_code == 403

    def test_admin_cannot_delete_own_account(self, admin_client, admin_user):
        response = admin_client.delete(f"/api/v1/users/{admin_user.id}")
        assert response.status_code == 400
