---
layout: default
title: "US #5-6 — View Carparks in List & Map"
parent: Iteration 2
---

# User Story #5-6: View Carparks in List & Map

| Field | Detail |
|-------|--------|
| Priority | 10 |
| Estimated Days | 5 |
| Status | **Done** |
| Persona | Tan Wei Ming (Daily Commuter) |

## Story

> As a **driver comparing parking options**, I want to **view nearby carparks on an interactive map and a sortable list** so that I can **quickly scan availability, see locations spatially, and choose the best option**.

## Acceptance Criteria

- [x] Interactive Leaflet map with OpenStreetMap tiles
- [x] User GPS shown as blue dot, auto-centers on first fix
- [x] Carpark markers color-coded by vacancy status (GREEN/YELLOW/RED)
- [x] Clicking a marker opens popup with carpark details
- [x] Sidebar shows carpark cards as scrollable list
- [x] Each card: carpark ID, distance, available lots, predicted %, total lots, status badge
- [x] Cards include mini trend sparkline (3-hour forecast, Chart.js)
- [x] Sort dropdown: Distance / Available Lots / Vacancy Rate (client-side `useMemo`)
- [x] Clicking card ↔ map marker highlights both
- [x] Loading state (spinner), error state (retry), empty state

## Implementation

### Frontend

| Component | File | Purpose |
|-----------|------|---------|
| `App` | `frontend/src/App.jsx` | GPS tracking, data fetching, state management |
| `MapView` | `frontend/src/components/MapView.jsx` | Leaflet map, color-coded markers, popups |
| `RecommendationList` | `frontend/src/components/RecommendationList.jsx` | Sortable card list, sort dropdown |
| `CarparkCard` | `frontend/src/components/CarparkCard.jsx` | Individual card with stats + trend chart |

### Backend

| Endpoint | File | Purpose |
|----------|------|---------|
| `GET /api/v1/recommend` | `backend/app/routers/recommend.py` | Top-N nearby carparks with ML predictions |
| `GET /api/v1/carpark/{id}` | `backend/app/routers/carpark.py` | Carpark detail + 24h history |

### Data Flow

```
GPS (navigator.geolocation.watchPosition)
    │
    ▼
fetchRecommendations(lat, lng, 5, 3000)
    │
    ▼
GET /api/v1/recommend
    │
    ├──▶ MapView (markers + popups)
    └──▶ RecommendationList (sortable cards)
              │
              └──▶ CarparkCard (stats + trend chart)
```

## Demo Flow

1. User opens app → GPS acquired → map flies to location
2. 5 color-coded markers appear on map, 5 cards appear in sidebar
3. Wei Ming keeps default "Distance" sort — sees closest carparks
4. Clicks a green marker → popup opens, sidebar card highlights
5. Switches sort to "Vacancy Rate" → list reorders instantly
6. Map and list stay in sync — selecting one highlights the other
