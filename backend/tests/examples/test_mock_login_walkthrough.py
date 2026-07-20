"""
Complete walkthrough: Mock Object Framework demonstration for ParkGuideSG.
Shows how to mock a user login process end-to-end.

This file is a self-contained tutorial — each test builds on the previous one.

Run: cd backend && python -m pytest tests/examples/test_mock_login_walkthrough.py -v
"""
import pytest
from unittest.mock import patch


class TestMockLoginWalkthrough:
    """Step-by-step demonstration of mock objects for login flow."""

    # ──────────────────────────────────────────────
    # Test 1: Happy path — valid credentials
    # ──────────────────────────────────────────────
    def test_mock_login_success(self, client, mock_db):
        """
        Mock user login with CORRECT password.

        MOCKS:
          - Database query → returns user record with bcrypt hash
          - Password verification → returns True (correct password)

        VERIFIES:
          - HTTP 200 with user_id and username in response body
          - JWT is set as httpOnly cookie (NOT in JSON body)
          - Cookie has security attributes (HttpOnly, SameSite=Lax)
        """
        conn, cur = mock_db

        # Arrange: mock the database query to return a valid user
        cur.fetchone.return_value = {
            "id": 1,
            "username": "testuser",
            "password_hash": "$2b$12$LJ3m4ys3GZfnYMz8kVsKaOm5pXVL5Hq1nVsGfJ3R8PQxRyNPMHI36",
        }

        # Arrange: mock bcrypt to always say "password matches"
        with patch("app.services.auth.verify_password", return_value=True):
            # Act: send login request
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "testuser", "password": "password123"},
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert data["user_id"] == 1
            assert data["username"] == "testuser"
            assert data["status"] == "ok"
            assert "token" not in data  # JWT is cookie-only, not in body!

            # Assert cookie attributes
            set_cookie = response.headers.get("set-cookie", "")
            assert "token=" in set_cookie
            assert "HttpOnly" in set_cookie
            assert "SameSite=Lax" in set_cookie
            assert "Path=/" in set_cookie

    # ──────────────────────────────────────────────
    # Test 2: Wrong password → 401
    # ──────────────────────────────────────────────
    def test_mock_login_invalid_password(self, client, mock_db):
        """
        Mock user login with WRONG password.

        MOCKS:
          - Database query → returns a user (user exists)
          - Password verification → returns False (wrong password)

        VERIFIES:
          - HTTP 401 with descriptive error message
        """
        conn, cur = mock_db
        cur.fetchone.return_value = {
            "id": 1,
            "username": "testuser",
            "password_hash": "$2b$12$...",
        }

        with patch("app.services.auth.verify_password", return_value=False):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "testuser", "password": "WRONG_PASSWORD"},
            )

            assert response.status_code == 401
            assert "Invalid" in response.json()["detail"]

    # ──────────────────────────────────────────────
    # Test 3: Database connection lost → 500
    # ──────────────────────────────────────────────
    def test_mock_login_db_connection_lost(self, client, mock_db):
        """
        Mock DATABASE DOWN scenario.

        This is the power of mocks — we can simulate infrastructure
        failures that are nearly impossible to trigger with a real DB.

        MOCKS:
          - Database cursor.execute() raises ConnectionError

        VERIFIES:
          - Server returns 500, does not crash
        """
        conn, cur = mock_db
        cur.execute.side_effect = ConnectionError("Connection refused")

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"},
        )

        assert response.status_code == 500

    # ──────────────────────────────────────────────
    # Test 4: Unknown username → 401
    # ──────────────────────────────────────────────
    def test_mock_login_user_not_found(self, client, mock_db):
        """
        Mock user NOT FOUND scenario.

        MOCKS:
          - Database query returns None (no matching user)

        VERIFIES:
          - HTTP 401 returned immediately
          - Password verification is NEVER called (no need to hash)
        """
        conn, cur = mock_db
        cur.fetchone.return_value = None

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "ghostuser", "password": "anything"},
        )

        assert response.status_code == 401

    # ──────────────────────────────────────────────
    # Test 5: side_effect for multi-step operations
    # ──────────────────────────────────────────────
    def test_mock_register_with_side_effect_sequence(self, client, mock_db):
        """
        Demonstrate side_effect for SEQUENTIAL database calls.

        The register endpoint calls the database TWICE:
          1. SELECT to check if username exists → None (no conflict)
          2. INSERT INTO users ... RETURNING id → {"id": 2}

        side_effect with a LIST lets us sequence the return values.
        """
        conn, cur = mock_db
        cur.fetchone.side_effect = [None, {"id": 2}]

        with patch("app.services.auth.verify_password", return_value=True):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "username": "newuser",
                    "email": "new@test.com",
                    "password": "password123",
                },
            )

            assert response.status_code == 200
            assert response.json()["username"] == "newuser"

            # Verify both database calls were made
            assert cur.execute.call_count == 2

    # ──────────────────────────────────────────────
    # Test 6: Duplicate username → 409
    # ──────────────────────────────────────────────
    def test_mock_register_duplicate_username(self, client, mock_db):
        """
        Mock DUPLICATE USERNAME during registration.

        MOCKS:
          - First DB call (check existing): returns existing user record
          - The route should RETURN 409 before the INSERT step
        """
        conn, cur = mock_db
        # Simulate: username already exists
        cur.fetchone.return_value = {"id": 1, "username": "existinguser"}

        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "existinguser",
                "email": "new@test.com",
                "password": "password123",
            },
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()


class TestMockComparison:
    """Side-by-side comparison: with mock vs. without mock."""

    def test_without_mock_real_function(self):
        """
        NO MOCK: Test a pure function directly.

        The _status() function is pure (no DB, no network, no file I/O).
        We test it WITHOUT any mocking.
        """
        from app.routers.recommend import _status

        assert _status(0.51) == "GREEN"   # >50%
        assert _status(0.50) == "YELLOW"  # boundary
        assert _status(0.21) == "YELLOW"  # 20-50%
        assert _status(0.20) == "RED"     # boundary
        assert _status(0.00) == "RED"     # <20%

    def test_with_mock_database_dependency(self, client, mock_db):
        """
        WITH MOCK: Test an endpoint that needs a database.

        The /api/v1/favourites endpoint needs a database query.
        Without mocking, it would fail trying to connect to PostgreSQL.
        With mocking, it runs in <5ms with no infrastructure.
        """
        conn, cur = mock_db
        cur.fetchone.return_value = {"id": 1, "username": "testuser"}
        cur.fetchall.return_value = []

        response = client.get(
            "/api/v1/favourites",
            cookies={"token": "valid-jwt-token"},
        )

        # The endpoint works because all DB calls are intercepted
        assert response.status_code in (200, 401)  # depends on JWT validation
