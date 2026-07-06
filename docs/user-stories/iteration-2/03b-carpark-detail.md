---
layout: default
title: "US #3b — Carpark Detail Panel"
parent: Iteration 2
---

# User Story #3b: Carpark Detail Panel

| Field | Detail |
|-------|--------|
| Priority | 20 |
| Estimated Days | 5 |
| Status | **Todo** |
| Persona | Siti Nurul (Weekend Explorer) |

## Story

> As a **driver evaluating a specific carpark**, I want to **click a carpark and see a full detail panel with 24-hour availability history and complete information** so that I can **make a confident parking decision with all the data at my fingertips**.

## Acceptance Criteria

- [ ] Clicking a carpark card or map marker opens a detail panel/modal
- [ ] Panel shows: full address, car lots, motorcycle lots, coordinates, latest available count, weather
- [ ] 24-hour availability history chart (up to 288 data points) rendered with Chart.js
- [ ] History chart supports zoom/pan for exploring specific time windows
- [ ] Color-coded vacancy trend over time
- [ ] Loading state while fetching detail, error state if API fails
- [ ] Close button / click-outside dismisses panel

## Implementation

### Backend (Already Complete)

**Endpoint**: `GET /api/v1/carpark/{carpark_id}`

**File**: `backend/app/routers/carpark.py:34-65`

Returns `CarparkHistoryResponse` with:
- `carpark`: address, car_lots, motorcycle_lots, lat, lng, latest_available, latest_vacancy, latest_weather, latest_updated
- `history`: array of `{timestamp, available_lots, vacancy_rate, weather}` (up to 288 points / 24 hours)

### Frontend (To Build)

**New Component**: `frontend/src/components/CarparkDetail.jsx`

```
┌─────────────────────────────────────┐
│ ACM — Carpark Detail          [✕]  │
├─────────────────────────────────────┤
│ 📍 123 Orchard Boulevard, S228899  │
│ 🅿️  Car Lots: 410 | Motorcycle: 85 │
│ 🟢 Available: 145/410 (35%)        │
│ 🌤️  Weather: Cloudy                │
│ 🕐  Updated: 2026-07-06 14:30 SGT  │
├─────────────────────────────────────┤
│ 24-Hour Availability Trend          │
│ ┌─────────────────────────────────┐ │
│ │  📈  (interactive Chart.js)     │ │
│ │  x: time (24h)                  │ │
│ │  y: available lots / vacancy %  │ │
│ │  green fill >50%, yellow 20-50%,│ │
│ │  red <20% zones                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Set as Favourite ★]                │
└─────────────────────────────────────┘
```

**Integration Points**:
- `App.jsx`: add `selectedCarpark` state, call `fetchCarparkDetail(id)` on click
- `MapView.jsx`: marker click triggers detail fetch
- `CarparkCard.jsx`: card click triggers detail fetch
- `api.js`: `fetchCarparkDetail(id)` already defined, ready to use

## Demo Flow

1. Siti sees 5 carpark results in the sidebar
2. Clicks "Orchard Boulevard" carpark card
3. Detail panel slides in from right (or modal opens)
4. Sees full info: 410 car lots, 85 motorcycle lots, current 145 available
5. Scrolls down → 24-hour history chart shows parking patterns
6. Sees that availability drops sharply at 11am-2pm → decides to go early
7. Clicks ★ to save as favourite → detail panel closes
