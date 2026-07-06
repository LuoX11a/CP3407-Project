---
layout: default
title: "US #9 — Register Account"
parent: Iteration 2
---

# User Story #9: Register Account

| Field | Detail |
|-------|--------|
| Priority | 40 |
| Estimated Days | 1 |
| Status | **Done** |
| Persona | Both Tan Wei Ming & Siti Nurul |

## Story

> As a **new user**, I want to **create an account** so that I can **save my favourite carparks and access personalized features**.

## Acceptance Criteria

- [x] "Login" button in header opens auth modal
- [x] Modal has two modes: Login and Register, switchable via link
- [x] Register form: Username, Email, Password (min 6 chars)
- [x] Client-side validation: required fields, email format, password min length
- [x] `POST /api/v1/auth/register` creates user account
- [x] Password hashed with bcrypt before storage
- [x] Returns JWT token + user_id + username on success
- [x] 409 Conflict if username or email already exists
- [x] On success: modal closes, user sees their username in header, favourites load
- [x] Token + user info persisted in localStorage for session survival

## Implementation

### Backend

**Endpoint**: `POST /api/v1/auth/register`

**File**: `backend/app/routers/auth.py`

```python
@router.post("/auth/register", response_model=AuthResponse)
def register(body: RegisterRequest):
    # 1. Check uniqueness — username OR email collision → 409
    cur.execute(
        "SELECT id FROM users WHERE username = %s OR email = %s",
        (body.username, body.email)
    )
    if cur.fetchone():
        raise HTTPException(status_code=409, detail="Username or email already exists")

    # 2. Hash password with bcrypt
    hashed = hash_password(body.password)

    # 3. Insert user
    cur.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
        (body.username, body.email, hashed),
    )
    user_id = cur.fetchone()["id"]

    # 4. Issue JWT
    token = create_token(user_id, body.username)
    return AuthResponse(user_id=user_id, username=body.username, token=token)
```

**File**: `backend/app/services/auth.py`
- `hash_password(pw)` — bcrypt hash with salt
- `create_token(user_id, username)` — JWT with user claims + expiry

**Schema** (`backend/app/models/schemas.py`):
```python
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str  # min_length=6

class AuthResponse(BaseModel):
    user_id: int
    username: str
    token: str
```

### Frontend

**File**: `frontend/src/components/AuthModal.jsx`

```jsx
// Register flow
async function handleSubmit(e) {
  const data = mode === "login"
    ? await login(username, password)
    : await register(username, email, password);

  localStorage.setItem("token", data.token);
  localStorage.setItem("user", JSON.stringify({ id: data.user_id, username: data.username }));
  onAuth(data);  // Updates App authUser state
  onClose();     // Closes modal
}
```

### Form States

| State | UI |
|-------|-----|
| Default | Empty form with Register/Login toggle |
| Validating | Browser-native validation (required, email, minLength) |
| Submitting | Button disabled + "Please wait..." |
| 409 Conflict | "Username or email already exists" |
| Network error | Error message from API |
| Success | Modal closes, username appears in header |

## Demo Flow

1. New user clicks "Login" in header
2. Clicks "Don't have an account? Register"
3. Fills in username, email, password → clicks Register
4. Backend creates account, returns JWT token
5. Modal closes, header shows "Welcome, [username]"
6. Favourites section appears (empty)
7. User can now star carparks as favourites
8. Refreshing the page → still logged in (localStorage token)
