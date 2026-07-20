---
layout: default
title: "US #10 — Register Account"
parent: Iteration 2
---

# User Story #10: Register Account

| Field | Detail |
|-------|--------|
| Priority | 40 |
| Estimated Days | 1 |
| Status | **Done** |
| Persona | Both Tan Wei Ming & Siti Nurul |

## Story

> As a **new user**, I want to **create an account with a username and password** so that I can **save my favourite carparks and access them across sessions**.

## Acceptance Criteria

- [x] Registration endpoint accepts username (3-50 chars) and password (min 6 chars)
- [x] Password hashed with bcrypt before storage
- [x] Duplicate usernames rejected with 409 Conflict
- [x] Successful registration returns user_id, username, and sets httpOnly JWT cookie
- [x] Input validation rejects short usernames and weak passwords
- [x] Auth modal in frontend with tab to switch between Login/Register

## Implementation

### Backend

**Endpoint**: `POST /api/v1/auth/register`

**File**: `backend/app/routers/auth.py:31-53`

```python
@router.post("/auth/register")
def register(body: RegisterRequest):
    # 1. Validate username length (3-50) and password length (≥6)
    # 2. Hash password with bcrypt via hash_password()
    # 3. Check for duplicate username → 409 if exists
    # 4. INSERT user into database
    # 5. Create JWT token via create_token()
    # 6. Set httpOnly cookie via _set_token_cookie()
    # 7. Return {user_id, username, status: "ok"}
```

**Service**: `backend/app/services/auth.py`
- `hash_password(password: str) → str` — bcrypt hashing
- `create_token(user_id, username) → str` — JWT creation (HS256, 7-day expiry)

### Frontend

**Component**: `frontend/src/components/AuthModal.jsx`

- Modal with Login/Register tabs
- Username + password fields
- Client-side validation before submit
- On success: stores user info in state + localStorage, closes modal
- On error: displays error message

### Security

- JWT stored in **httpOnly cookie** (not localStorage) — immune to XSS
- Cookie attributes: `HttpOnly`, `SameSite=Lax`, `Path=/`
- `Secure` flag enabled in production (`RENDER=true`)

## Test Cases

See [US #10 Secure Session](10-secure-session) for detailed test cases covering:
1. Login sets httpOnly cookie
2. Logout clears cookie
3. Protected endpoint authenticates from cookie
4. Invalid/expired token returns 401

## Demo Flow

1. New user clicks "Login" → switches to "Register" tab
2. Enters username "siti_nurul" + password "mypassword123"
3. Clicks "Register" → spinner while API call happens
4. Success → modal closes, username appears in header
5. Favourites panel appears (empty), ready to save carparks
6. JWT cookie set in browser → persists across page refreshes

## Related

- [US #11 — Login Account](11-login-account)
- [US #9 — Save Favourite Carparks](09-save-favourites)
- [US #10 — Secure Session (test cases)](10-secure-session)
