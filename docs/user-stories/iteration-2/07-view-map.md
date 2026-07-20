---
layout: default
title: "US #7 — View Carparks on Map"
parent: Iteration 2
---

# User Story #7: View Carparks on Map

| Field | Detail |
|-------|--------|
| Priority | 20 |
| Estimated Days | 1 |
| Status | **Done** |
| Persona | Tan Wei Ming (Daily Commuter) |

## Story

> As a **driver approaching a destination**, I want to **see nearby carparks on an interactive map** so that I can **visually assess which one is closest to my destination and understand the surrounding area**.

## Acceptance Criteria

- [x] Map renders using Leaflet with OpenStreetMap tiles
- [x] User's GPS location shown as a blue marker
- [x] Nearby carparks displayed as color-coded circle markers (GREEN/YELLOW/RED)
- [x] Clicking a marker shows a popup with carpark name, available lots, and status
- [x] Map automatically centers on user location
- [x] Clicking a marker selects that carpark in the sidebar list
- [x] Map container fills available space with absolute positioning

## Implementation

### Frontend

**Component**: `frontend/src/components/MapView.jsx`

- Uses `react-leaflet` (Leaflet + React bindings)
- OpenStreetMap tile layer (free, no API key needed)
- Circle markers color-coded by vacancy status:
  - Green `#4caf50` — plenty of space (>50%)
  - Yellow `#ff9800` — filling up (20-50%)
  - Red `#f44336` — nearly full (<20%)
- Popup on click with carpark name, available lots, and Navigate button
- Selected carpark gets a highlighted marker style
- Auto-fits bounds to show all visible markers

### Backend

Same `GET /api/v1/recommend` endpoint provides coordinates (`lat`, `lng`) for each carpark result.

## Demo Flow

1. App opens → map centers on user's GPS location
2. Blue dot shows current position
3. Colored circles appear for nearby carparks
4. Green circle = lots of space, Red = nearly full
5. Tap a marker → popup shows details + Navigate button
6. Selected carpark marker enlarges/highlights

## Related

- [US #1 — Search Nearby Carparks](../iteration-1/01-search-nearby)
- [US #8 — One-Tap Navigate](08-navigation)
