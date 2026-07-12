"""Shared fixtures for ParkGuideSG API tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock environment before importing app
import os

os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/testdb"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["MODEL_PATH"] = "/nonexistent/model.joblib"


@pytest.fixture
def client():
    """FastAPI TestClient with mocked database and model."""
    with patch("app.main.psycopg2"), patch("app.main.load_model"):
        from app.main import app

        app.dependency_overrides = {}
        return TestClient(app)


@pytest.fixture
def mock_db():
    """Return a MagicMock that simulates a psycopg2 connection."""
    conn = MagicMock()
    cur = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn


@pytest.fixture
def auth_headers():
    """Return valid auth headers for a test user."""
    from app.services.auth import create_token

    token = create_token(user_id=1, username="testuser")
    return {"Authorization": f"Bearer {token}"}
