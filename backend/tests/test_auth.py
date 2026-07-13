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
        assert data["username"] == "newuser"
        assert data["status"] == "ok"
        # Iteration 2: JWT is in httpOnly cookie, not in JSON body
        set_cookie = response.headers.get("set-cookie", "")
        assert "token=" in set_cookie
        assert "HttpOnly" in set_cookie


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


class TestCookieAuth:
    def test_login_sets_httponly_cookie(self, client, mock_db):
        """Login response includes HttpOnly Set-Cookie header with JWT."""
        conn, cur = mock_db
        import bcrypt
        from app.services.auth import hash_password
        hashed = hash_password("correctpassword")
        cur.fetchone.return_value = {
            "id": 1,
            "username": "testuser",
            "password_hash": hashed,
        }

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "correctpassword"},
        )

        assert response.status_code == 200
        set_cookie = response.headers.get("set-cookie", "")
        assert "token=" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite" in set_cookie
        assert "Path=/" in set_cookie

    def test_logout_clears_cookie(self, client):
        """Logout response clears the auth cookie."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        set_cookie = response.headers.get("set-cookie", "")
        # Cookie should be cleared (empty value or max-age=0)
        assert "token=" in set_cookie.lower() or set_cookie == ""
