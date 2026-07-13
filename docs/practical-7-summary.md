---
layout: default
title: Practical 7 — Iteration 2 TDD Summary
parent: Documentation
---

# Practical 7: Iteration 2 — Test-Driven Development

> **Course**: CP3102 — Software Engineering  
> **Project**: ParkGuideSG  
> **Branch**: `develop`  
> **Commit**: `d0d261c`  
> **Date**: 2026-07-13  

---

## Task 1: Discuss, Document, and Plan Testing

### Deliverable

**[`docs/test-strategy.md`](test-strategy.md)** — a comprehensive test strategy document covering all layers of the ParkGuideSG application.

### What the Document Covers

| Section | Content |
|---------|---------|
| **Test Pyramid** | Unit → Integration → E2E, with current coverage status per layer |
| **Backend Testing** | pytest + FastAPI TestClient + MagicMock; module-level mock injection architecture; fixture documentation (`client`, `mock_db`, `auth_headers`); database mocking patterns with code examples |
| **Frontend Testing** | vitest + React Testing Library + jsdom; component testing patterns; API service testing patterns; configuration setup |
| **ML Model Testing** | Three-tier inference fallback (LightGBM → LLM → Heuristic); current mock approach; recommended future tests |
| **ETL Pipeline Testing** | Data pipeline test recommendations for Iteration 3 |
| **CI Integration** | Ready-to-use GitHub Actions workflow YAML for both backend and frontend test suites |
| **Coverage Targets** | Per-module coverage targets for Iteration 2 and Iteration 3 |
| **Test Data Management** | Principles: no production data, deterministic mocks, version-controlled fixtures |

---

## Task 2: Five User Stories with Test Cases (p242 Format)

### Deliverable

Five user story documents in **[`docs/user-stories/iteration-2/`](user-stories/iteration-2/)** , each containing 3–4 test cases in the **Given/When/Then narrative format** (textbook page 242, BeatBox Pro style).

### Selected Stories

| # | Story | Persona | Iteration | Test Cases |
|---|-------|---------|-----------|------------|
| US#1 | [Search Nearby Carparks (GPS)](user-stories/iteration-2/01-search-nearby-testcases) | Tan Wei Ming (Daily Commuter) | Iteration 1 | 4 |
| US#4 | [Search by Address or Area](user-stories/iteration-2/04-search-address-testcases) | Siti Nurul (Weekend Explorer) | Iteration 1 | 3 |
| US#6 | [Manage Favourite Carparks](user-stories/iteration-2/06-favourites) | Both Personas | Iteration 2 | 4 |
| US#8 | [One-Tap Navigate to Carpark](user-stories/iteration-2/08-navigation) | Tan Wei Ming | Iteration 2 | 3 |
| US#10 | [Secure Session with httpOnly Cookie](user-stories/iteration-2/10-secure-session) | Both Personas | Iteration 2 | 4 |

**Total: 18 test cases across 5 stories** (requirement: ≥ 15)

### Test Case Format (p242 Style)

Each test case follows the textbook format:

```
N. Test for… [one-line description of what is being tested]
   [Narrative paragraph: detailed steps, what to set up,
    what action to take, what to observe, what to verify]
   [Classification: black-box / grey-box / white-box test]
[One-line summary of the test intent]
```

### Example — US#10 Test Case 1

> **1. Test for…** *a successful login response setting the httpOnly authentication cookie.*
>
> Start the ParkGuideSG backend server. Configure the database mock to return a user record with a valid bcrypt password hash when queried by username. Send a POST request to `/api/v1/auth/login` with `{"username": "testuser", "password": "correctpassword"}`. Check that the response has HTTP status 200. Verify the response body contains `{"user_id": 1, "username": "testuser", "status": "ok"}` — note that the `token` is NOT in the JSON body (it is only in the cookie). Check the response headers for `Set-Cookie`. Verify the cookie name is `"token"` and the value is a valid JWT string. Confirm the cookie attributes include `HttpOnly`, `SameSite=Lax`, and `Path=/`.
>
> *This is a grey-box test. You need to know the cookie attribute logic and that the login endpoint uses `_set_token_cookie()` to attach the cookie to the JSONResponse.*
>
> **User logs in → JWT goes into httpOnly cookie, not exposed to JavaScript.**

### Persona Mapping

