---
layout: default
title: "US #10 — Secure Session with httpOnly Cookie"
parent: Iteration 2
---

# User Story #10: Secure Session with httpOnly Cookie

| Field | Detail |
|-------|--------|
| Priority | 10 |
| Estimated Days | 0.5 |
| Status | **Done** (Iteration 2 — #38) |
| Persona | Both Tan Wei Ming & Siti Nurul |

## Story

> As a **security-conscious user**, I want my **login session stored in a secure httpOnly cookie** so that **my account cannot be hijacked by XSS attacks that steal tokens from localStorage**.

## Acceptance Criteria

- [x] Login and register responses set an httpOnly cookie named "token"
- [x] Cookie has `SameSite=Lax` (dev) or `SameSite=Strict` (production)
- [x] Logout clears the auth cookie
- [x] Protected endpoints read the token from the cookie (primary) with Bearer header fallback
- [x] Expired or invalid tokens return 401
- [x] Frontend no longer stores JWT in localStorage

## Implementation

**Backend**:
- `backend/app/routers/auth.py` — `_set_token_cookie()` helper, register, login, logout
- `backend/app/services/auth.py` — `get_current_user()` reads from `request.cookies.get("token")` first, falls back to Bearer header
- Cookie attributes: `httponly=True`, `secure=<IS_PRODUCTION>`, `samesite="strict"/"lax"`, `max_age=604800` (7 days)

**Frontend**:
- `frontend/src/services/api.js` — No manual token management; cookies sent automatically by browser
- `frontend/src/App.jsx` — User state restored from stored user object (not token)

---

## Test Cases

### 1. Test for…

*…a successful login response setting the httpOnly authentication cookie.*

Start the ParkGuideSG backend server. Configure the database mock to return a user record with a valid bcrypt password hash when queried by username. Send a POST request to `/api/v1/auth/login` with `{"username": "testuser", "password": "correctpassword"}`. Check that the response has HTTP status 200. Verify the response body contains `{"user_id": 1, "username": "testuser", "status": "ok"}` — note that the `token` is NOT in the JSON body (it is only in the cookie). Check the response headers for `Set-Cookie`. Verify the cookie name is `"token"` and the value is a valid JWT string (three dot-separated base64 segments). Confirm the cookie attributes include `HttpOnly`, `SameSite=Lax` (development), and `Path=/`. Also verify that `Secure` is NOT set in development mode but IS set when `RENDER=true` environment variable is present.

*This is a grey-box test. You need to know the cookie attribute logic: `secure=IS_PRODUCTION` where `IS_PRODUCTION` is true when `RENDER=true` or `ENVIRONMENT=production`. The login endpoint uses `_set_token_cookie()` to attach the cookie to the JSONResponse.*

**User logs in → JWT goes into httpOnly cookie, not exposed to JavaScript.**

---

### 2. Test for…

*…a logout request clearing the authentication cookie.*

Start the ParkGuideSG backend server. No database mock is needed — the logout endpoint does not query the database. Send a POST request to `/api/v1/auth/logout`. Check that the response has HTTP status 200. Verify the response body is `{"status": "ok"}`. Check the `Set-Cookie` response header. Verify it targets the `"token"` cookie and sets it to an empty value or a value with `max-age=0` (effectively deleting it). Confirm the cookie path matches the one used at login (`Path=/`).

*This is a black-box test. The logout endpoint simply clears the cookie; no database interaction is needed. The frontend calls this endpoint and then clears the local user state.*

**User clicks Logout → cookie is cleared, user state reset, no session remains.**

---

### 3. Test for…

*…a protected endpoint authenticating successfully from the httpOnly cookie without a Bearer header.*

Start the ParkGuideSG backend server. Generate a valid JWT token using `create_token(user_id=1, username="testuser")`. Send a GET request to `/api/v1/favourites` with the cookie `token=<jwt_value>` but WITHOUT any `Authorization` header. Configure the database mock to return an empty favourites list. Check that the response has HTTP status 200. Verify the response body is `{"favourites": []}`. This confirms the server read the JWT from the cookie and authenticated the user — demonstrating that the httpOnly cookie path works end-to-end. Repeat without any cookie or Bearer header to confirm 401 is returned, proving the cookie is the active authentication mechanism.

*This is a grey-box test. You need to know that `get_current_user()` checks `request.cookies.get("token")` first, then falls back to `credentials.credentials` from the Bearer header. This test proves the cookie-primary, header-fallback priority chain.*

**Page refresh → browser sends cookie automatically → user stays logged in.**

---

### 4. Test for…

*…rejecting a request with an invalid or tampered JWT in the cookie.*

Start the ParkGuideSG backend server. Construct a deliberately invalid JWT string (e.g., `"not.a.real.jwt.token"` or a valid JWT with a wrong signature). Send a GET request to `/api/v1/favourites` with the cookie `token=not.a.real.jwt.token`. Check that the response has HTTP status 401. Verify the response detail message is "Invalid or expired token". Also test with an expired token: use `python-jose` to create a token with `exp` set to 1 hour in the past. Send the request with this expired token in the cookie. Confirm HTTP 401 is returned. Verify no database query was executed — the JWT validation happens before any route handler runs.

*This is a black-box test. You only need to know that protected endpoints return 401 for invalid tokens. The JWT validation in `decode_token()` runs inside `get_current_user()`, which is a FastAPI dependency that executes before the route handler.*

**Tampered token → rejected. Expired token → rejected. Both return 401 before touching the database.**
