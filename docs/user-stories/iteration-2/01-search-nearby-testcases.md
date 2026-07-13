---
layout: default
title: "US #1 Test Cases — Search Nearby Carparks"
parent: Iteration 2
---

# Test Cases: US #1 — Search Nearby Carparks

| Field | Detail |
|-------|--------|
| Story | [US #1 — Search Nearby Carparks](../iteration-1/01-search-nearby) |
| Persona | Tan Wei Ming (Daily Commuter) |
| Status | **Done** (Iteration 1) |
| Test Level | Integration (API endpoint), Unit (status logic) |

## Story Summary

> As a **driver approaching a destination**, I want to **see nearby HDB carparks with real-time availability** so that I can **drive directly to one with empty lots instead of circling**.

---

## Test Cases

### 1. Test for…

*…verifying that the recommendation endpoint returns nearby carparks ordered by distance for a valid GPS location.*

Start the ParkGuideSG backend server. Send a GET request to `/api/v1/recommend?lat=1.3521&lng=103.8198&n=5&radius_m=3000` with the database mock configured to return 5 carpark records within the search radius. Check that the response has HTTP status 200. Verify that the response body contains a `results` array with exactly 5 items. Confirm that each result has the fields `carpark_id`, `address`, `total_lots`, `available_lots`, `predicted_vacancy_rate`, `status`, `distance_m`, `weather`, `lat`, `lng`, and `trend`. Verify that the `distance_m` values are in ascending order (closest carpark first). Also check that the `query_time_ms` field is a positive number.

*This is a grey-box test. You need to know the API response schema defined in `backend/app/models/schemas.py` and that the geospatial query uses haversine distance ordering. The database is mocked at the connection-pool level via the `mock_db` fixture.*

**Verifying the full recommendation pipeline — GPS coordinates in, ordered carpark results out.**

---

### 2. Test for…

*…handling the case where no carparks exist within the search radius.*

Start the ParkGuideSG backend server. Configure the database mock (`mock_db` fixture) to return an empty list from the geospatial query (`cur.fetchall.return_value = []`). Send a GET request to `/api/v1/recommend?lat=1.3521&lng=103.8198&n=5&radius_m=100`. Check that the response has HTTP status 404. Verify that the response detail message includes the text "No carparks found" and mentions the search radius. Confirm that no unhandled exception is raised on the server side.

*This is a grey-box test. You need to know that the recommend router raises `HTTPException(status_code=404)` when the geospatial query returns an empty list.*

**Empty result set → clear 404 message, no crash.**

---

### 3. Test for…

*…input validation rejecting requests with missing or invalid query parameters.*

Start the ParkGuideSG backend server. Send a GET request to `/api/v1/recommend` with no query parameters at all. Check that the response has HTTP status 422 (Unprocessable Entity). Verify that the response detail indicates which fields are required (`lat` and `lng`). Repeat the test with `lat=91` (out of valid range -90 to 90) and confirm HTTP 422 is returned. Repeat with `n=0` (below minimum 1) and confirm HTTP 422 is returned. Repeat with `radius_m=50` (below minimum 100) and confirm HTTP 422 is returned.

*This is a black-box test. You only need to know the API endpoint URL and that FastAPI/Pydantic validates query parameters based on the `Query(...)` constraints defined in the route signature. No internal knowledge is required beyond the API contract.*

**Validation guards reject bad input before any database work happens.**

---

### 4. Test for…

*…the vacancy status classification returning the correct colour for boundary values.*

Import the `_status` function from `app.routers.recommend`. Call `_status(0.51)` and verify it returns the string `"GREEN"`. Call `_status(0.5)` and verify it returns `"YELLOW"` (the boundary: >0.5 is GREEN, 0.2-0.5 is YELLOW). Call `_status(0.21)` and verify it returns `"YELLOW"`. Call `_status(0.2)` and verify it returns `"RED"`. Call `_status(0.0)` and verify it returns `"RED"`. This ensures the three-tier colour coding (GREEN >50%, YELLOW 20-50%, RED <20%) works correctly at all boundary values.

*This is a white-box test. You need direct access to the function implementation and knowledge of the threshold values (0.5 and 0.2). No server, database, or network is involved — it is a pure unit test.*

**Colour thresholds: >0.5 Green, 0.2-0.5 Yellow, <0.2 Red — tested at every boundary.**
