---
layout: default
title: "US #8 — Recommend Best Carpark"
parent: Iteration 2
---

# User Story #8: Recommend Best Carpark

| Field | Detail |
|-------|--------|
| Priority | 30 |
| Estimated Days | 3 |
| Status | **Done** |
| Persona | Both Tan Wei Ming & Siti Nurul |

## Story

> As a **driver who wants to park quickly**, I want the system to **recommend the best carpark based on distance, availability, and predicted vacancy** so that I **don't have to manually compare every option**.

## Acceptance Criteria

- [x] System ranks carparks by composite factors: distance + vacancy rate + time of day
- [x] ML model (LightGBM) predicts vacancy rate for each carpark
- [x] Three-tier fallback: ML Model → LLM (DeepSeek API) → Heuristic rules
- [x] Heuristic uses time-of-day, day-of-week, weekend/weekday patterns
- [x] Carparks without EPS get k-NN spatial proxy predictions from nearest EPS carparks
- [x] Recommendation API returns ranked results with query execution time

## Implementation

**Endpoint**: `GET /api/v1/recommend?lat=1.35&lng=103.81&n=5&radius_m=3000`

**File**: `backend/app/routers/recommend.py`

### Prediction Pipeline (`backend/app/services/inference.py`)

```
1. LightGBM model (primary)
   ├── Loaded from ml/model/carpark_predictor.joblib
   ├── Features: hour, day_of_week, is_weekend, is_holiday, weather, total_lots
   └── Fallback if model unavailable
2. DeepSeek LLM (backup)
   ├── Requires DEEPSEEK_API_KEY env var
   └── Fallback if API key missing or call fails
3. Heuristic rules (guaranteed)
   ├── Peak hours (8-10am, 5-8pm) → low vacancy
   ├── Weekends → moderate vacancy
   └── Late night → high vacancy
```

### k-NN Spatial Proxy

For carparks without EPS (Electronic Parking System) data, the system uses k-Nearest Neighbors to find the nearest EPS-enabled carparks and averages their predictions.

**File**: `ml/knn_spatial_proxy.py`

## Demo Flow

1. User GPS coordinates sent to `/api/v1/recommend`
2. Backend queries nearby carparks (Haversine distance in PostgreSQL)
3. ML model predicts vacancy rate for each carpark
4. Results ranked by composite score
5. Response includes `query_time_ms` for performance monitoring
6. Each result shows predicted vacancy + weather + 3-hour trend

## Related

- [US #1 — Search Nearby Carparks](../iteration-1/01-search-nearby)
- [Test Strategy](../../test-strategy) — ML Model Testing section
