---
layout: default
title: ParkGuideSG
description: Real-time HDB carpark recommendations for Singapore drivers
---

# ParkGuideSG

Real-time parking recommendation system for Singapore HDB carparks.

## User Personas

### Persona 1: Tan Wei Ming — Daily Commuter

| Attribute | Detail |
|-----------|--------|
| Age / Role | 34, Financial Analyst at Raffles Place |
| Driving Pattern | Drives to CBD every workday, arrives 8:30–9:00 AM |
| Pain Point | Spends 15–20 minutes circling carparks near office during peak hours. Often ends up parking 10+ minutes walk away. |
| Goal | See nearby carpark availability in real time before leaving home, sorted by distance. |
| Related Stories | [#1 Search Nearby Carparks](user-stories/iteration-1/01-search-nearby.md), [#2 View Available Lots](user-stories/iteration-1/02-view-lots.md), [#7 Sort Carparks](user-stories/iteration-1/07-sort.md) |

Wei Ming opens ParkGuideSG each morning. GPS picks up his location on the expressway approaching CBD. Within seconds he sees the 5 nearest carparks ranked by distance, each with live availability counts and color-coded vacancy status. He chooses a GREEN-status carpark 300m from his office and drives straight there — no more circling.

---

### Persona 2: Siti Nurul — Weekend Explorer

| Attribute | Detail |
|-----------|--------|
| Age / Role | 29, Freelance Designer, mother of two |
| Driving Pattern | Drives family to different malls, parks, and attractions every weekend |
| Pain Point | Unfamiliar with parking situation at destinations. Arrives to find full carparks — stressful with young children in the car. |
| Goal | Search carparks by area name before leaving, check details and vacancy rates, pick the one with most empty lots. |
| Related Stories | [#3 View Carpark Details](user-stories/iteration-1/03-carpark-detail.md), [#4 Search by Area](user-stories/iteration-1/04-search-address.md), [#7 Sort Carparks](user-stories/iteration-1/07-sort.md) |

Before heading to Orchard Road on Saturday, Siti types "Orchard" into the search bar. She sees all carparks in the area with available lots. She sorts by vacancy rate, opens the top result to check total lot count and 3-hour availability forecast, then sets it as her destination. The family arrives knowing exactly where to park.

---

## Iteration 1 — Completed User Stories

| # | Story | Priority | Days | Status |
|---|-------|----------|------|--------|
| 1 | [Search Nearby Carparks](user-stories/iteration-1/01-search-nearby.md) | 10 | 5 | Done |
| 2 | [View Available Lots](user-stories/iteration-1/02-view-lots.md) | 10 | 5 | Done |
| 3 | [View Carpark Details](user-stories/iteration-1/03-carpark-detail.md) | 10 | 5 | Done |
| 4 | [Search by Area or Address](user-stories/iteration-1/04-search-address.md) | 20 | 1 | Done |
| 7 | [Sort Carparks](user-stories/iteration-1/07-sort.md) | 20 | 1 | Done |

**Iteration 1 Velocity**:

- Team members: **3**
- Working days: **20**
- Completed work: **17 days**
- Total team capacity: 3 × 20 = **60 person-days**
- Actual velocity factor: 17 ÷ 60 = **0.28 (28%)**
- Planned velocity factor: **0.5 (50%)**

---

## Iteration 2 — Completed User Stories

| # | Story | Priority | Days | Status |
|---|-------|----------|------|--------|
| 6 | [View Carparks in List](user-stories/iteration-2/06-view-list) | 10 | 3 | Done |
| 7 | [View Carparks on Map](user-stories/iteration-2/07-view-map) | 20 | 1 | Done |
| 8 | [Recommend Best Carpark](user-stories/iteration-2/08-recommend-best) | 30 | 3 | Done |
| 9 | [Save Favourite Carparks](user-stories/iteration-2/09-save-favourites) | 40 | 1 | Done |
| 10 | [Register Account](user-stories/iteration-2/10-register-account) | 40 | 1 | Done |
| 11 | [Login Account](user-stories/iteration-2/11-login-account) | 40 | 1 | Done |
| 12 | [Carpark Detail Panel](user-stories/iteration-2/12-carpark-detail-panel) | 40 | 3 | Done |
| 13 | [Frontend Architecture Refactor](user-stories/iteration-2/13-frontend-refactor) | 40 | 3 | Done |

**Iteration 2 Velocity**:

- Team members: **3**
- Working days: **20**
- Completed work: **16 days**
- Maximum work per iteration: **16 days** (planned)
- Actual velocity factor: 16 ÷ 20 = **0.80 (80%)**
- Improvement from Iteration 1: 28% → 80% (+52%)

> **Note**: Velocity calculation methodology differs from Iteration 1. Iteration 2 uses *ideal developer days* (single-threaded) rather than *person-day capacity* (3×20=60), reflecting the textbook approach of measuring velocity against planned work rather than total team capacity.
