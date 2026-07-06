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
| Related Stories | [#1 Search Nearby Carparks](user-stories/iteration-1/01-search-nearby.md), [#2 View Available Lots](user-stories/iteration-1/02-view-lots.md), [#5 View Carparks in List](user-stories/iteration-2/05-view-list.md), [#6 View Carparks on Map](user-stories/iteration-2/06-view-map.md), [#7 Sort Carparks](user-stories/iteration-1/07-sort.md), [#11 Recommend Best Carpark](user-stories/iteration-2/11-recommend-best.md) |

Wei Ming opens ParkGuideSG each morning. GPS picks up his location on the expressway approaching CBD. Within seconds he sees the 5 nearest carparks ranked by distance, each with live availability counts and color-coded vacancy status. He chooses a GREEN-status carpark 300m from his office and drives straight there — no more circling.

---

### Persona 2: Siti Nurul — Weekend Explorer

| Attribute | Detail |
|-----------|--------|
| Age / Role | 29, Freelance Designer, mother of two |
| Driving Pattern | Drives family to different malls, parks, and attractions every weekend |
| Pain Point | Unfamiliar with parking situation at destinations. Arrives to find full carparks — stressful with young children in the car. |
| Goal | Search carparks by area name before leaving, check details and vacancy rates, pick the one with most empty lots. Save favourites for regularly visited places. |
| Related Stories | [#3 View Carpark Details](user-stories/iteration-1/03-carpark-detail.md), [#4 Search by Area](user-stories/iteration-1/04-search-address.md), [#7 Sort Carparks](user-stories/iteration-1/07-sort.md), [#8 Save Favourites](user-stories/iteration-2/08-save-favourites.md), [#9 Register Account](user-stories/iteration-2/09-register-account.md), [#10 Login Account](user-stories/iteration-2/10-login-account.md) |

Before heading to Orchard Road on Saturday, Siti types "Orchard" into the search bar. She sees all carparks in the area with available lots. She sorts by vacancy rate, opens the top result to check total lot count and 3-hour availability forecast, then sets it as her destination. She saves her favourite carparks so next weekend they're one click away. The family arrives knowing exactly where to park.

---

## Velocity Tracking

> **公式**（来自 Group 4 文档）：
>
> ```
> Max Work per Iteration = Team Members × Working Days × Velocity
> ```
>
> 验证 Iteration 1：3 人 × 20 天 × 0.5 = **30 天**（团队总产能）

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
| Story days planned | 10 天 |
| Story days completed | 10 天 ✅ |

> **Backlog 分析**：Iteration 2 产能 **9 天**，计划 **10 天**，基本匹配（超出仅 1 天）。
> 所有故事标记为 Done，功能已全部实现。

### Iteration 3（预测，Velocity = 0.5）

| Metric | Value |
|--------|-------|
| Team members | 3 |
| Working days | 6 |
| Max work capacity | 3 × 6 × 0.5 = **9 天** |
| Story days planned | 6 天 |

> Iteration 3 产能 9 天，计划 6 天，绰绰有余。

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

## Iteration 2 — Completed User Stories

| # | Story | Priority | Days | Status |
|---|-------|----------|------|--------|
| 5 | [View Carparks in List](user-stories/iteration-2/05-view-list.md) | 10 | 3 | ✅ Done |
| 6 | [View Carparks on Map](user-stories/iteration-2/06-view-map.md) | 20 | 1 | ✅ Done |
| 11 | [Recommend Best Carpark](user-stories/iteration-2/11-recommend-best.md) | 30 | 3 | ✅ Done |
| 8 | [Save Favourite Carparks](user-stories/iteration-2/08-save-favourites.md) | 40 | 1 | ✅ Done |
| 9 | [Register Account](user-stories/iteration-2/09-register-account.md) | 40 | 1 | ✅ Done |
| 10 | [Login Account](user-stories/iteration-2/10-login-account.md) | 40 | 1 | ✅ Done |

**Iteration 2 Summary**: 6/6 stories completed (100%). Recommendation engine, user accounts, and favourites delivered.

### Iteration 2 Story Map

```
Priority 10 (High)     Priority 20          Priority 30          Priority 40
┌──────────────────┐   ┌──────────────┐    ┌────────────────┐    ┌──────────────────┐
│ #5 View List     │   │ #6 View Map  │    │ #11 Recommend  │    │ #8 Favourites    │
│ (3 days) ✅      │   │ (1 day) ✅   │    │ (3 days) ✅    │    │ (1 day) ✅       │
└──────────────────┘   └──────────────┘    └────────────────┘    ├──────────────────┤
                                                                  │ #9 Register      │
                                                                  │ (1 day) ✅       │
                                                                  ├──────────────────┤
                                                                  │ #10 Login        │
                                                                  │ (1 day) ✅       │
                                                                  └──────────────────┘
```

---

## Iteration 3 — Planned (Backlog)

| # | Story | Priority | Days | Status |
|---|-------|----------|------|--------|
| 12 | Mobile-Friendly Website | 50 | 3 | 📋 Todo |
| 13 | View Search History | 50 | 1 | 📋 Todo |
| 14 | Admin View Records | 50 | 2 | 📋 Todo |

**Iteration 3 Budget**: 3 人 × 6 天 × 0.5 velocity = **9 天有效产能**，计划工作量 6 天，产能充足。

---

## Completed vs. Unfinished Summary

### Completed (Iteration 1 + 2)

| Iteration | Stories | Completed | Completion Rate |
|-----------|---------|-----------|-----------------|
| Iteration 1 | 5 stories (17 days) | 5/5 | 100% |
| Iteration 2 | 6 stories (10 days) | 6/6 | 100% |
| **Total** | **11 stories (27 days)** | **11/11** | **100%** |

### Unfinished / Remaining

| Iteration | Stories | Planned Days |
|-----------|---------|---------------|
| Iteration 3 | 3 stories (12, 13, 14) | 6 days |

### Features Delivered

| Feature Area | Stories | Implementation |
|-------------|--------|----------------|
| GPS Location | #1 | `navigator.geolocation.watchPosition` |
| Nearby Search | #1, #11 | Haversine query + ML ranking |
| Live Availability | #2, #3 | PostgreSQL view + availability logs |
| Map Visualization | #6 | Leaflet + OpenStreetMap, color-coded markers |
| List View | #5 | Card list with trend charts, sort options |
| Address Search | #4 | ILIKE fuzzy text matching |
| Sort & Filter | #7 | Client-side sort by distance/lots/vacancy |
| ML Recommendation | #11 | Random Forest model with feature engineering |
| User Accounts | #9, #10 | JWT auth, bcrypt passwords, register/login |
| Favourites | #8 | CRUD with live availability, star toggle |
| Trend Forecast | #2, #11 | 3-hour predicted availability chart |
| Error Handling | All | Loading, empty, error states with retry |

---

## Project Board

> **GitHub Projects**: Track progress at [github.com/LuoX11a/CP3407-Project](https://github.com/LuoX11a/CP3407-Project)

### Story Status Labels

| Label | Meaning |
|-------|---------|
| `todo` | Not yet started |
| `in-progress` | Currently being developed |
| `done` | Completed and verified |
