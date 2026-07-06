---
layout: default
title: "US #6 — View Carparks on Map"
parent: Iteration 2
---

# User Story #6: View Carparks on Map

| Field | Detail |
|-------|--------|
| Priority | 20 |
| Estimated Days | 1 |
| Status | **Done** |
| Persona | Tan Wei Ming (Daily Commuter) |

## Story

> As a **driver navigating to a carpark**, I want to **see carpark locations on an interactive map** so that I can **understand their spatial relationship to my destination and visually choose the most convenient one**.

## Acceptance Criteria

- [x] Interactive Leaflet map with OpenStreetMap tiles
- [x] User's GPS location shown as a blue dot marker
- [x] Nearby carparks shown as color-coded circle markers (GREEN/YELLOW/RED)
- [x] Map auto-centers on user's location on first GPS fix
- [x] Clicking a marker selects the carpark and opens a popup with details
- [x] Popup shows: carpark ID, available lots, distance, weather, status
- [x] Selected carpark marker popup opens automatically
- [x] Map takes absolute position (does not scroll with page)

## Implementation

### Frontend

**File**: `frontend/src/components/MapView.jsx`

The `MapView` component renders an interactive Leaflet map:

```jsx
// Init map once with OpenStreetMap tiles
const map = L.map(mapRef.current, {
  center: SINGAPORE_CENTER,  // [1.3521, 103.8198]
  zoom: 14,
  zoomControl: true,
});

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; OpenStreetMap | Data.gov.sg',
  maxZoom: 19,
}).addTo(map);
```

### Marker Design

**User location** — blue dot with ripple effect:
```javascript
const icon = L.divIcon({
  html: `<div style="
    width:16px;height:16px;border-radius:50%;
    background:#2196f3;border:3px solid #fff;
    box-shadow:0 0 0 4px rgba(33,150,243,0.3);
  "></div>`,
});
```

**Carpark markers** — color-coded by vacancy status:
- Green `#4caf50` — GREEN status (>50% vacancy)
- Yellow `#ff9800` — YELLOW status (20–50% vacancy)
- Red `#f44336` — RED status (<20% vacancy)

### Map Behavior

| Event | Action |
|-------|--------|
| First GPS fix | Map centers on user location |
| GPS update | Blue dot moves, map stays in place |
| Click carpark card | Corresponding map marker popup opens |
| Click map marker | Marker popup opens, sidebar card highlights |
| Map container | `position: absolute` — fills panel without scroll |

### Popup Content

```
┌─────────────────────┐
│ ACM                │
│ Available: 145/410 (35%) │
│ Distance: 230m | Weather: Cloudy │
│ Status: GREEN       │
└─────────────────────┘
```

## Demo Flow

1. App loads → map appears filling left panel
2. GPS acquired → map flies to user's current location
3. Blue dot appears at user position
4. 5 color-coded carpark markers appear on map
5. User sees green markers first (most available) — clicks one
6. Popup opens with carpark details
7. Sidebar card for that carpark highlights simultaneously
