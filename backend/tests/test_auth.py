"""Tests for auth endpoints — register and login."""


class TestRegisterEndpoint:
    def test_register_validation_rejects_short_password(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "ab", "email": "test@test.com", "password": "12345"},
        )
        assert response.status_code == 422

    def test_register_validation_rejects_short_username(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "a", "email": "test@test.com", "password": "123456"},
        )
        assert response.status_code == 422

    def test_register_success(self, client, mock_db):
        conn, cur = mock_db
        # First query: check existing user → None (no conflict)
        # Second query: INSERT RETURNING id → {"id": 1}
        cur.fetchone.side_effect = [None, {"id": 1}]

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

    def test_login_invalid_credentials(self, client, mock_db):
        conn, cur = mock_db
        cur.fetchone.return_value = None  # user not found

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "wrong"},
        )

        assert response.status_code == 401


class TestProtectedEndpoint:
    def test_favourites_requires_auth(self, client):
        response = client.get("/api/v1/favourites")
        assert response.status_code == 401

    def test_favourites_with_valid_token(self, client, auth_headers, mock_db):
        conn, cur = mock_db
        cur.fetchall.return_value = []

        response = client.get("/api/v1/favourites", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "favourites" in data
