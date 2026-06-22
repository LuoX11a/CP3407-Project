---
layout: default
title: "US #1 — Search Nearby Carparks"
parent: Iteration 1
---

# User Story #1: Search Nearby Carparks

| Field | Detail |
|-------|--------|
| Priority | 10 |
| Estimated Days | 5 |
| Status | **Done** |
| Persona | Tan Wei Ming (Daily Commuter) |

## Story

> As a **driver approaching a destination**, I want to **see nearby HDB carparks with real-time availability** so that I can **drive directly to one with empty lots instead of circling**.

## Acceptance Criteria

- [x] App detects user GPS location automatically
- [x] System queries carparks within configurable radius (default 3000m) using haversine distance
- [x] Results include carpark ID, address, distance, and live available lots
- [x] Results are ordered by distance from user
- [x] User sees results on both a map and a list view

## Implementation

### Backend

**Endpoint**: `GET /api/v1/recommend?lat=1.35&lng=103.81&n=5&radius_m=3000`

**File**: `backend/app/routers/recommend.py`

```python
@router.get("/recommend", response_model=RecommendResponse)
def recommend(
    lat: float = Query(...),
    lng: float = Query(...),
    n: int = Query(default=5),
    radius_m: int = Query(default=1000),
):
    carparks = query_nearby_carparks(lat, lng, radius_m, n)
    # ... prediction + assembly
```

**Service**: `backend/app/services/geospatial.py` — `query_nearby_carparks()` uses PostgreSQL haversine distance to find carparks within the search radius, joined with latest availability data from `v_carpark_latest`.

### Frontend

**File**: `frontend/src/App.jsx`

- `navigator.geolocation.watchPosition` tracks user GPS
- `fetchRecommendations(lat, lng, 5, 3000)` called automatically when location updates
- Results render in `MapView` (map markers) and `RecommendationList` (cards)

## Demo Flow

1. User opens ParkGuideSG in browser
2. Browser prompts for location permission
3. GPS coordinates acquired → displayed in header
4. API call fires automatically → nearby carparks load on map and in sidebar
5. Each result shows distance, available lots, and vacancy prediction
