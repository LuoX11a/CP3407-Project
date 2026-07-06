"""Tests for auth endpoints — register and login."""

import pytest
from unittest.mock import patch, MagicMock


class TestRegisterEndpoint:
    def test_register_validation_rejects_short_password(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "ab", "email": "test@test.com", "password": "12345"},
        )
        assert response.status_code == 422  # Pydantic validation error

    def test_register_validation_rejects_short_username(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "a", "email": "test@test.com", "password": "123456"},
        )
        assert response.status_code == 422

    def test_register_success(self, client):
        mock_user = {"id": 1}
        with patch("app.routers.auth.psycopg2.connect") as mock_conn:
            cur = MagicMock()
            cur.fetchone.return_value = None  # No existing user
            cur2 = MagicMock()
            cur2.fetchone.return_value = mock_user
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.side_effect = [
                cur, cur2
            ]
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__exit__ = MagicMock(
                return_value=False
            )

            response = client.post(
                "/api/v1/auth/register",
                json={"username": "newuser", "email": "new@test.com", "password": "password123"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == "newuser"


class TestLoginEndpoint:
    def test_login_validation_requires_username(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "somepass"},
        )
        assert response.status_code == 422

    def test_login_invalid_credentials(self, client):
        with patch("app.routers.auth.psycopg2.connect") as mock_conn:
            cur = MagicMock()
            cur.fetchone.return_value = None  # User not found
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
                cur
            )
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__exit__ = MagicMock(
                return_value=False
            )

            response = client.post(
                "/api/v1/auth/login",
                json={"username": "nobody", "password": "wrong"},
            )

        assert response.status_code == 401


class TestProtectedEndpoint:
    def test_favourites_requires_auth(self, client):
        response = client.get("/api/v1/favourites")
        assert response.status_code == 401

    def test_favourites_with_valid_token(self, client, auth_headers):
        with patch("app.routers.favourites.psycopg2.connect") as mock_conn:
            cur = MagicMock()
            cur.fetchall.return_value = []
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
                cur
            )
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__exit__ = MagicMock(
                return_value=False
            )

            response = client.get("/api/v1/favourites", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "favourites" in data
