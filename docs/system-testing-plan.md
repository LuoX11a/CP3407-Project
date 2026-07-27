---
layout: default
title: System Testing Plan
parent: Documentation
---

# ParkGuideSG — System Testing Plan

> **Version**: 1.0  
> **Date**: 2026-07-27  
> **Purpose**: Week 10 live demonstration and system validation  
> **Team**: LuoX11a, Vince-1206, LauTszTsun

---

## 1. Objectives

Validate that ParkGuideSG meets its core promise: **a driver opens the app, sees nearby carpark availability in real time, and navigates to the best option — all within seconds.**

| Objective | Success Criteria |
|-----------|-----------------|
| GPS location detection | App acquires user location within 5 seconds of opening |
| Nearby carpark search | Returns 5+ carparks within 3 km radius in under 200 ms |
| ML predictions | Predicted vacancy rate within ±10% of actual (MAE ≤ 0.10) |
| Map interaction | Markers render with correct color coding (green/yellow/red) |
| Address search | User can search "Orchard" and see relevant carparks |
| Authentication | Register → Login → Add favourite → Logout → Login → favourite persists |
| PWA installation | App can be added to home screen; offline fallback shows cached page |
| Navigation | One-tap opens Google Maps / Apple Maps with correct destination |
| Cross-browser | Works on Chrome, Firefox, and mobile (Pixel 5 viewport) |

---

## 2. Test Environment

| Component | Configuration |
|-----------|--------------|
| **Backend** | FastAPI on `localhost:8000` (or Render cloud instance) |
| **Database** | Neon PostgreSQL — `ep-crimson-bread-ao6pswy8-pooler` |
| **Frontend** | Vite dev server on `localhost:5173` |
| **Browser** | Chrome 120+, Firefox 120+, Pixel 5 (Playwright / real device) |
| **Network** | WiFi or 4G; throttled to 3G for mobile test |
| **Test data** | Live Data.gov.sg API + backfilled 607K-row training dataset |

### Startup Commands

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npx vite --port 5173
```

Open `http://localhost:5173` in the browser.

---

## 3. Test Scenarios

### 3.1 Scenario Mapping to User Stories

| Scenario | User Story | Persona | Type |
|----------|-----------|---------|------|
| S1 — GPS Nearby Search | US#1 Search Nearby Carparks | Tan Wei Ming | Functional |
| S2 — Address Search | US#4 Search by Area | Siti Nurul | Functional |
| S3 — Map & List Views | US#5-6 View List & Map | Tan Wei Ming | Functional |
| S4 — Carpark Detail Panel | US#3b Carpark Detail | Siti Nurul | Functional |
| S5 — Authentication & Favourites | US#8-10 User Account | Both | Functional |
| S6 — One-Tap Navigation | US#8 Navigation | Tan Wei Ming | Functional |
| S7 — PWA Offline | US#14 PWA Support | Both | Non-functional |
| S8 — Cross-Browser | — | Both | Compatibility |
| S9 — Error Handling | — | Both | Robustness |
| S10 — Performance | — | Tan Wei Ming | Non-functional |

---

### S1 — GPS Nearby Search

**Setup**: Open ParkGuideSG, grant location permission.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | Open `http://localhost:5173` | Map renders with Leaflet tiles |
| 1.2 | Browser prompts for location | Click Allow |
| 1.3 | GPS coordinates acquired | Header shows "GPS: 1.XXXX, 103.XXXX" |
| 1.4 | API call completes | Sidebar shows 5 carpark cards |
| 1.5 | Each card shows carpark ID, available lots, vacancy %, distance | Values present and non-negative |
| 1.6 | Cards sorted by composite score | Top card has highest score |
| 1.7 | Map shows markers at carpark locations | Markers color-coded (green/yellow/red) |

**Pass**: All steps complete within 5 seconds of location grant.

---

### S2 — Address Search

**Setup**: App loaded and location granted.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | Type "Orchard" into search bar and press Enter | Loading indicator appears |
| 2.2 | Results appear in sidebar | Section titled "Search Results" |
| 2.3 | Click a search result | Map flies to that carpark location |
| 2.4 | Search for "Jurong East" | Different set of carparks appears |
| 2.5 | Search for empty string "  " | No error; previous results remain |

**Pass**: At least 1 valid carpark returned per search with address containing the query.

---

### S3 — Map & List Views

**Setup**: Results loaded from S1.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | Click a carpark card in the sidebar | Card highlights (selected class), map marker pops up |
| 3.2 | Click a map marker | Corresponding card highlights in sidebar |
| 3.3 | Pan/zoom the map | Map tiles load smoothly, markers reposition |
| 3.4 | Verify marker colors | Green (vacancy > 50%), Yellow (20-50%), Red (< 20%) |

