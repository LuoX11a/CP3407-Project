---
layout: default
title: "US #5 — View Carparks in List"
parent: Iteration 2
---

# User Story #5: View Carparks in List

| Field | Detail |
|-------|--------|
| Priority | 10 |
| Estimated Days | 3 |
| Status | **Done** |
| Persona | Tan Wei Ming (Daily Commuter) |

## Story

> As a **driver comparing parking options**, I want to **view nearby carparks as a scrollable list of summary cards** so that I can **quickly scan and compare key information without clicking each one**.

## Acceptance Criteria

- [x] Sidebar displays carpark results as a scrollable list of cards
- [x] Each card shows: carpark ID, distance, available lots, predicted vacancy rate, total lots, status badge
- [x] Cards include a mini trend sparkline chart (3-hour forecast)
- [x] Clicking a card selects it and highlights corresponding map marker
- [x] Selected card is visually highlighted
- [x] Empty state shown when no results: "No carparks found nearby"
- [x] Loading state with spinner while fetching results

## Implementation

### Frontend

**File**: `frontend/src/components/RecommendationList.jsx`

The `RecommendationList` component renders the sidebar result list:

- Accepts `results`, `loading`, `error`, `selectedId`, `onSelect` props
- Client-side sort via `useMemo` with 3 sort modes (Distance, Available Lots, Vacancy Rate)
- Sort dropdown appears above results when results exist
- Maps over sorted results to render `CarparkCard` components

**File**: `frontend/src/components/CarparkCard.jsx`

Each `CarparkCard` displays:
```jsx
<div className="carpark-card">
  <div className="card-header">
    <span>{carpark.carpark_id}</span>
    <span>{carpark.distance_m}m</span>
  </div>
  <div className="card-stats">
    Available / Predicted % / Total Lots / Status badge
  </div>
  <div className="card-address">{carpark.address}</div>
  <div className="trend-chart">
    <Line data={chartData} options={chartOpts} />
  </div>
</div>
```

- Status badge: GREEN (>50%), YELLOW (20–50%), RED (<20%)
- Trend chart uses Chart.js `Line` with 3-hour forecast points
- Star button on each card for adding/removing favourites (logged-in users)

### States Handled

| State | UI |
|-------|-----|
| Loading | Spinner + "Searching nearby carparks..." |
| Error | Error message + Retry button |
| Empty (no GPS) | "Waiting for GPS location..." |
| Empty (no results) | "No carparks found nearby. Try expanding your search radius." |
| Results | Scrollable list of carpark cards |

## Demo Flow

1. User opens app → GPS location acquired
2. API returns 5 nearby carparks → list populates in sidebar
3. Each card shows color-coded status + key stats at a glance
4. User clicks a card → card highlights, map marker opens popup
5. User changes sort to "Vacancy Rate" → list re-orders instantly
6. Star icon on card toggles favourite status (requires login)
