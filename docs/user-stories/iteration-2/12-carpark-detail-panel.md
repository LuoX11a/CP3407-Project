---
layout: default
title: "US #12 — Carpark Detail Panel"
parent: Iteration 2
---

# User Story #12: Carpark Detail Panel

| Field | Detail |
|-------|--------|
| Priority | 40 |
| Estimated Days | 3 |
| Status | **Done** |
| Persona | Siti Nurul (Weekend Explorer) |

## Story

> As a **driver evaluating a specific carpark**, I want to **see a detailed panel with full information including 24-hour availability history** so that I can **make a confident decision about where to park**.

## Acceptance Criteria

- [x] API returns full carpark detail by `carpark_id`
- [x] Response includes: address, car lots, motorcycle lots, coordinates
- [x] Latest availability snapshot: available lots, vacancy rate, weather, timestamp
- [x] 24-hour availability history returned (up to 288 data points, one per 5 min)
- [x] Frontend API function `fetchCarparkDetail()` ready for UI integration
- [x] 404 returned for unknown carpark IDs
- [x] History data includes weather condition at each timestamp

## Implementation

### Backend

**Endpoint**: `GET /api/v1/carpark/{carpark_id}`

**File**: `backend/app/routers/carpark.py:34-65`

```python
@router.get("/carpark/{carpark_id}", response_model=CarparkHistoryResponse)
def carpark_detail(carpark_id: str):
    detail = query_carpark_detail(carpark_id)   # joins carparks + v_carpark_latest
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Carpark '{carpark_id}' not found")
    history = query_carpark_history(carpark_id, hours=24)
    return CarparkHistoryResponse(carpark=..., history=[...])
```

**Service**: `backend/app/services/geospatial.py`
- `query_carpark_detail(id)` — joins `carparks` table with `v_carpark_latest` view
- `query_carpark_history(id, hours=24)` — queries `availability_logs` for the past 24h

### Response Schema

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
    history: list[HistoryPoint]
```

### Frontend

**File**: `frontend/src/services/api.js:30-32`

```javascript
export async function fetchCarparkDetail(id) {
  const res = await fetch(`${API_BASE}/carpark/${id}`);
  if (!res.ok) throw new Error(`Carpark ${id} not found`);
  return res.json();
}
```

Ready for UI integration in a detail panel/sheet component.

## Demo Flow

1. User clicks a carpark card → detail panel slides in
2. Panel header: carpark ID, full address
3. Key stats: Total car lots (410), Motorcycle lots (50)
4. Live status: 145 available, 35% vacancy (YELLOW)
5. Weather: "Cloudy"
6. 24-hour chart: availability over past day with weather overlay
7. Action buttons: Navigate, Add to Favourites

## Related

- [US #3 — View Carpark Details (original story)](../iteration-1/03-carpark-detail)