**Pass**: Bidirectional selection between map and list; markers have correct colors.

---

### S4 — Carpark Detail Panel

**Setup**: Select a carpark from S1 results.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | Click carpark card | Detail panel shows: address, total lots, motorcycle lots |
| 4.2 | Check availability data | Latest available lots and vacancy rate displayed |
| 4.3 | Check trend chart | 3-hour forecast chart visible with data points |
| 4.4 | Check weather display | Current weather condition shown |
| 4.5 | Check rate info | Hourly rate displayed (e.g. "$0.80/hr" or "$1.20/hr") |
| 4.6 | Check EV indicator | EV badge shown if carpark has charging stations |

**Pass**: All fields present and non-null for a valid carpark.

---

### S5 — Authentication & Favourites

**Setup**: App loaded.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | Click "Login" button | Auth modal appears with Register/Login tabs |
| 5.2 | Register: username="testuser99", email="test@test.com", password="Test1234" | Toast: "Registered successfully" |
| 5.3 | Login: username="testuser99", password="Test1234" | Modal closes, header shows username and Logout button |
| 5.4 | Click star icon on a carpark card | Star fills yellow (favourited) |
| 5.5 | Click star again | Star unfills (unfavourited) |
| 5.6 | Favourite another carpark, then Logout | Returns to logged-out state |
| 5.7 | Login again with same credentials | Previously favourited carparks appear with filled stars |

**Pass**: Favourites persist across login sessions.

---

### S6 — One-Tap Navigation

**Setup**: A carpark is selected from results.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | Click the navigation button on a carpark card | New tab opens with Google Maps directions |
| 6.2 | Verify URL format | `https://www.google.com/maps/dir/?api=1&destination=<lat>,<lng>` |
| 6.3 | Test on iPhone (simulated) | URL uses `maps.apple.com` for iOS |

**Pass**: Correct deep-link URL generated for each platform.

---

### S7 — PWA Offline

**Setup**: App loaded at least once (SW installed).

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | Open DevTools → Application → Manifest | Manifest detected with name "ParkGuideSG" |
| 7.2 | Check "Add to Home Screen" prompt | Browser shows install prompt |
| 7.3 | DevTools → Network → Offline | Checkbox: enable offline mode |
| 7.4 | Reload page | App shell loads from cache (not blank white page) |
| 7.5 | Go back online | Live data resumes loading |

**Pass**: Offline cached page renders; online data resumes after reconnection.

---

### S8 — Cross-Browser

**Setup**: Repeat S1 in each browser.

| Browser | Viewport | Pass Criteria |
|---------|----------|---------------|
| Chrome 120+ | 1920×1080 | Map, cards, search all functional |
| Firefox 120+ | 1920×1080 | Same as Chrome |
| Mobile (Pixel 5) | 393×851 | Responsive layout; touch-friendly tap targets |

**Pass**: All three environments show functional map and recommendation list.

---

### S9 — Error Handling

**Setup**: Simulate failure conditions.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | Stop backend server, reload frontend | Error message displayed ("Service unavailable" or similar) |
| 9.2 | Restart backend, click Retry | Data loads normally |
| 9.3 | Deny location permission | Shows "Location unavailable" with manual search option |
| 9.4 | Search for non-existent address "xyzzy123" | "No carparks found" message, no crash |

**Pass**: No uncaught exceptions or white screens; graceful degradation.

---

### S10 — Performance

**Setup**: Normal operation (S1).

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Time to first carpark card | < 2 seconds | Performance API / stopwatch |
| API response time (/recommend) | < 200 ms | `query_time_ms` in response JSON |
| Map render time | < 1 second | Stopwatch from page load to tile visibility |
| Location acquisition | < 5 seconds | Browser geolocation timeout |
| PWA install size | < 1 MB | DevTools → Application → Cache Storage |

**Pass**: All metrics within targets on WiFi.

---

## 4. Bug Tracking Procedure

Bugs discovered during system testing are tracked using **GitHub Issues** with the following workflow:

### 4.1 Bug Report Template

When filing a bug, use the following structure:

```
**Title**: [BUG] <brief one-line description>

**Severity**: Critical / Major / Minor / Cosmetic

**Environment**:
- Browser: Chrome 125 / Firefox 126 / Safari
- OS: Windows / macOS / iOS / Android
- Backend: localhost / Render cloud

**Steps to Reproduce**:
1. Go to ...
2. Click on ...
3. Observe ...

**Expected Behavior**:
<what should happen>

**Actual Behavior**:
<what actually happens, with screenshots if applicable>

**Related User Story**: US#X — <story title>
```

