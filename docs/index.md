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
| Related Stories | [#1 Search Nearby Carparks](user-stories/iteration-1/01-search-nearby.md), [#2 View Available Lots](user-stories/iteration-1/02-view-lots.md), [#5-6 View Carparks in List & Map](user-stories/iteration-2/05-view-carpark.md), [#7 Sort Carparks](user-stories/iteration-1/07-sort.md) |

Wei Ming opens ParkGuideSG each morning. GPS picks up his location on the expressway approaching CBD. Within seconds he sees the 5 nearest carparks ranked by distance, each with live availability counts and color-coded vacancy status. He chooses a GREEN-status carpark 300m from his office and drives straight there — no more circling.

---

### Persona 2: Siti Nurul — Weekend Explorer

| Attribute | Detail |
|-----------|--------|
| Age / Role | 29, Freelance Designer, mother of two |
| Driving Pattern | Drives family to different malls, parks, and attractions every weekend |
| Pain Point | Unfamiliar with parking situation at destinations. Arrives to find full carparks — stressful with young children in the car. |
| Goal | Search carparks by area name before leaving, check details and vacancy rates, pick the one with most empty lots. Save favourites for regularly visited places. |
| Related Stories | [#3 View Carpark Details](user-stories/iteration-1/03-carpark-detail.md), [#4 Search by Area](user-stories/iteration-1/04-search-address.md), [#7 Sort Carparks](user-stories/iteration-1/07-sort.md), [#8-10 User Account & Favourites](user-stories/iteration-2/08-user-account.md) |

Before heading to Orchard Road on Saturday, Siti types "Orchard" into the search bar. She sees all carparks in the area with available lots. She sorts by vacancy rate, opens the top result to check total lot count and 3-hour availability forecast, then sets it as her destination. She saves her favourite carparks so next weekend they're one click away. The family arrives knowing exactly where to park.

---

## Velocity Tracking

> **公式**: `Max Work = Team Members × Working Days × Velocity`

### Iteration 1（基准）

| Metric | Value |
|--------|-------|
| Team members | 3 |
| Working days | 20 |
| Velocity | **0.5** |
| Max work capacity | 3 × 20 × 0.5 = **30 天** |
| Story days planned | 17 天 |
| Story days completed | 17 天 ✅ |

### Iteration 2（使用 Iteration 1 的 Velocity = 0.5）

| Metric | Value |
|--------|-------|
| Team members | 3 |
| Working days | **6** |
| Velocity（来自 Iteration 1） | **0.5** |
| Max work capacity | 3 × 6 × 0.5 = **9 天** |
| Story days planned | 16 天 |
| Story days completed | **10 天** ✅ |
| Story days remaining | **6 天** 📋 |

> ⚠️ 计划 16 天超过产能 9 天，实际以 LuoX11a 单人投入为准。

### Iteration 3（预测，Velocity = 0.5）

| Metric | Value |
|--------|-------|
| Team members | 3 |
| Working days | 6 |
| Max work capacity | 3 × 6 × 0.5 = **9 天** |
| Story days planned | **6 天** 📋 |

---

## Iteration 1 — Completed User Stories

| # | Story | Priority | Days | Status |
|---|-------|----------|------|--------|
| 1 | [Search Nearby Carparks](user-stories/iteration-1/01-search-nearby.md) | 10 | 5 | ✅ Done |
| 2 | [View Available Lots](user-stories/iteration-1/02-view-lots.md) | 10 | 5 | ✅ Done |
| 3 | [View Carpark Details](user-stories/iteration-1/03-carpark-detail.md) | 10 | 5 | ✅ Done |
| 4 | [Search by Area or Address](user-stories/iteration-1/04-search-address.md) | 20 | 1 | ✅ Done |
| 7 | [Sort Carparks](user-stories/iteration-1/07-sort.md) | 20 | 1 | ✅ Done |

**Iteration 1 Summary**: 5/5 stories completed (100%). Core carpark search and display features delivered.

---

## Iteration 2 — User Stories (16 days)

| # | Story | Priority | Days | Status |
|---|-------|----------|------|--------|
| 5-6 | [View Carparks in List & Map](user-stories/iteration-2/05-view-carpark.md) | 10 | 5 | ✅ Done |
| 8-10 | [User Account & Favourites](user-stories/iteration-2/08-user-account.md) | 40 | 5 | ✅ Done |
| 3b | [Carpark Detail Panel](user-stories/iteration-2/03b-carpark-detail.md) | 20 | 3 | 📋 Todo |
| 15 | [Frontend Architecture Refactor](user-stories/iteration-2/15-frontend-refactor.md) | 30 | 3 | 📋 Todo |

**Iteration 2 Summary**: 2/4 stories completed, 2 todo. 已完成 10 天，剩余 6 天，合计 16 天。

### Iteration 2 Story Map

```
Done ✅                    Todo 📋
┌────────────────────┐    ┌──────────────────────┐
│ #5-6 View List &   │    │ #3b Carpark Detail   │
│     Map (4d)       │    │     Panel (5d)        │
├────────────────────┤    │ 24h history chart,   │
│ #8-10 User Account │    │ motorcycle lots,      │
│     & Favourites   │    │ detail modal          │
│     (3d)           │    ├──────────────────────┤
└────────────────────┘    │ #15 Frontend Refactor │
                          │     (4d)              │
                          │ hooks拆分, ErrorBoundary│
                          └──────────────────────┘
```

---

## Iteration 3 — Planned (Backlog)

| # | Story | Priority | Days | Status |
|---|-------|----------|------|--------|
| 12 | Mobile-Friendly Website | 50 | 3 | 📋 Todo |
| 13 | View Search History | 50 | 1 | 📋 Todo |
| 14 | Admin View Records | 50 | 2 | 📋 Todo |

**Iteration 3 Budget**: 3 人 × 6 天 × 0.5 = **9 天有效产能**，计划 6 天，产能充足。

---

## Completed vs. Unfinished Summary

### Completed (Iteration 1 + 2)

| Iteration | Stories | Completed | Completion Rate |
|-----------|---------|-----------|-----------------|
| Iteration 1 | 5 stories (17 days) | 5/5 | 100% |
| Iteration 2 | 4 stories (16 days) | 2/4 (10 days) | 50% |
| **Total** | **9 stories (33 days)** | **7/9 (27 days)** | **82%** |

### Unfinished / Remaining

| Iteration | Stories | Planned Days |
|-----------|---------|---------------|
| Iteration 2 | 2 stories (#3b, #15) | 9 days |
| Iteration 3 | 3 stories (12, 13, 14) | 6 days |

---

## Project Board

> **GitHub Projects**: Track progress at [github.com/LuoX11a/CP3407-Project](https://github.com/LuoX11a/CP3407-Project)

### Story Status Labels

| Label | Meaning |
|-------|---------|
| `todo` | Not yet started |
| `in-progress` | Currently being developed |
| `done` | Completed and verified |
