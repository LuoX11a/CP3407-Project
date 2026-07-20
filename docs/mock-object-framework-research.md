---
layout: default
title: Mock Object Framework Research
parent: Documentation
---

# Mock Object Framework — Research & Implementation

> **Date**: 2026-07-20  
> **Context**: Iteration 3 TDD — Understanding and applying mock objects to ParkGuideSG testing  
> **Reference**: Textbook Chapter 8 — Test-Driven Development

---

## 1. What Are Mock Objects?

Mock objects are **simulated objects that mimic the behavior of real objects in controlled ways**. In testing, they replace real dependencies (databases, APIs, file systems, ML models) so that:

| Without Mocks | With Mocks |
|--------------|------------|
| Tests need a running PostgreSQL instance | Tests run in memory, no DB needed |
| Tests depend on external API availability | Tests are deterministic and repeatable |
| 1 test takes 500ms (network + DB) | 1 test takes <5ms (pure memory) |
| Tests can fail due to network issues | Tests only fail due to code bugs |
| Hard to simulate edge cases (DB down, API timeout) | Easy: `mock.side_effect = TimeoutError()` |

### The Test Double Taxonomy

```
                    Test Doubles
                         │
          ┌──────────────┼──────────────┐
          │              │              │
        Dummy          Stub           Mock
     (placeholder)  (fixed return)  (expectation)
          │              │              │
          └──────────────┼──────────────┘
                         │
                       Fake
                 (lightweight impl)
```

| Type | What It Does | ParkGuideSG Example |
|------|-------------|-------------------|
| **Dummy** | Passed around but never used | `MagicMock()` assigned to `sys.modules["lightgbm"]` — prevents import errors |
| **Stub** | Returns pre-programmed answers | `cur.fetchone.return_value = {"id": 1, "username": "testuser"}` |
| **Mock** | Records calls + verifies expectations | `assert conn.cursor.called` — verifies DB was queried |
| **Fake** | Working implementation, but simplified | In-memory SQLite instead of PostgreSQL (not used in ParkGuideSG yet) |

---

## 2. Python: `unittest.mock` — The Standard Library Framework

### 2.1 Core Classes

```python
from unittest.mock import Mock, MagicMock, patch, PropertyMock
```

| Class | Behavior |
|-------|----------|
| `Mock` | Bare mock object. Any attribute access returns a new Mock. |
| `MagicMock` | `Mock` subclass with Python magic methods (`__len__`, `__iter__`, `__enter__`, `__exit__`) pre-implemented. **Use this by default.** |
| `PropertyMock` | Specialized mock for `@property` descriptors. |
| `AsyncMock` | (Python 3.8+) Mock for `async def` functions. |

### 2.2 Three Ways to Inject Mocks

#### Pattern A: Module-Level Injection (Heavy Dependencies)

Used in `conftest.py` to prevent importing heavyweight libraries:

```python
# conftest.py
from unittest.mock import MagicMock
import sys

# Replace real psycopg2 with mock BEFORE any app import
_mock_psycopg2 = MagicMock()
_mock_psycopg2.paramstyle = "pyformat"       # DBAPI 2.0 attribute
_mock_psycopg2.apilevel = "2.0"
sys.modules["psycopg2"] = _mock_psycopg2
sys.modules["lightgbm"] = MagicMock()
sys.modules["pandas"] = MagicMock()
```

**When to use**: Libraries that are slow to import, require native binaries, or need a database connection.

#### Pattern B: Fixture Injection (Per-Test Control)

Used for `mock_db` — each test gets fresh mocks:

```python
# conftest.py
@pytest.fixture
def mock_db():
    cur = MagicMock()
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cur
    # Mock the connection pool so get_sync_conn() returns our mock
    with patch("app.database._get_sync_pool",
               return_value=MagicMock(getconn=MagicMock(return_value=conn))):
        yield conn, cur
```

**When to use**: Dependencies that need per-test customization (different return values, different error conditions).

#### Pattern C: Context Manager Patch (Targeted Override)

Used for overriding specific functions in a single test:

```python
def test_health_degraded(self, client):
    with patch("app.routers.health.query_db_stats",
               return_value={"rows": 0, "uptime": "0s"}), \
         patch("app.routers.health.is_model_loaded",
               return_value=False):
        response = client.get("/api/v1/health")
        assert response.json()["status"] == "degraded"
```

**When to use**: Overriding 1-2 specific functions for a single test case.

### 2.3 Key Mock Configuration APIs

