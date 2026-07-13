---
layout: default
title: "US #6 — Manage Favourite Carparks"
parent: Iteration 2
---

# User Story #6: Manage Favourite Carparks

| Field | Detail |
|-------|--------|
| Priority | 15 |
| Estimated Days | 2 |
| Status | **Done** (Iteration 2) |
| Persona | Siti Nurul (Weekend Explorer) & Tan Wei Ming (Daily Commuter) |

## Story

> As a **regular driver**, I want to **save carparks to my favourites and manage them** so that I can **quickly access my go-to parking spots without searching every time**.

## Acceptance Criteria

- [x] Authenticated users can view their favourites list
- [x] Users can add a carpark to favourites by carpark ID
- [x] Users can remove a carpark from favourites
- [x] Adding a non-existent carpark returns 404
- [x] Unauthenticated requests return 401
- [x] Favourites include live availability and weather data

## Implementation

**Endpoints**:
- `GET /api/v1/favourites` — List user's favourites (requires auth)
- `POST /api/v1/favourites/{carpark_id}` — Add to favourites (requires auth)
- `DELETE /api/v1/favourites/{carpark_id}` — Remove from favourites (requires auth)

**File**: `backend/app/routers/favourites.py`

**Auth**: JWT httpOnly cookie (primary) with Bearer header fallback via `get_current_user()` dependency.

---

## Test Cases

### 1. Test for…

*…listing favourites for a newly registered user who has not saved any carparks yet.*

Start the ParkGuideSG backend server. Create a valid JWT token for a test user (user_id=1, username="newuser") using `create_token()`. Send a GET request to `/api/v1/favourites` with the cookie header `token=<jwt_value>`. Configure the database mock to return an empty list for the favourites join query. Check that the response has HTTP status 200. Verify the response body is `{"favourites": []}`. Confirm that no INSERT or DELETE side effects occurred — only the SELECT query was executed.

*This is a grey-box test. You need to know the JWT token format and that the endpoint reads the user identity from the httpOnly cookie. The database is mocked, so you control the query result.*

**New user opens favourites tab → sees an empty list, not an error.**

---

### 2. Test for…

*…adding an existing carpark to favourites.*

Start the ParkGuideSG backend server. Generate a valid JWT for user_id=1. Configure the database mock so that the first query (checking the carpark exists in the `carparks` table) returns `[1]` (meaning the carpark exists), and the second query (INSERT INTO favourites) does not need a return value. Send a POST request to `/api/v1/favourites/ACM` with the auth cookie. Check that the response has HTTP status 200. Verify the response body is `{"status": "ok"}`. Confirm that both the existence check (SELECT 1 FROM carparks) and the INSERT were executed.

*This is a grey-box test. You need to know that the endpoint first checks the carpark table before inserting into favourites, and that `ON CONFLICT DO NOTHING` handles duplicates idempotently.*

**Tapping the star icon on a carpark → saved to favourites, star turns filled.**

---

### 3. Test for…

*…trying to add a carpark that does not exist in the database.*

Start the ParkGuideSG backend server. Generate a valid JWT for user_id=1. Configure the database mock so that the carpark existence check (`SELECT 1 FROM carparks`) returns `None` — meaning no such carpark. Send a POST request to `/api/v1/favourites/FAKE123` with the auth cookie. Check that the response has HTTP status 404. Verify the response detail message contains "Carpark not found". Confirm that the INSERT INTO favourites query was never executed (since the existence check failed first).

*This is a grey-box test. You need to know the endpoint's validation logic: it checks the carparks table before inserting. This prevents orphaned favourites records.*

**Trying to favourite a non-existent carpark ID → 404, no orphaned data.**

---

### 4. Test for…

*…accessing the favourites endpoint without authentication.*

Start the ParkGuideSG backend server. Do NOT include any auth cookie or Bearer header. Send a GET request to `/api/v1/favourites`. Check that the response has HTTP status 401 (Unauthorized). Verify the response detail message is "Authentication required". Repeat for POST `/api/v1/favourites/ACM` and DELETE `/api/v1/favourites/ACM` — both should also return 401. Also test with an expired JWT token: create a token, then configure the mock to simulate expiry. Confirm 401 is returned with "Invalid or expired token".

*This is a black-box test. You only need to know that the favourites endpoints require authentication. The auth dependency (`get_current_user`) checks the cookie/Bearer header before the route handler runs.*

**No login → no access to favourites. Login expired → 401, prompted to re-authenticate.**
