---
layout: default
title: "US #2 — View Available Lots"
parent: Iteration 1
---

# User Story #2: View Available Lots

| Field | Detail |
|-------|--------|
| Priority | 10 |
| Estimated Days | 5 |
| Status | **Done** |
| Persona | Tan Wei Ming (Daily Commuter) |

## Story

> As a **driver looking for parking**, I want to **see how many lots are available at each nearby carpark** so that I can **choose one that isn't full**.

## Acceptance Criteria

- [x] Each carpark result displays `available_lots` and `total_lots`
- [x] Vacancy rate shown as a percentage (predicted by ML model)
- [x] Color-coded status: GREEN (>50%), YELLOW (20–50%), RED (<20%)
- [x] Map markers are color-coded by status
- [x] Carpark card shows a mini trend chart (3-hour forecast)
- [x] Map popup also shows available lot numbers

## Implementation

### Backend

Vacancy data comes from `v_carpark_latest` view joined in the geospatial query. The prediction pipeline (`backend/app/services/inference.py`) enhances raw availability with an ML-predicted vacancy rate.

**Status logic** in `backend/app/routers/recommend.py:22-27`:

```python
def _status(vacancy: float) -> str:
    if vacancy > 0.5:
        return "GREEN"
    elif vacancy > 0.2:
        return "YELLOW"
    return "RED"
```

### Frontend

**CarparkCard** (`frontend/src/components/CarparkCard.jsx`) displays:
- Available lots count (large number)
- Predicted vacancy rate (percentage)
- Total lots
- Color-coded status badge
- Mini trend sparkline chart (Chart.js `Line`)

**MapView** (`frontend/src/components/MapView.jsx`) uses color-coded circle markers:
- Green `#4caf50` — plenty of space
- Yellow `#ff9800` — filling up
- Red `#f44336` — nearly full

## Demo Flow

1. Recommendations load → each card shows `Available: 145` / `Total: 410`
2. Status badge shows GREEN / YELLOW / RED
3. Map markers match the status color
4. Click a marker → popup confirms available lot count
5. Trend chart shows predicted availability over next 3 hours
