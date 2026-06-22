---
layout: default
title: "US #3 — View Carpark Details"
parent: Iteration 1
---

# User Story #3: View Carpark Details

| Field | Detail |
|-------|--------|
| Priority | 10 |
| Estimated Days | 5 |
| Status | **Done** |
| Persona | Siti Nurul (Weekend Explorer) |

## Story

> As a **driver planning a trip**, I want to **see detailed information about a specific carpark** including its total capacity, motorcycle lots, and recent availability history so that I can **make an informed parking decision**.

## Acceptance Criteria

- [x] API returns full carpark detail by `carpark_id`
- [x] Response includes: address, car lots, motorcycle lots, coordinates
- [x] Includes latest availability snapshot (available lots, vacancy rate, weather, timestamp)
- [x] Returns 24-hour availability history (up to 288 data points)
- [x] Frontend has `fetchCarparkDetail()` ready to call

## Implementation

### Backend

**Endpoint**: `GET /api/v1/carpark/{carpark_id}`

**File**: `backend/app/routers/carpark.py:34-65`

```python
@router.get("/carpark/{carpark_id}", response_model=CarparkHistoryResponse)
def carpark_detail(carpark_id: str):
    detail = query_carpark_detail(carpark_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Carpark '{carpark_id}' not found")
    history = query_carpark_history(carpark_id, hours=24)
    return CarparkHistoryResponse(carpark=..., history=[...])
```

**Service**: `backend/app/services/geospatial.py`
- `query_carpark_detail()` — joins `carparks` with `v_carpark_latest` for live availability
- `query_carpark_history()` — queries `availability_logs` for the past 24 hours (288 rows max)

### Response Schema (`backend/app/models/schemas.py`):

```python
class CarparkDetail(BaseModel):
    carpark_id: str
    address: str
    car_lots: int
    motorcycle_lots: int
    lat: float
    lng: float
    latest_available: int | None
    latest_vacancy: float | None
    latest_weather: str | None
    latest_updated: str | None

class CarparkHistoryResponse(BaseModel):
    carpark: CarparkDetail
    history: list[HistoryPoint]   # timestamp, available_lots, vacancy_rate, weather
```

### Frontend

`frontend/src/services/api.js:30-32` — `fetchCarparkDetail(id)` is defined and ready for UI integration.

## Demo Flow

1. User clicks on a carpark card or map marker
2. Frontend calls `GET /api/v1/carpark/A11`
3. Response returns full detail + 24-hour timestamps of availability
4. UI shows address, coordinates, total lots, latest available count, weather at location
