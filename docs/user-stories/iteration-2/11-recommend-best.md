---
layout: default
title: "US #11 — Recommend Best Carpark"
parent: Iteration 2
---

# User Story #11: Recommend Best Carpark

| Field | Detail |
|-------|--------|
| Priority | 30 |
| Estimated Days | 3 |
| Status | **Done** |
| Persona | Both Tan Wei Ming & Siti Nurul |

## Story

> As a **driver who wants the best parking option**, I want the system to **intelligently recommend the best carpark based on distance, availability, and predicted demand** so that I can **make a confident decision without manually comparing every option**.

## Acceptance Criteria

- [x] `GET /api/v1/recommend` endpoint returns top-N carparks ranked by recommendation score
- [x] Recommendation considers: haversine distance, live availability, ML-predicted vacancy rate
- [x] ML model (Random Forest) predicts vacancy rate based on time, weather, and location features
- [x] Fallback to database vacancy values when ML prediction fails
- [x] Each result includes: carpark ID, address, total/available lots, predicted vacancy %, status, distance, weather, 3-hour trend
- [x] Response includes query execution time for performance monitoring
- [x] Configurable search radius (100m–5000m) and result count (1–10)

## Implementation

### Backend

**Endpoint**: `GET /api/v1/recommend?lat=1.35&lng=103.81&n=5&radius_m=3000`

**File**: `backend/app/routers/recommend.py`

```python
@router.get("/recommend", response_model=RecommendResponse)
def recommend(
    lat: float = Query(...),
    lng: float = Query(...),
    n: int = Query(default=5, ge=1, le=10),
    radius_m: int = Query(default=1000, ge=100, le=5000),
):
    # 1. Geospatial query — PostgreSQL haversine distance
    carparks = query_nearby_carparks(lat, lng, radius_m, n)

    # 2. ML prediction — Random Forest model
    preds = predict(carparks)  # falls back to DB vacancy on failure

    # 3. Assemble results with status + trend
    results = [CarparkResult(...) for cp, pred in zip(carparks, preds)]

    return RecommendResponse(results=results, query_time_ms=...)
```

### Recommendation Pipeline

```
User GPS (lat, lng)
    │
    ▼
┌─────────────────────────┐
│ Geospatial Query         │
│ query_nearby_carparks()  │  ← PostgreSQL ST_Distance / haversine
│ Returns carparks within   │
│ radius_m, sorted by       │
│ distance, limited to n    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ ML Prediction            │
│ predict()                │  ← Random Forest Regressor
│ Features: hour, day_of_   │
│ week, weather, location   │
│ Returns: vacancy_rate     │
│ Fallback: DB vacancy_rate │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Result Assembly          │
│ _status() → GREEN/YELLOW/│
│            RED           │
│ _make_trend() → 3hr      │
│ forecast points          │
└───────────┬─────────────┘
            │
            ▼
    RecommendResponse {
      results: CarparkResult[],
      query_time_ms: float
    }
```

### ML Model

**File**: `ml/train.py` — Trains a Random Forest Regressor on historical availability data.

**Features** (`ml/features.py`):
| Feature | Description |
|---------|-------------|
| `hour_sin` / `hour_cos` | Cyclic time encoding (time of day) |
| `day_of_week_sin` / `day_of_week_cos` | Cyclic day encoding |
| `is_weekend` | Boolean weekend flag |
| `weather_condition_encoded` | Label-encoded weather |
| `lat` / `lng` | Carpark coordinates |
| `car_lots` | Total capacity |

**Model file**: `ml/model/carpark_predictor.joblib`

### Status Classification

```python
def _status(vacancy: float) -> str:
    if vacancy > 0.5:   return "GREEN"   # Plenty of space
    elif vacancy > 0.2: return "YELLOW"  # Filling up
    return "RED"                          # Nearly full
```

## Demo Flow

1. User opens app → GPS location sent to `/api/v1/recommend`
2. Backend queries 5 nearest carparks within 3000m
3. ML model predicts vacancy rate for each
4. Results ranked and returned with status + trend
5. Frontend renders ranked list + color-coded map markers
6. If ML fails → gracefully falls back to latest DB vacancy rate
7. Response time displayed in logs for monitoring