```python
# Fixed return value (Stub)
cur.fetchone.return_value = {"id": 1, "username": "testuser"}

# Different return per call (sequence)
cur.fetchone.side_effect = [
    None,           # 1st call: user not found (for duplicate check)
    {"id": 1},      # 2nd call: INSERT RETURNING id
]

# Raise an exception
cur.fetchone.side_effect = Exception("Database connection lost")

# Verify calls
conn.cursor.assert_called()                     # Was cursor() called at all?
cur.execute.assert_called_once()                # Exactly one call?
cur.execute.assert_called_with("SELECT ...")     # Called with specific SQL?

# Access call history
print(cur.execute.call_count)                   # How many times?
print(cur.execute.call_args_list)               # All call arguments
```

### 2.4 DBAPI 2.0 Compliance for Database Mocks

When mocking database drivers, the mock must expose DBAPI 2.0 attributes that SQLAlchemy/psycopg2 introspects:

```python
_mock_psycopg2 = MagicMock()
_mock_psycopg2.paramstyle = "pyformat"     # Required by SQLAlchemy
_mock_psycopg2.apilevel = "2.0"            # Required by DBAPI spec
_mock_psycopg2.threadsafety = 2            # Required by connection pool
_mock_psycopg2.__version__ = "2.9.9"       # Required by driver detection
_mock_psycopg2.extensions = MagicMock()    # Required by psycopg2 internals
_mock_psycopg2._psycopg = MagicMock()      # Required by asyncpg compat
```

---

## 3. JavaScript: Vitest Mocking

### 3.1 Core APIs

```javascript
import { vi, describe, it, expect, beforeEach } from "vitest";

// Mock a module
vi.mock("../services/api", () => ({
  fetchRecommendations: vi.fn(),
  searchCarparks: vi.fn(),
}));

// Mock global objects
global.fetch = vi.fn();

// Spy on a method (track calls, keep original behavior)
const spy = vi.spyOn(console, "log");

// Create a mock function
const mockFn = vi.fn();
mockFn.mockReturnValue({ data: [] });           // Fixed return
mockFn.mockResolvedValue({ data: [] });          // Promise resolve
mockFn.mockRejectedValue(new Error("fail"));     // Promise reject
mockFn.mockImplementation((id) => ({ id }));    // Custom logic
```

### 3.2 ParkGuideSG Frontend Mock Example

From `frontend/src/__tests__/api.test.js`:

```javascript
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("fetchRecommendations", () => {
  beforeEach(() => {
    // Replace global fetch with a mock
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ results: [] }),
      })
    );
  });

  it("constructs correct URL with all params", async () => {
    const { fetchRecommendations } = await import("../services/api");
    await fetchRecommendations(1.35, 103.81, 5, 3000);

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/recommend?lat=1.35")
    );
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("n=5")
    );
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("radius_m=3000")
    );
  });

  it("throws on HTTP 500 error", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: false, status: 500 })
    );
    const { fetchRecommendations } = await import("../services/api");
    await expect(fetchRecommendations(1.35, 103.81)).rejects.toThrow();
  });
});
```

### 3.3 Component Test Mock Example

From `frontend/src/__tests__/NavButton.test.jsx`:

```javascript
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

describe("NavButton", () => {
  it("generates Google Maps URL on non-iOS device", () => {
    // Mock navigator.userAgent
    Object.defineProperty(navigator, "userAgent", {
      value: "Mozilla/5.0 (Linux; Android 14)",
      configurable: true,
    });

    render(<NavButton lat={1.3521} lng={103.8198} />);

    const link = screen.getByTitle("Navigate");
    expect(link.href).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=1.3521,103.8198"
    );
    expect(link.target).toBe("_blank");
    expect(link.rel).toBe("noopener noreferrer");
  });
});
```

---

## 4. Complete Example: Mock User Login Process

This is a **step-by-step walkthrough** of building a mock object that simulates a complete user login flow — from HTTP request to database query to JWT cookie response.

### 4.1 The Real Flow (What We're Mocking)

```
POST /api/v1/auth/login {"username": "testuser", "password": "mypass"}
  │
  ├─ [1] Query database: SELECT * FROM users WHERE username = 'testuser'
  │     Returns: {id: 1, username: "testuser", password_hash: "$2b$12$..."}
  │
  ├─ [2] Verify password: bcrypt.checkpw("mypass", stored_hash)
  │     Returns: True
  │
  ├─ [3] Create JWT: jwt.encode({user_id: 1, username: "testuser", exp: ...})
  │     Returns: "eyJhbGciOiJIUzI1NiIs..."
  │
  └─ [4] Set cookie: Set-Cookie: token=eyJ...; HttpOnly; SameSite=Lax; Path=/
       Response: {"user_id": 1, "username": "testuser", "status": "ok"}
```

### 4.2 The Mock Setup

