---
layout: default
title: "US #4 — Search by Area or Address"
parent: Iteration 1
---

# User Story #4: Search by Area or Address

| Field | Detail |
|-------|--------|
| Priority | 20 |
| Estimated Days | 1 |
| Status | **Done** |
| Persona | Siti Nurul (Weekend Explorer) |

## Story

> As a **driver going to an unfamiliar area**, I want to **search carparks by typing an address or area name** so that I can **find parking options near my intended destination before I leave**.

## Acceptance Criteria

- [x] Search input available in the app header
- [x] API supports ILIKE fuzzy text matching on carpark addresses
- [x] Search results show carpark ID, address, and available lots
- [x] Clicking a search result re-centers the map and selects that carpark
- [x] Empty state shown when no carparks match

## Implementation

### Backend

**Endpoint**: `GET /api/v1/carpark/search?q=orchard&limit=20`

**File**: `backend/app/routers/carpark.py:14-31`

```python
@router.get("/carpark/search", response_model=SearchResponse)
def carpark_search(
    q: str = Query(...),
    limit: int = Query(default=20),
):
    rows = search_carparks_by_address(q, limit)
    return SearchResponse(results=[...])
```

**Service**: `backend/app/services/geospatial.py:108-127` — `search_carparks_by_address()`:

```sql
SELECT c.carpark_id, c.address, c.car_lots, c.lat, c.lng,
       l.available_lots, l.vacancy_rate
FROM carparks c
LEFT JOIN v_carpark_latest l ON c.carpark_id = l.carpark_id
WHERE c.address ILIKE '%orchard%'
ORDER BY c.carpark_id
LIMIT 20
```

### Frontend

**File**: `frontend/src/App.jsx:162-171`

The header contains a search form:
```jsx
<form className="search-form" onSubmit={handleSearch}>
  <input
    placeholder="Search address or area..."
    value={searchQuery}
    onChange={(e) => setSearchQuery(e.target.value)}
  />
  <button type="submit">Search</button>
</form>
```

Search results panel (`showSearchResults` state, lines 203-227):
- Each result shows carpark_id, address, and available lots
- Click fires `handleSearchSelect(cp)` → sets userLocation to carpark coordinates, centers map, selects carpark
- Empty state: "No carparks found"

## Demo Flow

1. Siti types "Orchard" into the search bar → Enter
2. Results panel slides in with all Orchard-area carparks
3. Each result shows: carpark ID, full address, available lots
4. Clicks "Orchard Boulevard" → map flies to that location, sidebar shows recommendations nearby
5. Types "asdfxyz" → "No carparks found" empty state
