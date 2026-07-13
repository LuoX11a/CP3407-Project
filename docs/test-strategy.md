---
layout: default
title: Test Strategy
parent: Documentation
---

# ParkGuideSG — Test Strategy

> **Version**: 0.1.0  
> **Last Updated**: 2026-07-13  
> **Phase**: Iteration 2 — Test-Driven Development  

---

## 1. Overview

ParkGuideSG is a full-stack real-time parking recommendation system for Singapore HDB carparks. The system combines a FastAPI backend, React frontend, PostgreSQL database, and ML prediction pipeline. This document defines the testing philosophy, tools, and practices for the project.

### 1.1 Test Pyramid

```
        ╱  E2E  ╲          ← Cypress / Playwright (future)
       ╱──────────╲
      ╱ Integration ╲      ← FastAPI TestClient + vitest
     ╱────────────────╲
    ╱   Unit Tests     ╲    ← pytest + vitest (pure functions, components)
   ╱──────────────────────╲
```

| Layer | Scope | Tool | Current Coverage |
|-------|-------|------|------------------|
| **Unit** | Pure functions (hashing, JWT, status logic, sort logic, URL generation) | pytest, vitest | ✅ Auth service, recommend logic; ❌ Frontend utilities |
| **Integration** | API endpoints (request → response cycle), component rendering | FastAPI TestClient, React Testing Library | ✅ Auth endpoints, health, recommend; ❌ Favourites, carpark |
| **E2E** | Full user flows across frontend + backend | Cypress / Playwright | ❌ Not yet implemented (Iteration 3 plan) |

### 1.2 Testing Philosophy

1. **No real database in tests** — All database calls are mocked at the connection pool level. Tests run fast, are deterministic, and require no infrastructure.
2. **One test, one behaviour** — Each test verifies exactly one aspect of the system: a happy path, an error case, or a boundary condition.
3. **Class-based organisation** — Backend tests use Python test classes (`TestRegisterEndpoint`, `TestPasswordHashing`) grouped by feature area.
4. **Given/When/Then thinking** — Test cases are designed around preconditions (Given), actions (When), and assertions (Then), matching the textbook format (p242).

---

## 2. Backend Testing

### 2.1 Technology Stack

| Tool | Version | Purpose |
|------|---------|---------|
| pytest | ≥ 8.0 | Test runner |
| FastAPI TestClient | (bundled) | HTTP client for endpoint testing |
| unittest.mock (MagicMock, patch) | (stdlib) | Mocking database, ML models, external services |
| pytest-asyncio | ≥ 0.24 | Async test support (future use) |
| httpx | ≥ 0.27 | Underlying HTTP transport for TestClient |

### 2.2 Mock Architecture

The test suite uses **module-level mock injection** to avoid loading heavy dependencies and prevent real database connections. This is configured in `backend/tests/conftest.py`.

```
sys.modules["psycopg2"]      → MagicMock  (prevents DB connection)
sys.modules["lightgbm"]       → MagicMock  (prevents ML model loading)
sys.modules["joblib"]         → MagicMock  (prevents model deserialization)
sys.modules["pandas"]         → MagicMock  (prevents DataFrame operations)
```

This means tests depend only on `pytest`, `httpx`, `python-jose`, and `passlib[bcrypt]` — not on `lightgbm`, `joblib`, or `pandas`.

### 2.3 Key Fixtures

| Fixture | Scope | Returns | Usage |
|---------|-------|---------|-------|
| `app` | session | FastAPI instance | Created once per test session |
| `client` | function | `TestClient(app)` | Makes HTTP requests to endpoints |
| `auth_headers` | function | `{"Authorization": "Bearer <jwt>"}` | Authenticated requests |
| `mock_db` | function | `(conn, cur)` MagicMock tuple | Controls database behaviour per test |

### 2.4 Database Mocking Pattern

