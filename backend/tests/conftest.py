"""Shared fixtures for ParkGuideSG API tests."""

import sys
from pathlib import Path

# Ensure backend/ is on PYTHONPATH so `from app.xxx` imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import MagicMock, patch
import os

os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/testdb"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["MODEL_PATH"] = "/nonexistent/model.joblib"

# ── Mock heavy / DB-dependent modules before any app import ────

_mock_psycopg2 = MagicMock()
_mock_psycopg2.extras = MagicMock()
sys.modules["psycopg2"] = _mock_psycopg2
sys.modules["psycopg2.extras"] = _mock_psycopg2.extras

for _mod in ("lightgbm", "joblib", "pandas"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Prevent lifespan() from trying to connect to a real DB or load a real model
import app.services.inference as _inf
_inf.load_model = MagicMock()
_inf.is_model_loaded = MagicMock(return_value=True)


import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    """Create FastAPI app once per test session."""
    from app.main import app
    app.dependency_overrides = {}
    return app


@pytest.fixture
def client(app):
    """TestClient bound to the session-scoped app."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Valid auth headers for a test user."""
    from app.services.auth import create_token
    token = create_token(user_id=1, username="testuser")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_db():
    """Configure psycopg2.connect mock for a single test.

    Returns (mock_connect, mock_cursor) so tests can set fetchone/fetchall.
    """
    cur = MagicMock()
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = False

    with patch.object(_mock_psycopg2, "connect", return_value=conn):
        yield conn, cur
