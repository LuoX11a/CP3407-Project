---
layout: default
title: "US #13 — Frontend Architecture Refactor"
parent: Iteration 2
---

# User Story #13: Frontend Architecture Refactor

| Field | Detail |
|-------|--------|
| Priority | 40 |
| Estimated Days | 3 |
| Status | **Done** |
| Persona | Development Team |

## Story

> As a **developer maintaining the ParkGuideSG frontend**, I want the **React application to have a clean component architecture with proper separation of concerns** so that **adding new features is fast and the code is easy to understand**.

## Acceptance Criteria

- [x] Components split into focused, single-responsibility files
- [x] API calls centralized in `services/api.js` (no inline fetch calls in components)
- [x] Auth state managed at App level with localStorage persistence
- [x] GPS location managed with `useEffect` + `watchPosition` with proper cleanup
- [x] Favourites with optimistic UI updates
- [x] Address search with separate results panel
- [x] One-tap navigation as reusable `NavButton` component
- [x] Mobile-responsive CSS with media queries

## Implementation

### Component Architecture

```
App.jsx                        ← Root: state management, auth, GPS
├── MapView.jsx                ← Leaflet map with color-coded markers
├── RecommendationList.jsx     ← Sort controls + results list
│   └── CarparkCard.jsx        ← Individual carpark card
│       └── NavButton.jsx      ← Deep-link to Google/Apple Maps
├── AuthModal.jsx              ← Login/Register modal
└── services/
    └── api.js                 ← All fetch calls centralized
```

### Key Refactoring Decisions

1. **API layer separation** (`services/api.js`)
   - `fetchRecommendations(lat, lng, n, radius)` — single entry point
   - `searchCarparks(query)` — address search
   - `fetchCarparkDetail(id)` — detail endpoint
   - `fetchFavourites()`, `addFavourite(id)`, `removeFavourite(id)` — CRUD
   - `login()`, `register()`, `logout()` — auth
   - All error handling centralized (throws on !res.ok)

2. **State management** (React `useState` + `useCallback`)
   - Auth state: `authUser` (null | object), persisted to localStorage
   - GPS state: `userLocation`, `locationLoading`, `locationError`
   - Data state: `results`, `loading`, `apiError`
   - UI state: `selectedId`, `showAuth`, `showSearchResults`

3. **Mobile responsive** (CSS media queries)
   - Layout flips from side-by-side to stacked on < 768px
   - Map height adjusts for mobile viewport
   - Search bar full-width on mobile

## Related

- [US #15 Frontend Architecture Refactor (GitHub Issue #31)](https://github.com/LuoX11a/CP3407-Project/issues/31) — planned Iteration 3 enhancements
