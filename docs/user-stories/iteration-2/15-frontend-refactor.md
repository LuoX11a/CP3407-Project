---
layout: default
title: "US #15 — Frontend Architecture Refactor"
parent: Iteration 2
---

# User Story #15: Frontend Architecture Refactor

| Field | Detail |
|-------|--------|
| Priority | 30 |
| Estimated Days | 3 |
| Status | **Todo** |
| Persona | Developer |

## Story

> As a **developer maintaining the ParkGuideSG frontend**, I want to **refactor the monolithic App.jsx into reusable hooks and components with proper error boundaries** so that the **codebase is maintainable, testable, and resilient to runtime errors**.

## Acceptance Criteria

- [ ] Extract `useGeolocation` hook: GPS watch, loading/error states, fallback location
- [ ] Extract `useAuth` hook: login/register/logout, token persistence, auth state
- [ ] Extract `useFavourites` hook: fetch/add/remove, optimistic UI updates
- [ ] Extract `useSearch` hook: debounced search, results state, error handling
- [ ] Extract `Header` component (currently ~30 lines inline in App.jsx)
- [ ] Add `ErrorBoundary` component wrapping map and sidebar independently
- [ ] App.jsx reduced to ≤80 lines (orchestration only)
- [ ] All existing functionality preserved — zero regression
- [ ] Component tree documented in README or architecture doc

## Current State

**File**: `frontend/src/App.jsx` — 280 lines, 14 state variables in one component

```
App.jsx (280 lines)
├── GPS logic (30 lines) ── inline useEffect
├── Auth logic (20 lines) ── inline useCallback
├── Favourites logic (30 lines) ── inline useCallback
├── Search logic (25 lines) ── inline useCallback
├── Recommendations logic (20 lines) ── inline useCallback
├── Header JSX (30 lines) ── inline in return
├── Search Results JSX (25 lines) ── inline in return
├── Favourites JSX (25 lines) ── inline in return
├── Recommendation List JSX (10 lines)
└── Auth Modal JSX (5 lines)
```

## Target Architecture

```
App.jsx (~80 lines, orchestration only)
│
├── hooks/
│   ├── useGeolocation.js    — GPS watch, loading, error, fallback
│   ├── useAuth.js            — register, login, logout, token mgmt
│   ├── useFavourites.js      — fetch, add, remove, optimistic update
│   └── useSearch.js          — debounced query, results, error
│
├── components/
│   ├── Header.jsx            — Logo, search bar, GPS info, auth buttons
│   ├── ErrorBoundary.jsx     — Catches render errors, shows fallback UI
│   ├── MapView.jsx           — (existing, unchanged)
│   ├── RecommendationList.jsx — (existing, unchanged)
│   ├── CarparkCard.jsx       — (existing, unchanged)
│   ├── CarparkDetail.jsx     — (new, from US #3b)
│   └── AuthModal.jsx         — (existing, unchanged)
│
└── services/
    └── api.js                — (existing, unchanged)
```

## Implementation Notes

### ErrorBoundary

```jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-fallback">
          <h3>Something went wrong</h3>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false })}>
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

### Custom Hook Pattern (example)

```javascript
// hooks/useGeolocation.js
export function useGeolocation() {
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!navigator.geolocation) {
      setError("Geolocation not supported");
      setLoading(false);
      return;
    }
    const id = navigator.geolocation.watchPosition(
      (pos) => {
        setLocation([pos.coords.latitude, pos.coords.longitude]);
        setError(null);
        setLoading(false);
      },
      (err) => {
        setError("Location denied. Using default.");
        setLocation([1.3521, 103.8198]);
        setLoading(false);
      },
      { enableHighAccuracy: true, maximumAge: 60000, timeout: 10000 }
    );
    return () => navigator.geolocation.clearWatch(id);
  }, []);

  return { location, loading, error };
}
```

## Demo Flow

1. Developer opens `App.jsx` → sees ≤80 lines of clean orchestration
2. Changes GPS logic → only touches `useGeolocation.js`
3. Adds new feature → imports existing hooks instead of copying code
4. Map component crashes → ErrorBoundary catches it, sidebar still works
5. User sees "Something went wrong" with retry button instead of white screen
