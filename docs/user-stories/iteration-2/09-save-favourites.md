---
layout: default
title: "US #9 — Save Favourite Carparks"
parent: Iteration 2
---

# User Story #9: Save Favourite Carparks

| Field | Detail |
|-------|--------|
| Priority | 40 |
| Estimated Days | 1 |
| Status | **Done** |
| Persona | Siti Nurul (Weekend Explorer) |

## Story

> As a **regular driver**, I want to **save carparks to my favourites** so that I can **quickly check availability at my go-to parking spots without searching every time**.

## Acceptance Criteria

- [x] Authenticated users can view their favourites list
- [x] Star icon on each carpark card toggles favourite status
- [x] Favourites panel shows saved carparks with live availability
- [x] Clicking a favourite flies to that carpark on the map
- [x] Removing a favourite is instant (optimistic UI update)
- [x] Unauthenticated users clicking the star see the login prompt
- [x] Duplicate favourites handled idempotently (no error)

## Implementation

### Backend

**Endpoints** (`backend/app/routers/favourites.py`):

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/favourites` | Required | List user's saved carparks |
| `POST` | `/api/v1/favourites/{carpark_id}` | Required | Add carpark to favourites |
| `DELETE` | `/api/v1/favourites/{carpark_id}` | Required | Remove carpark from favourites |

- Validates carpark exists before adding (returns 404 if not)
- Uses `ON CONFLICT DO NOTHING` for idempotent adds
- Returns live availability data joined from `v_carpark_latest`

### Frontend

**File**: `frontend/src/App.jsx`

- Favourites loaded on login via `fetchFavourites()`
- Star icon toggling with `handleToggleFavourite(cp)`
- Favourites panel in sidebar with: carpark ID, address, remove button
- Clicking favourite calls `handleSearchSelect(f)` → map fly-to

## Test Cases

See [US #6 Test Cases](06-favourites) for detailed Given/When/Then test cases (4 test cases).

## Demo Flow

1. Siti logs in → favourites panel appears (empty initially)
2. Searches "Orchard" → finds a carpark → taps star icon
3. Star fills in → carpark added to favourites panel
4. Favourites panel shows saved carpark with live lot count
5. Taps the favourite → map flies to that location
6. Taps ✕ on a favourite → removed instantly

## Related

- [US #6 — Manage Favourite Carparks (detailed test cases)](06-favourites)
- [US #10 — Register Account](10-register-account)
