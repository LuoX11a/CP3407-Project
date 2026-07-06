---
layout: default
title: "US #8 — Save Favourite Carparks"
parent: Iteration 2
---

# User Story #8: Save Favourite Carparks

| Field | Detail |
|-------|--------|
| Priority | 40 |
| Estimated Days | 1 |
| Status | **Done** |
| Persona | Siti Nurul (Weekend Explorer) |

## Story

> As a **regular driver who frequents the same areas**, I want to **save carparks as favourites** so that I can **quickly check availability at my preferred carparks without searching every time**.

## Acceptance Criteria

- [x] Logged-in users can add carparks to favourites via star icon on each card
- [x] Logged-in users can remove carparks from favourites
- [x] Favourites appear in a dedicated sidebar section "Your Favourites"
- [x] Clicking a favourite re-centers the map and searches nearby that carpark
- [x] Favourites persist across sessions (stored in PostgreSQL)
- [x] Non-logged-in users clicking the star are prompted to login
- [x] `POST /api/v1/favourites/{carpark_id}` — add favourite (protected)
- [x] `DELETE /api/v1/favourites/{carpark_id}` — remove favourite (protected)
- [x] `GET /api/v1/favourites` — list all favourites with live availability (protected)

## Implementation

### Backend

**File**: `backend/app/routers/favourites.py`

All endpoints require JWT authentication via `get_current_user` dependency.

```python
# List favourites with live availability
@router.get("/favourites")
def list_favourites(user: dict = Depends(get_current_user)):
    # JOIN favourites → carparks → v_carpark_latest
    # Returns: carpark_id, address, car_lots, lat, lng,
    #          available_lots, vacancy_rate, weather_condition
    return {"favourites": [...]}

# Add favourite (idempotent — ON CONFLICT DO NOTHING)
@router.post("/favourites/{carpark_id}")
def add_favourite(carpark_id: str, user: dict = Depends(get_current_user)):
    # Validates carpark exists (404 if not found)
    # INSERT INTO favourites ... ON CONFLICT DO NOTHING
    return {"status": "ok"}

# Remove favourite
@router.delete("/favourites/{carpark_id}")
def remove_favourite(carpark_id: str, user: dict = Depends(get_current_user)):
    # DELETE FROM favourites WHERE user_id AND carpark_id
    return {"status": "ok"}
```

### Frontend

**File**: `frontend/src/App.jsx`

Favourites state management:
```javascript
// Load favourites on login
useEffect(() => {
  if (isLoggedIn) {
    fetchFavourites()
      .then((data) => setFavourites(data.favourites || []))
      .catch(() => {});
  } else {
    setFavourites([]);
  }
}, [isLoggedIn]);

// Toggle favourite
const handleToggleFavourite = useCallback(async (cp) => {
  if (!isLoggedIn) {
    setShowAuth(true);  // Prompt login
    return;
  }
  const isFav = favourites.some((f) => f.carpark_id === cp.carpark_id);
  if (isFav) {
    await removeFavourite(cp.carpark_id);
    setFavourites((prev) => prev.filter(...));
  } else {
    await addFavourite(cp.carpark_id);
    setFavourites((prev) => [...prev, {...}]);
  }
}, [isLoggedIn, favourites]);
```

**File**: `frontend/src/components/CarparkCard.jsx`

Star button on each card:
```jsx
<span className={`star-btn ${favourited ? "favourited" : ""}`}
      onClick={(e) => { e.stopPropagation(); onToggleFavourite(carpark); }}>
  {favourited ? "★" : "☆"}
</span>
```

### UI States

| State | Behavior |
|-------|----------|
| Not logged in | Star icon hidden on cards |
| Logged in, not faved | Empty star ☆ — click to add |
| Logged in, faved | Filled star ★ — click to remove |
| Not logged in, clicks star | Auth modal opens |
| Favourites sidebar | Shown when logged in + has favs |
| API error | Silently fails (non-blocking) |

## Demo Flow

1. Siti logs into her account
2. Searches "Orchard" → sees carpark results
3. Clicks ☆ on "Orchard Boulevard" → becomes ★ → added to favourites
4. "Your Favourites" section appears in sidebar with the carpark
5. Next visit → favourites load automatically with live availability
6. Clicks a favourite → map flies to that location
7. Clicks ★ again → removes from favourites
