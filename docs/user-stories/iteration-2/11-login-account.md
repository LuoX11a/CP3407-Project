---
layout: default
title: "US #11 — Login Account"
parent: Iteration 2
---

# User Story #11: Login Account

| Field | Detail |
|-------|--------|
| Priority | 40 |
| Estimated Days | 1 |
| Status | **Done** |
| Persona | Both Tan Wei Ming & Siti Nurul |

## Story

> As a **returning user**, I want to **log in with my username and password** so that I can **access my saved favourites and personalized settings**.

## Acceptance Criteria

- [x] Login endpoint accepts username and password
- [x] Password verified against stored bcrypt hash
- [x] Invalid credentials return 401 Unauthorized
- [x] Successful login returns user_id, username, and sets httpOnly JWT cookie
- [x] JWT valid for 7 days
- [x] Auth modal shows Login tab by default
- [x] Logout clears the auth cookie and resets user state

## Implementation

### Backend

**Endpoint**: `POST /api/v1/auth/login`

**File**: `backend/app/routers/auth.py:55-73`

```python
@router.post("/auth/login")
def login(body: LoginRequest):
    # 1. Query user by username
    # 2. Verify password with bcrypt via verify_password()
    # 3. If invalid → 401 "Invalid username or password"
    # 4. Create JWT token via create_token()
    # 5. Set httpOnly cookie via _set_token_cookie()
    # 6. Return {user_id, username, status: "ok"}
```

**Endpoint**: `POST /api/v1/auth/logout`

**File**: `backend/app/routers/auth.py:75-83`

```python
@router.post("/auth/logout")
def logout():
    # Clears the "token" cookie by setting max-age=0
    # Returns {status: "ok"}
```

**Service**: `backend/app/services/auth.py`
- `verify_password(password, hashed) → bool` — bcrypt comparison
- `decode_token(token) → dict | None` — JWT validation and decoding
- `get_current_user(request) → dict` — FastAPI dependency, reads from cookie or Bearer header

### Frontend

**Component**: `frontend/src/components/AuthModal.jsx`

- Login tab (default): username + password → submit
- Error display for invalid credentials
- On success: `handleAuth(data)` stores user in state + localStorage

**File**: `frontend/src/App.jsx`

- `handleLogout()` — calls logout API, clears localStorage, resets user state
- User state restored from localStorage on page load

## Demo Flow

1. Returning user clicks "Login" in header
2. Auth modal opens with Login tab selected
3. Enters "tan_weiming" + password → clicks "Login"
4. Valid credentials → modal closes, username appears in header
5. Favourites panel populates with saved carparks
6. User clicks "Logout" → cookie cleared, favourites hidden

## Related

- [US #10 — Register Account](10-register-account)
- [US #10 — Secure Session (test cases)](10-secure-session)