```python
def test_example(self, client, mock_db):
    conn, cur = mock_db
    # Arrange: configure mock cursor behaviour
    cur.fetchone.return_value = {"id": 1, "username": "testuser"}
    cur.fetchall.return_value = [{"carpark_id": "ACM"}, {"carpark_id": "A11"}]

    # Act: call the endpoint
    response = client.get("/api/v1/example")

    # Assert: verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
```

For multi-step database operations, use `side_effect`:

```python
cur.fetchone.side_effect = [
    None,        # First call: check existing user → not found
    {"id": 1},   # Second call: INSERT RETURNING id → user created
]
```

### 2.5 Endpoint-Level Mocking

For endpoints that call service functions directly, use `unittest.mock.patch`:

```python
with patch("app.routers.health.query_db_stats", return_value=mock_stats), \
     patch("app.routers.health.is_model_loaded", return_value=True):
    response = client.get("/api/v1/health")
```

### 2.6 Running Backend Tests

```bash
# Install test dependencies
cd backend
pip install -r requirements-test.txt

# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_auth.py -v

# Run a specific test class
python -m pytest tests/test_auth.py::TestLoginEndpoint -v
```

### 2.7 Test File Organisation

```
backend/tests/
  conftest.py              ← Shared fixtures and module-level mocks
  test_auth_service.py     ← Unit tests: password hashing, JWT create/decode
  test_auth.py             ← Integration tests: register, login, logout endpoints
  test_health.py           ← Integration tests: health endpoint (ok / degraded)
  test_recommend.py        ← Unit tests: _status(), _make_trend(), schema validation
  test_favourites.py       ← Integration tests: favourites CRUD endpoints
  test_carpark.py          ← Integration tests: carpark search and detail endpoints
```

---

## 3. Frontend Testing

### 3.1 Technology Stack

| Tool | Version | Purpose |
|------|---------|---------|
| vitest | ≥ 2.0 | Test runner (Vite-native, fast) |
| @testing-library/react | ≥ 16.0 | Component rendering and querying |
| @testing-library/jest-dom | ≥ 6.0 | DOM assertion matchers |
| jsdom | ≥ 24.0 | Browser environment simulation |

### 3.2 Configuration

`vitest.config.js`:

```javascript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/tests/setup.js"],
  },
});
```

### 3.3 Component Testing Pattern

```javascript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ComponentName from "../components/ComponentName";

describe("ComponentName", () => {
  it("renders expected content", () => {
    render(<ComponentName prop1="value" />);
    expect(screen.getByText("Expected Text")).toBeInTheDocument();
  });
});
```

### 3.4 Service/API Testing Pattern

```javascript
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("API Service", () => {
  beforeEach(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ data: [] }) })
    );
  });

  it("constructs correct URL", async () => {
    await fetchRecommendations(1.35, 103.81, 5, 3000);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/recommend?lat=1.35")
    );
  });
});
```

### 3.5 Running Frontend Tests

```bash
cd frontend

# Install dependencies (including test deps)
npm install

# Run all tests
npx vitest run

# Run with watch mode (during development)
npx vitest
```

### 3.6 Frontend Test File Organisation

```
frontend/src/
  __tests__/                    ← Test files (vitest default glob)
    NavButton.test.jsx          ← Component tests
    api.test.js                 ← API service tests
  tests/
    setup.js                    ← Test environment setup
```

---

## 4. ML Model Testing

### 4.1 Current Approach

The ML inference service (`backend/app/services/inference.py`) has a three-tier fallback architecture:

1. **ML Model (LightGBM)** — primary predictor, loaded from `ml/model/carpark_predictor.joblib`
2. **LLM (DeepSeek API)** — backup when model is unavailable but API key is set
3. **Heuristic fallback** — rule-based prediction using time-of-day, weekend/weekday, carpark capacity

### 4.2 Testing Strategy

| Tier | Test Approach | Status |
|------|--------------|--------|
| `load_model()` | Mocked at module level in conftest.py | ✅ |
| `is_model_loaded()` | Mocked to return `True` | ✅ |
| `predict()` | Tested indirectly via recommend endpoint mocks | ⚠️ Partial |
| `_heuristic_predict()` | Pure function — testable with known inputs | ❌ Not yet |
| `_predict_with_llm()` | Requires API key — tested manually | ❌ Not yet |

