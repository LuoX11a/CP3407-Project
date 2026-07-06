---
layout: default
title: "US #8-10 — User Account & Favourites"
parent: Iteration 2
---

# User Story #8-10: User Account & Favourites

| Field | Detail |
|-------|--------|
| Priority | 40 |
| Estimated Days | 3 |
| Status | **Done** |
| Persona | Siti Nurul (Weekend Explorer) |

## Story

> As a **regular driver**, I want to **register an account, log in, and save my favourite carparks** so that I can **quickly check availability at my preferred carparks without searching every time**.

## Acceptance Criteria

- [x] Register: username + email + password → JWT token returned
- [x] Login: username + password → JWT token returned
- [x] Password hashed with bcrypt, verified constant-time
- [x] JWT attached to all protected API calls via `Authorization: Bearer`
- [x] Logged-in user sees username in header + logout button
- [x] Logged-in users can star/unstar carparks as favourites
- [x] Favourites appear in dedicated sidebar section with live availability
- [x] Clicking a favourite re-centers map to that location
- [x] Non-logged-in user clicking star → auth modal opens
- [x] Token + user info persisted in localStorage (survives refresh)
- [x] Logout clears token + user + favourites
- [x] 409 on duplicate register, 401 on invalid login

## Implementation

### Backend

| Endpoint | Method | Auth | File |
|----------|--------|------|------|
| `/api/v1/auth/register` | POST | No | `backend/app/routers/auth.py` |
| `/api/v1/auth/login` | POST | No | `backend/app/routers/auth.py` |
| `/api/v1/favourites` | GET | JWT | `backend/app/routers/favourites.py` |
| `/api/v1/favourites/{id}` | POST | JWT | `backend/app/routers/favourites.py` |
| `/api/v1/favourites/{id}` | DELETE | JWT | `backend/app/routers/favourites.py` |

### Frontend

| Component | File | Purpose |
|-----------|------|---------|
| `AuthModal` | `frontend/src/components/AuthModal.jsx` | Login/Register modal, mode toggle |
| `api.js` | `frontend/src/services/api.js` | JWT auto-attach, auth + favourites API |

### Auth Flow

```
┌────────────┐     POST /auth/register     ┌──────────────┐
│ Register   │ ──────────────────────────▶  │ bcrypt hash  │
│ username   │ ◀──── {token, user_id} ──── │ JWT issue    │
│ email+pass │                              └──────────────┘
└────────────┘

┌────────────┐     POST /auth/login        ┌──────────────┐
│ Login      │ ──────────────────────────▶  │ verify bcrypt│
│ username   │ ◀──── {token, user_id} ──── │ JWT issue    │
│ password   │                               └──────────────┘
└────────────┘
     │
     │ localStorage.setItem("token", ...)
     │ localStorage.setItem("user", ...)
     ▼
┌────────────────────────────────────────────────┐
│ All subsequent API calls:                      │
│ fetch(url, { headers: { Authorization:         │
│   `Bearer ${localStorage.getItem("token")}` }})│
└────────────────────────────────────────────────┘
```

### Favourites Flow

```
Logged-in user clicks ☆ on carpark card
    │
    ▼
POST /api/v1/favourites/{carpark_id}
    │
    ▼
☆ → ★ (toggled in UI)
    │
    ▼
"Your Favourites" sidebar populated
    │
    ▼
Click favourite → map flies to location
```

## Demo Flow

1. Siti clicks "Login" → "Don't have an account? Register"
2. Fills username, email, password → Register → modal closes
3. Header shows "Welcome, siti_nurul"
4. Searches "Orchard" → clicks ☆ on "Orchard Boulevard" → becomes ★
5. "Your Favourites" section appears with the carpark
6. Next visit → logs in → favourites load automatically with live availability
7. Clicks ★ again → removes from favourites
8. Clicks "Logout" → favourites hidden, back to logged-out state
