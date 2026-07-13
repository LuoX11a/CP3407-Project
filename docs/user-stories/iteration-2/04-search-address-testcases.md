---
layout: default
title: "US #4 Test Cases — Search by Address or Area"
parent: Iteration 2
---

# Test Cases: US #4 — Search by Address or Area

| Field | Detail |
|-------|--------|
| Story | [US #4 — Search by Address or Area](../iteration-1/04-search-address) |
| Persona | Siti Nurul (Weekend Explorer) |
| Status | **Done** (Iteration 1) |
| Test Level | Integration (API endpoint) |

## Story Summary

> As a **driver going to an unfamiliar area**, I want to **search carparks by typing an address or area name** so that I can **find parking options near my intended destination before I leave**.

---

## Test Cases

### 1. Test for…

*…searching for carparks by a valid area name returns matching results.*

Start the ParkGuideSG backend server. Configure the database mock to return two carpark records matching the query. Send a GET request to `/api/v1/carpark/search?q=Orchard&limit=10`. Check that the response has HTTP status 200. Verify the response body contains a `results` array with 2 items. Confirm each result has the fields `carpark_id`, `address`, `car_lots`, `lat`, `lng`, `available_lots`, and `vacancy_rate`. Verify that at least one result's `address` field contains the word "Orchard" (case-insensitive match). Also check that the search respects the `limit` parameter — if the mock is configured to return 5 rows but limit=3, only 3 results should appear.

*This is a grey-box test. You need to know the endpoint URL and the response schema (`SearchResponse` with `SearchResult` items). The database is mocked via `mock_db`; the SQL uses `ILIKE '%query%'` for fuzzy matching.*

**Typing "Orchard" in the search bar → relevant carparks returned with live availability.**

---

### 2. Test for…

*…searching with a query that matches no carparks returns an empty result set.*

Start the ParkGuideSG backend server. Configure the database mock to return an empty list (`cur.fetchall.return_value = []`). Send a GET request to `/api/v1/carpark/search?q=xyznonexistentplace&limit=20`. Check that the response has HTTP status 200 (not 404 — an empty search is a valid result, not an error). Verify the response body contains `{"results": []}`. Confirm no exception is raised.

*This is a black-box test. You only need to know the endpoint URL. The expected behaviour is an empty array, not an error, because "no results" is a normal search outcome — the frontend shows a "No carparks found" empty state rather than an error.*

**Typing gibberish → empty results, graceful empty state, no crash.**

---

### 3. Test for…

*…input validation requiring the search query parameter.*

Start the ParkGuideSG backend server. Send a GET request to `/api/v1/carpark/search` with no `q` parameter at all. Check that the response has HTTP status 422 (Unprocessable Entity). Verify the response detail indicates that `q` is a required field. Repeat the test with `q=` (empty value) and confirm HTTP 422 is also returned, since the query parameter has `min_length=1`. Also test with a query string longer than 200 characters — confirm HTTP 422 is returned, since `max_length=200`.

*This is a black-box test. You only need to know the API contract: the `q` parameter is required with `min_length=1` and `max_length=200`, enforced by FastAPI/Pydantic validation.*

**Empty search box submit → validation error before any database query.**