### 4.3 Recommended ML Tests (Iteration 3)

- Test `_heuristic_predict()` returns values in `[0.0, 1.0]` for various time/capacity inputs
- Test model fallback chain: model unavailable → LLM, LLM unavailable → heuristic
- Test `predict_batch()` with known feature vectors → expected output ranges

---

## 5. ETL Pipeline Testing

### 5.1 Current State

The ETL pipeline (`etl_cloud.py`) runs in GitHub Actions every 30 minutes. It fetches from Data.gov.sg and NEA APIs, transforms data, and loads into PostgreSQL.

### 5.2 Testing Strategy

| Test Type | What to Test | Status |
|-----------|-------------|--------|
| Unit: `_haversine()` | Distance calculation with known coordinates | ❌ Not yet |
| Unit: `_fetch_json()` | HTTP mock, retry logic, timeout behaviour | ❌ Not yet |
| Integration: ETL cycle | Mock APIs, verify records inserted correctly | ❌ Not yet |
| Validation: data quality | Low carpark count warning, missing fields | ⚠️ Inline checks only |

### 5.3 Recommended ETL Tests (Iteration 3)

- Extract fetch/transform/load logic into testable functions
- Add `pytest` tests for the ETL module with mocked `requests.get`
- Add data validation tests (schema compliance, value ranges)

---

## 6. Continuous Integration

### 6.1 Recommended GitHub Actions Workflow

```yaml
name: Test Suite
on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r backend/requirements.txt -r backend/requirements-test.txt
      - run: cd backend && python -m pytest tests/ -v

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: cd frontend && npm ci
      - run: cd frontend && npx vitest run
```

### 6.2 Pre-commit Hooks (Recommended)

- `black` / `ruff` — Python formatting and linting
- `eslint` + `prettier` — JavaScript formatting and linting
- `pytest --lf` — Run last-failed tests before commit

---

## 7. Test Coverage Targets

| Area | Current | Iteration 2 Target | Iteration 3 Target |
|------|---------|-------------------|-------------------|
| Backend auth service | 100% (9/9 functions) | 100% | 100% |
| Backend endpoints | 50% (4/8 endpoints) | 75% (6/8) | 100% |
| Backend geospatial service | 0% | 0% | 60% |
| Backend inference service | 30% | 30% | 70% |
| Frontend components | 0% | 25% (NavButton) | 60% |
| Frontend services | 0% | 50% (api.js) | 100% |
| ETL pipeline | 0% | 0% | 50% |

---

## 8. Test Data Management

### 8.1 Principles

- **No production data in tests** — All test data is synthetic or mocked.
- **Deterministic tests** — Mock returns are explicit; no reliance on timing or random values.
- **Version-controlled resources** — Test fixtures and sample inputs live in the repository.

### 8.2 Sample Test Data

For tests requiring realistic data shapes, use inline dictionaries that match the Pydantic schema:

```python
SAMPLE_CARPARK = {
    "carpark_id": "ACM",
    "address": "123 Test Street",
    "car_lots": 400,
    "motorcycle_lots": 50,
    "lat": 1.3521,
    "lng": 103.8198,
    "available_lots": 150,
    "vacancy_rate": 0.375,
    "weather_condition": "cloudy",
}
```

---

## 9. Appendix: Test Naming Convention

| Convention | Example |
|-----------|---------|
| **File**: `test_<module>.py` | `test_favourites.py` |
| **Class**: `Test<Feature>` | `TestFavouritesList` |
| **Method**: `test_<scenario>_<expected>` | `test_add_favourite_success` |
| **Frontend file**: `<Component>.test.jsx` | `NavButton.test.jsx` |
| **Frontend describe**: Component name | `describe("NavButton", ...)` |
| **Frontend it**: `it("does X when Y", ...)` | `it("renders Google Maps URL on non-iOS", ...)` |
