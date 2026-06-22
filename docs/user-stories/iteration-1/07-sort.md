---
layout: default
title: "US #7 — Sort Carparks"
parent: Iteration 1
---

# User Story #7: Sort Carparks

| Field | Detail |
|-------|--------|
| Priority | 20 |
| Estimated Days | 1 |
| Status | **Done** |
| Persona | Both Tan Wei Ming & Siti Nurul |

## Story

> As a **driver viewing multiple carpark options**, I want to **sort the results by different criteria** (distance, available lots, vacancy rate) so that I can **quickly find the best option for my situation**.

## Acceptance Criteria

- [x] Sort dropdown appears above the recommendation list when results exist
- [x] Three sort options: Distance, Available Lots, Vacancy Rate
- [x] Sorting happens client-side with `useMemo` for performance
- [x] Default sort is by distance (closest first)
- [x] Sort selection preserved while results update

## Implementation

**File**: `frontend/src/components/RecommendationList.jsx`

### Sort Options

```javascript
const SORT_OPTIONS = [
  { key: "distance", label: "Distance" },
  { key: "available", label: "Available Lots" },
  { key: "vacancy", label: "Vacancy Rate" },
];
```

### Sort Logic

```javascript
const sorted = useMemo(() => {
  const list = [...results];
  switch (sortBy) {
    case "available":
      list.sort((a, b) => (b.available_lots || 0) - (a.available_lots || 0));
      break;
    case "vacancy":
      list.sort((a, b) => (b.predicted_vacancy_rate || 0) - (a.predicted_vacancy_rate || 0));
      break;
    default: // distance
      list.sort((a, b) => (a.distance_m || 0) - (b.distance_m || 0));
  }
  return list;
}, [results, sortBy]);
```

### UI

```jsx
{results.length > 0 && (
  <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
    <option value="distance">Sort by Distance</option>
    <option value="available">Sort by Available Lots</option>
    <option value="vacancy">Sort by Vacancy Rate</option>
  </select>
)}
```

## Demo Flow

1. Recommendations load → 5 carparks sorted by distance (default)
2. **Wei Ming** keeps the default "Distance" sort — commuter cares about closest walk
3. **Siti** switches to "Vacancy Rate" — weekend explorer wants guaranteed space
4. List re-renders instantly with highest vacancy at top
5. Switching to "Available Lots" → sorts by raw empty lot count

## Persona Usage

| Persona | Preferred Sort | Why |
|---------|---------------|-----|
| Tan Wei Ming (Commuter) | **Distance** | Wants the closest carpark to office. Has flexible hours so vacancy is secondary. |
| Siti Nurul (Weekend) | **Vacancy Rate** or **Available Lots** | Has kids in the car — needs guaranteed parking. Distance is secondary to certainty. |
