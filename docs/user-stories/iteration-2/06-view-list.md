---
layout: default
title: "US #6 — View Carparks in List"
parent: Iteration 2
---

# User Story #6: View Carparks in List

| Field | Detail |
|-------|--------|
| Priority | 10 |
| Estimated Days | 3 |
| Status | **Done** |
| Persona | Both Tan Wei Ming & Siti Nurul |

## Story

> As a **driver viewing search results**, I want to **see carparks displayed in a scrollable list with key information at a glance** so that I can **quickly compare options without clicking into each one**.

## Acceptance Criteria

- [x] Each carpark displayed as a card showing: ID, address, distance, available lots, vacancy rate
- [x] Color-coded status badge (GREEN/YELLOW/RED) visible on each card
- [x] 3-hour vacancy trend sparkline chart on each card (Chart.js)
- [x] Sort controls: Distance, Available Lots, Vacancy Rate
- [x] Client-side sorting with `useMemo` for performance
- [x] Loading spinner shown while fetching data
- [x] Error state with retry button when API call fails
- [x] Empty state when no carparks found

## Implementation

### Frontend

**Component**: `frontend/src/components/RecommendationList.jsx`

- Sort dropdown with 3 options
- Renders `CarparkCard` for each result
- Loading spinner during data fetch
- Error banner with retry button
- Empty state message

**Component**: `frontend/src/components/CarparkCard.jsx`

- Available lots count (large number)
- Predicted vacancy rate percentage
- Total lots
- Color-coded status badge
- Mini trend chart (Chart.js `Line`, 3 data points)

### Backend

**Endpoint**: `GET /api/v1/recommend?lat=&lng=&n=5&radius_m=3000`

Returns `RecommendResponse` with array of `CarparkResult` objects, each containing:
- `carpark_id`, `address`, `total_lots`, `available_lots`
- `predicted_vacancy_rate`, `status` (GREEN/YELLOW/RED)
- `distance_m`, `weather`, `trend` (3-hour forecast)

## Demo Flow

1. User opens app → GPS acquired → API call fires automatically
2. Results render as cards in sidebar, sorted by distance (default)
3. User switches sort to "Vacancy Rate" → cards reorder instantly
4. Each card shows available lots number + color badge + mini chart
5. If API fails → error message with "Retry" button

## Related

- [US #1 — Search Nearby Carparks](../iteration-1/01-search-nearby)
- [US #2 — View Available Lots](../iteration-1/02-view-lots)
- [US #7 — Sort Carparks](../iteration-1/07-sort)