```python
# File: backend/tests/examples/test_mock_login_walkthrough.py
"""Complete walkthrough of mocking a user login flow."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


class TestMockLoginWalkthrough:
    """Step-by-step demonstration of mock objects for login."""

    def test_mock_login_success(self, client, mock_db):
        """
        Test: POST /api/v1/auth/login with valid credentials.
        
        MOCKED:
        - Database query (returns a user record with bcrypt hash)
        - Password verification (returns True)
        - JWT creation (returns a valid-looking token)
        """
        conn, cur = mock_db

        # ── STEP 1: Mock the database query ──
        # The auth router does: cur.execute("SELECT ... FROM users WHERE username = %s")
        # Then: cur.fetchone() to get the user row
        cur.fetchone.return_value = {
            "id": 1,
            "username": "testuser",
            # This is a fake bcrypt hash for "password123"
            "password_hash": "$2b$12$LJ3m4ys3GZfnYMz8kVsKaOm5pXVL5Hq1nVsGfJ3R8PQxRyNPMHI36",
        }

        # ── STEP 2: Mock password verification ──
        # bcrypt.checkpw is slow (~200ms). Mock it to return True instantly.
        with patch(
            "app.services.auth.verify_password", return_value=True
        ) as mock_verify:
            # ── STEP 3: Send the request ──
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "testuser", "password": "password123"},
            )

            # ── STEP 4: Assertions ──
            # (A) HTTP status is 200
            assert response.status_code == 200

            # (B) Response body: no token in JSON (it's in cookie only)
            data = response.json()
            assert data["user_id"] == 1
            assert data["username"] == "testuser"
            assert data["status"] == "ok"
            assert "token" not in data  # <-- JWT NOT in body!

            # (C) Cookie is set with correct attributes
            set_cookie = response.headers.get("set-cookie", "")
            assert "token=" in set_cookie
            assert "HttpOnly" in set_cookie   # XSS protection
            assert "SameSite=Lax" in set_cookie
            assert "Path=/" in set_cookie

            # (D) Database was queried exactly once
            cur.execute.assert_called_once()

            # (E) Password verification was called with the right args
            mock_verify.assert_called_once_with(
                "password123", cur.fetchone.return_value["password_hash"]
            )

    def test_mock_login_invalid_password(self, client, mock_db):
        """
        Test: POST /api/v1/auth/login with WRONG password.
        
        MOCKED:
        - Database returns a user (user exists)
        - Password verification returns False (wrong password)
        """
        conn, cur = mock_db
        cur.fetchone.return_value = {
            "id": 1,
            "username": "testuser",
            "password_hash": "$2b$12$...",
        }

        with patch(
            "app.services.auth.verify_password", return_value=False
        ):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "testuser", "password": "WRONG"},
            )

            assert response.status_code == 401
            assert "Invalid" in response.json()["detail"]

    def test_mock_login_db_connection_lost(self, client, mock_db):
        """
        Test: POST /api/v1/auth/login when database is down.
        
        MOCKED:
        - Database query raises an exception (DB connection lost)
        
        This is the POWER of mocks — we can simulate infrastructure
        failures that would be hard to trigger with a real DB.
        """
        conn, cur = mock_db
        cur.execute.side_effect = Exception("Connection refused")

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"},
        )

        # Should get a 500, not crash the server
        assert response.status_code == 500

    def test_mock_login_user_not_found(self, client, mock_db):
        """
        Test: POST /api/v1/auth/login with unknown username.
        
        MOCKED:
        - Database query returns None (user doesn't exist)
        
        Note: Password verification is NEVER called — the route
        returns 401 immediately when fetchone returns None.
        """
        conn, cur = mock_db
        cur.fetchone.return_value = None  # <-- No matching user

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "ghostuser", "password": "anything"},
        )

        assert response.status_code == 401

    def test_mock_login_with_side_effect_sequence(self, client, mock_db):
        """
        Demonstrate side_effect for multi-step operations.
        
        Real scenario: The register endpoint does:
          1. SELECT ... WHERE username = %s    → None (no duplicate)
          2. INSERT INTO users ... RETURNING id → {"id": 2}
        
        We use side_effect with a list to sequence returns.
        """
        conn, cur = mock_db
        # Sequence: 1st call → None, 2nd call → new user id
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

            # Verify both DB calls happened
            assert cur.execute.call_count == 2
```

### 4.3 What Each Mock Replaces

| Real Component | Mocked By | Why |
|---------------|-----------|-----|
| PostgreSQL database | `mock_db` fixture → `MagicMock()` connection + cursor | Tests run in <5ms, no DB needed |
| psycopg2 driver | `sys.modules["psycopg2"] = MagicMock()` | Prevents import-time DB connection |
| bcrypt password hashing | `patch("app.services.auth.verify_password")` | bcrypt is slow (~200ms per hash) |
| JWT creation | Real `create_token()` (not mocked) | Pure function, fast, no side effects |
| LightGBM model | `sys.modules["lightgbm"] = MagicMock()` | Requires native binary, 100MB+ model file |
| HTTP client (frontend) | `global.fetch = vi.fn()` | No real backend needed for frontend tests |