### 4.2 Severity Classification

| Label | Criteria | Example |
|-------|----------|---------|
| `bug-critical` | App crashes, data loss, security breach | Login exposes password in URL |
| `bug-major` | Core feature broken, no workaround | Map fails to load carparks |
| `bug-minor` | Feature works but is degraded | Sort order incorrect for edge case |
| `bug-cosmetic` | Visual glitch, typo | Misaligned button on mobile |

### 4.3 Issue Labels

| Label | Color | Purpose |
|-------|-------|---------|
| `bug` | `#d73a4a` | All bug reports |
| `bug-critical` | `#b60205` | Critical severity |
| `bug-major` | `#ee0701` | Major severity |
| `bug-minor` | `#f9d0c4` | Minor severity |
| `bug-cosmetic` | `#fef2c0` | Cosmetic issues |

### 4.4 Workflow

```
System Test → Bug Found → Create GitHub Issue with [BUG] prefix
    → Assign severity label → Reproduce → Fix → PR → Close
```

All bugs must be traceable to a specific user story and test scenario from this plan.

---

## 5. Week 10 Demo Script

**Duration**: 10 minutes

| Time | Action | Scenario | Speaker |
|------|--------|----------|---------|
| 0:00–0:30 | Introduction: what ParkGuideSG does | — | Any |
| 0:30–1:30 | Open app → GPS detects location → 5 carparks appear on map | S1 | Member 1 |
| 1:30–2:30 | Show composite scoring: top pick has best overall score. Click card → detail panel with rate, EV, trend chart. Click navigate → Google Maps opens. | S1, S4, S6 | Member 1 |
| 2:30–3:30 | Search "Orchard" → results appear → click result → map flies to location | S2 | Member 2 |
| 3:30–5:00 | Register account → Login → Favourite 2 carparks → Logout → Login → favourites persist | S5 | Member 2 |
| 5:00–6:00 | Open DevTools → show PWA manifest → enable offline → reload → cached page loads | S7 | Member 3 |
| 6:00–7:00 | Show mobile view (Pixel 5) → responsive layout → touch targets work | S8 | Member 3 |
| 7:00–8:00 | Backend down → frontend shows error → restart backend → retry → recovers | S9 | Member 3 |
| 8:00–9:00 | Show performance metrics: API response time, model R², test coverage | S10 | Member 1 |
| 9:00–10:00 | Q&A | — | All |

---

## 6. Test Data

### 6.1 Live Data (via API)

- **Carpark availability**: Data.gov.sg `carpark-availability` endpoint — ~1,998 carparks per cycle
- **Weather**: NEA 2-hour forecast + air temperature, humidity, rainfall

### 6.2 Historical Data (database)

| Table | Rows | Coverage |
|-------|------|----------|
| `carparks` | 2,276 | All HDB carparks |
| `availability_logs` | 603,486 | May 29 – July 27, 2026 |
| `weather_records` | 27,213 | NEA 47 stations |
| `ml_predictions` | 53,558 | 1,997 carparks |

### 6.3 Test User Accounts

| Username | Password | Role |
|----------|----------|------|
| `demouser1` | `Test1234` | Pre-registered with 2 favourites |
| `testuser99` | `Test1234` | Register during demo (S5) |

---

## 7. Test Execution Record

Use this table during the Week 10 demo to record actual results.

| Scenario | Pass/Fail | Notes | Tester |
|----------|-----------|-------|--------|
| S1 — GPS Nearby Search | | | |
| S2 — Address Search | | | |
| S3 — Map & List Views | | | |
| S4 — Carpark Detail | | | |
| S5 — Auth & Favourites | | | |
| S6 — Navigation | | | |
| S7 — PWA Offline | | | |
| S8 — Cross-Browser | | | |
| S9 — Error Handling | | | |
| S10 — Performance | | | |

---

## Appendix A: Automated Test Suite Reference

| Layer | Tool | Tests | Command |
|-------|------|-------|---------|
| Backend unit/integration | pytest | 60 tests | `cd backend && python -m pytest tests/ -v` |
| Frontend unit/component | vitest | 9 tests | `cd frontend && npx vitest run` |
| E2E | Playwright | 4 specs | `cd e2e && npx playwright test` |
| CI | GitHub Actions | Auto on push | `.github/workflows/test.yml` |

## Appendix B: Bug Tracking Quick Reference

```bash
# Create a bug report
gh issue create --repo LuoX11a/CP3407-Project \
  --title "[BUG] <description>" \
  --label "bug" \
  --body "**Severity**: ..."
```