| Persona | Stories | Motivation |
|---------|---------|------------|
| **Tan Wei Ming** (Daily Commuter, 34, Financial Analyst) | US#1, US#8 | Needs fastest route to nearest carpark with real-time GPS search and one-tap navigation |
| **Siti Nurul** (Weekend Explorer, 29, Freelance Designer) | US#4, US#6 | Plans ahead with address search, saves frequent destinations as favourites |
| **Both** | US#10 | Security-conscious: wants XSS-resistant authentication without repeated login |

---

## Task 3: Implement 15+ Automated Tests

### Deliverable

**25 automated tests implemented and passing** — 16 backend (pytest) + 9 frontend (vitest).

### Backend Tests — 44 Total (16 New)

| File | New Tests | What They Verify |
|------|-----------|-----------------|
| `backend/tests/test_favourites.py` | **9** | Favourites list (auth required, empty state, saved items); Add favourite (auth required, success, nonexistent carpark → 404); Remove favourite (auth required, success, idempotent delete) |
| `backend/tests/test_carpark.py` | **5** | Carpark search (missing query → 422, matching results, empty results); Carpark detail (404 for unknown ID, full detail with 24h history) |
| `backend/tests/test_auth.py` | **2** | `TestCookieAuth`: login sets HttpOnly cookie; logout clears cookie |

**Test infrastructure improvements:**
- Fixed `conftest.py`: added DBAPI 2.0 attributes (`paramstyle`, `apilevel`, `threadsafety`), `asyncpg` mock, connection-pool-level mocking for `get_sync_conn()`
- Updated `test_register_success` for Iteration 2 behaviour (JWT in `Set-Cookie` header, not JSON body)
- Removed 5 duplicate root-level test files (pytest only scans `tests/`)

### Frontend Tests — 9 Total (All New)

| File | Tests | What They Verify |
|------|-------|-----------------|
| `frontend/src/__tests__/NavButton.test.jsx` | **3** | Google Maps URL generation on non-iOS; custom label rendering; compact mode CSS class and 16×16 SVG icon |
| `frontend/src/__tests__/api.test.js` | **6** | `fetchRecommendations` URL construction with all params; default n=5/radius=1000; `searchCarparks` query encoding; HTTP 500 error throws; HTTP 404 error throws; `fetchFavourites` correct endpoint |

**Frontend test infrastructure:**
- Added `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom` to `package.json`
- Created `vitest.config.js` with jsdom environment and React plugin
- Created `src/tests/setup.js` for testing-library matchers

### Verification — All Tests Pass

**Backend (pytest):**
```
======================== 44 passed, 1 warning in 7.15s ========================
```

**Frontend (vitest):**
```
 Test Files  2 passed (2)
      Tests  9 passed (9)
```

### Running the Tests

```bash
# Backend
cd backend
pip install -r requirements-test.txt
python -m pytest tests/ -v

# Frontend
cd frontend
npm install
npx vitest run
```

---

## Summary of All Deliverables

| Task | Deliverable | Location | Count |
|------|------------|----------|-------|
| 1 | Test Strategy Document | `docs/test-strategy.md` | 1 document |
| 2 | User Stories with Test Cases | `docs/user-stories/iteration-2/` | 5 stories, 18 test cases |
| 3 | Automated Tests (Backend) | `backend/tests/test_*.py` | 16 new tests |
| 3 | Automated Tests (Frontend) | `frontend/src/__tests__/` | 9 new tests |
| **Total** | | | **25 tests, 5 stories, 1 strategy doc** |

### Files Created/Modified

```
CREATED:
  docs/test-strategy.md
  docs/user-stories/iteration-2/01-search-nearby-testcases.md
  docs/user-stories/iteration-2/04-search-address-testcases.md
  docs/user-stories/iteration-2/06-favourites.md
  docs/user-stories/iteration-2/08-navigation.md
  docs/user-stories/iteration-2/10-secure-session.md
  backend/tests/test_favourites.py
  backend/tests/test_carpark.py
  frontend/vitest.config.js
  frontend/src/tests/setup.js
  frontend/src/__tests__/NavButton.test.jsx
  frontend/src/__tests__/api.test.js

MODIFIED:
  backend/tests/conftest.py         (DBAPI attrs, asyncpg mock, pool mocking)
  backend/tests/test_auth.py        (TestCookieAuth + fixed register test)
  frontend/package.json             (vitest + testing-library deps)

REMOVED:
  backend/conftest.py               (duplicate — tests/conftest.py is authoritative)
  backend/test_auth.py              (duplicate)
  backend/test_auth_service.py      (duplicate)
  backend/test_health.py            (duplicate)
  backend/test_recommend.py         (duplicate)
```