### 4.4 Mock Decision Tree

```
Is the dependency...
│
├── Fast & no side effects? → DON'T mock (e.g., JWT create/decode, _status())
│
├── Slow (>50ms)? → MOCK (e.g., bcrypt, LightGBM load, HTTP requests)
│
├── Requires infrastructure? → MOCK (e.g., PostgreSQL, Redis, external APIs)
│
├── Non-deterministic? → MOCK (e.g., random(), Date.now(), weather API)
│
└── Hard to trigger error states? → MOCK (e.g., DB connection lost, API timeout)
```

---

## 5. Mock Patterns Used in ParkGuideSG

### 5.1 Architecture Overview

```
                          ┌─────────────────────────┐
                          │     conftest.py          │
                          │  (Module-level mocks)    │
                          │                         │
                          │  sys.modules["psycopg2"] │ ←── Heavy DB driver
                          │  sys.modules["lightgbm"] │ ←── ML framework
                          │  sys.modules["pandas"]   │ ←── Data processing
                          │  sys.modules["joblib"]   │ ←── Model serialization
                          │  sys.modules["asyncpg"]  │ ←── Async DB driver
                          └───────────┬─────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
     ┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
     │   mock_db       │    │  auth_headers   │    │  unittest.mock  │
     │   fixture       │    │  fixture        │    │  .patch()       │
     │                 │    │                 │    │                 │
     │  Mock conn pool │    │  Real JWT from  │    │  Targeted per-  │
     │  Mock cursor    │    │  create_token() │    │  test overrides │
     │  Per-test setup │    │  Session-scoped │    │  Context manager│
     └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      │
                            ┌─────────▼─────────┐
                            │   Test Functions   │
                            │                    │
                            │  test_auth.py      │
                            │  test_favourites.py│
                            │  test_carpark.py   │
                            │  test_health.py    │
                            │  test_recommend.py │
                            │  test_auth_service │
                            └────────────────────┘
```

### 5.2 Test File → Mock Dependency Map

| Test File | Mocks Used | Pattern |
|-----------|-----------|---------|
| `test_auth_service.py` | None (pure unit tests) | No mocking needed — functions are pure |
| `test_auth.py` | `mock_db`, `patch(verify_password)`, `auth_headers` | Fixture + context manager |
| `test_favourites.py` | `mock_db`, `auth_headers` | Fixture |
| `test_carpark.py` | `mock_db` | Fixture |
| `test_health.py` | `patch(query_db_stats)`, `patch(is_model_loaded)` | Context manager |
| `test_recommend.py` | None (pure functions + schema validation) | No mocking needed |
| `api.test.js` | `global.fetch = vi.fn()` | Vitest mock function |
| `NavButton.test.jsx` | `Object.defineProperty(navigator, "userAgent")` | jsdom property mock |

### 5.3 Mock Coverage: What's NOT Yet Mocked

| Missing Mock | Impact | Recommendation |
|-------------|--------|---------------|
| Data.gov.sg API in ETL tests | Can't test ETL without network | Create `mock_requests` fixture for `etl_cloud.py` |
| DeepSeek LLM API | Tests depend on API key | Mock `_predict_with_llm()` to return synthetic predictions |
| `navigator.geolocation` in frontend | Can't test GPS flows | Mock `getCurrentPosition` / `watchPosition` in jsdom |
| Weather API in ETL | Can't test weather data ingestion | Mock NEA API with canned JSON responses |

---

## 6. Best Practices

### ✅ DO

1. **Mock at the boundary** — Mock the database driver, not every SQL query
2. **Use `side_effect` for sequences** — Simulate multi-step DB operations
3. **Verify mock calls** — `assert_called_with()` catches logic errors
4. **Reset between tests** — Each test gets fresh mocks via `function`-scoped fixtures
5. **Mock the slowest thing first** — bcrypt, model loading, HTTP calls

### ❌ DON'T

1. **Don't mock what you don't own** — Mock your adapter layer, not the library internals
2. **Don't over-mock** — Pure functions (`_status()`, `_make_trend()`) need no mocks
3. **Don't mock values that don't matter** — If a test doesn't depend on a return value, don't configure it
4. **Don't forget to mock `__enter__`/`__exit__`** — Context managers need both methods for `with` statements
5. **Don't use real credentials in mocks** — `os.environ["JWT_SECRET"] = "test-secret-key"`

---

## 7. References

- [Python `unittest.mock` Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Vitest Mocking Guide](https://vitest.dev/guide/mocking.html)
- [FastAPI Testing with TestClient](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing React with React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- ParkGuideSG [Test Strategy](test-strategy.md)
- ParkGuideSG [`conftest.py`](../backend/tests/conftest.py) — Working mock examples
