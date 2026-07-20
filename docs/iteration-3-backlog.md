---
layout: default
title: Iteration 3 Backlog
parent: Documentation
---

# ParkGuideSG — Iteration 3 Backlog

> **Date**: 2026-07-20  
> **Velocity (from Iteration 2)**: 0.80 (80%)  
> **Team**: 3 members × 20 working days  
> **Planned capacity**: 16 ideal developer days  
> **Methodology**: TDD — Every story includes Given/When/Then test cases before implementation

---

## Story Map

| # | Story | Priority | Est. Days | Status | Assignee | Labels |
|---|-------|----------|-----------|--------|----------|--------|
| 14 | PWA Support (Service Worker + manifest) | 10 | 1 | `todo` | — | enhancement |
| 15 | CI/CD Test Automation (GitHub Actions) | 10 | 1 | `todo` | — | enhancement |
| 16 | Carpark Rate Information Display | 20 | 2 | `todo` | — | enhancement |
| 17 | Favourites Push Notification | 20 | 2 | `todo` | — | enhancement |
| 18 | Model A/B Testing Framework | 30 | 3 | `todo` | — | enhancement |
| 19 | EV Charging Station Data Integration | 30 | 3 | `todo` | — | enhancement |
| 20 | E2E Testing with Playwright/Cypress | 30 | 3 | `todo` | — | testing |
| 21 | ETL Pipeline Unit Tests | 40 | 1 | `todo` | — | testing |
| **Total** | | | **16** | | | |

---

## Status Legend

| Label | Meaning |
|-------|---------|
| `todo` | Not yet started |
| `in-progress` | Currently working on |
| `done` | Completed and verified |

---

## Iteration 3 Stories — Detailed

### US #14: PWA Support
**Priority**: 10 | **Est.** 1 day | **Status**: `todo`

> As a **mobile driver**, I want to **add ParkGuideSG to my phone's home screen** so that I can **launch it like a native app without opening the browser**.

**Key Tests**:
- Service Worker registers and caches app shell
- Manifest enables "Add to Home Screen"
- Offline fallback page displays when no network

**GitHub**: [#35 — Frontend refactor](https://github.com/LuoX11a/CP3407-Project/issues/35) (includes PWA scope)

---

### US #15: CI/CD Test Automation
**Priority**: 10 | **Est.** 1 day | **Status**: `todo`

> As a **developer**, I want **automated tests to run on every push and PR** so that **regressions are caught before merging**.

**Key Tests**:
- GitHub Actions workflow triggers on push to develop/main
- Backend pytest suite runs and reports results
- Frontend vitest suite runs and reports results
- Failed tests block PR merge

**Reference**: [test-strategy.md](test-strategy.md) §6.1 — Ready-to-use workflow YAML

---

### US #16: Carpark Rate Information
**Priority**: 20 | **Est.** 2 days | **Status**: `todo`

> As a **cost-conscious driver**, I want to **see parking rates for each carpark** so that I can **choose based on total cost, not just distance**.

**Key Tests**:
- API returns rate info per carpark (hourly, daily max, overnight)
- Frontend displays rate on carpark card and detail panel
- Sort by hourly rate works correctly
- Carparks with missing rate data show "Rate unavailable"

---

### US #17: Favourites Push Notification
**Priority**: 20 | **Est.** 2 days | **Status**: `todo`

> As a **regular driver**, I want to **get a notification when a favourite carpark has plenty of empty lots** so that I can **time my departure for the best parking availability**.

**Key Tests**:
- Notification triggers when vacancy > 70% at a favourited carpark
- User can enable/disable notifications per carpark
- Notification contains carpark name and available lot count
- Service Worker handles push events

---

### US #18: Model A/B Testing Framework
**Priority**: 30 | **Est.** 3 days | **Status**: `todo`

> As a **data scientist**, I want to **compare two model versions side-by-side in production** so that I can **confidently deploy model improvements**.

**Key Tests**:
- A/B split routes traffic to model A or B based on user ID hash
- Both model predictions logged for comparison
- Dashboard shows accuracy difference between A and B
- Rollback to 100% model A works instantly

**Reference**: [project-analysis-pm-perspective.md](project-analysis-pm-perspective.md) §2.3 — ML model gaps

---

### US #19: EV Charging Station Integration
**Priority**: 30 | **Est.** 3 days | **Status**: `todo`

> As an **EV driver**, I want to **see which carparks have charging stations** so that I can **park AND charge at the same time**.

**Key Tests**:
- API returns charging station count per carpark
- EV icon shown on carpark cards with chargers
- Filter to show only carparks with chargers
- Data sourced from LTA/URA open datasets

---

### US #20: E2E Testing (Playwright)
**Priority**: 30 | **Est.** 3 days | **Status**: `todo`

> As a **QA engineer**, I want **end-to-end tests that simulate real user flows** so that I can **verify the full stack works together**.

**Key Tests**:
- Full flow: Open app → GPS detected → recommendations load → select carpark → view detail → navigate
- Auth flow: Register → Login → Add favourite → Logout → Login → Favourite persists
- Search flow: Type address → Results appear → Click result → Map flies to location
- Error flow: API down → Error message → Retry → Success

**Reference**: [test-strategy.md](test-strategy.md) §1.1 — Test pyramid

---

### US #21: ETL Pipeline Unit Tests
**Priority**: 40 | **Est.** 1 day | **Status**: `todo`

> As a **data engineer**, I want **the ETL pipeline to have unit tests** so that **data quality issues are caught before they corrupt the database**.

**Key Tests**:
- `_haversine()` returns correct distance for known coordinates
- `_fetch_json()` handles HTTP errors, timeouts, and retries
- Data validation catches NULL weather_condition, negative available_lots
- Mocked Data.gov.sg API → verify correct INSERT statements

**Reference**: [test-strategy.md](test-strategy.md) §5.3

---

## Velocity Calculation

```
Iteration 1: 17/60 = 0.28 (28%)
Iteration 2: 16/20 = 0.80 (80%)
Iteration 3: 16/20 = 0.80 (estimated, based on Iteration 2)
```

| Metric | Iteration 1 | Iteration 2 | Iteration 3 (plan) |
|--------|-------------|-------------|-------------------|
| Stories planned | 5 | 8 | 8 |
| Total days | 17 | 16 | 16 |
| Velocity factor | 28% | 80% | 80% (target) |
| Test cases | 0 | 18 | 20+ (TDD) |

---

## Monitoring

Progress tracked via:
- **GitHub Issues** — [#31](https://github.com/LuoX11a/CP3407-Project/issues/31), [#34](https://github.com/LuoX11a/CP3407-Project/issues/34), [#35](https://github.com/LuoX11a/CP3407-Project/issues/35) + new issues for #14-#21
- **Labels**: `todo`, `in-progress`, `done`
- **This document** — updated at each standup
