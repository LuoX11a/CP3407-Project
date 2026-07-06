---
layout: default
title: "US #10 — Login Account"
parent: Iteration 2
---

# User Story #10: Login Account

| Field | Detail |
|-------|--------|
| Priority | 40 |
| Estimated Days | 1 |
| Status | **Done** |
| Persona | Both Tan Wei Ming & Siti Nurul |

## Story

> As a **returning user**, I want to **log into my account** so that I can **access my saved favourites and personalized parking recommendations**.

## Acceptance Criteria

- [x] "Login" button in app header opens auth modal
- [x] Login form: Username + Password
- [x] `POST /api/v1/auth/login` authenticates user
- [x] Password verified against bcrypt hash
- [x] Returns JWT token + user_id + username on success
- [x] 401 Unauthorized if credentials invalid (generic message, no field disclosure)
- [x] On success: modal closes, user sees their username in header, favourites load
- [x] Token attached to all subsequent API requests via `Authorization: Bearer` header
- [x] Logout button clears token + user from localStorage, resets favourites

## Implementation

### Backend

**Endpoint**: `POST /api/v1/auth/login`

**File**: `backend/app/routers/auth.py`

```python
@router.post("/auth/login", response_model=AuthResponse)
def login(body: LoginRequest):
    # 1. Look up user by username
    cur.execute(
        "SELECT id, username, password_hash FROM users WHERE username = %s",
        (body.username,),
    )
    user = cur.fetchone()

    # 2. Verify password (constant-time bcrypt check)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # 3. Issue JWT
    token = create_token(user["id"], user["username"])
    return AuthResponse(user_id=user["id"], username=user["username"], token=token)
```

**File**: `backend/app/services/auth.py`
- `verify_password(plain, hashed)` — bcrypt verification
- `get_current_user(authorization: str)` — FastAPI dependency that decodes JWT from `Authorization: Bearer <token>` header, returns `{"user_id", "username"}` or raises 401

### Frontend

**File**: `frontend/src/services/api.js`

All API calls automatically attach the JWT token:
```javascript
async function request(path, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}
```

**File**: `frontend/src/components/AuthModal.jsx`

Login form (same modal component, mode toggle):
```jsx
<form onSubmit={handleSubmit}>
  <label>Username</label>
  <input value={username} onChange={...} required minLength={2} autoFocus />

  <label>Password</label>
  <input type="password" value={password} onChange={...} required minLength={6} />

  {error && <div className="form-error">{error}</div>}

  <button type="submit" disabled={submitting}>
    {submitting ? "Please wait..." : "Login"}
  </button>
</form>
```

### Header States

| State | UI |
|-------|-----|
| Not logged in | "Login" button |
| Logged in | Username display + "Logout" button |
| Logging in | Button disabled + "Please wait..." |
| Invalid credentials | "Invalid username or password" in modal |
| Logging out | Clears localStorage, resets state, favourites disappear |

### Logout Flow

```javascript
const handleLogout = useCallback(() => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  setAuthUser(null);
  setFavourites([]);
}, []);
```

## Demo Flow

1. Returning user clicks "Login" in header
2. Enters username + password → clicks Login
3. Backend verifies credentials, returns JWT
4. Modal closes, header shows username
5. Favourites load automatically from backend
6. All subsequent API calls include JWT in Authorization header
7. User clicks "Logout" → token cleared, favourites hidden, back to logged-out state
8. Refreshing page → session persists (localStorage)
