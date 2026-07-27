---
layout: default
title: Sequence Diagram
parent: Documentation
---

# ParkGuideSG — Recommendation Flow Sequence Diagram

```mermaid
sequenceDiagram
    actor Driver
    participant Browser as React Frontend
    participant API as FastAPI Backend
    participant ML as ML Inference
    participant DB as PostgreSQL
    participant Ext as External APIs

    Note over Driver,Ext: Main Recommendation Flow (GPS-based search)

    Driver->>Browser: Opens ParkGuideSG
    Browser->>Browser: navigator.geolocation.getCurrentPosition()
    Browser->>API: GET /api/v1/recommend?lat=1.35&lng=103.81&n=5&radius_m=3000

    API->>DB: SELECT * FROM carparks WHERE haversine(lat, lng, 1.35, 103.81) < 3000
    DB-->>API: Nearby carparks [A11, A12, A20, ...]

    loop For each carpark
        API->>DB: SELECT * FROM availability_logs WHERE carpark_id = ? ORDER BY timestamp DESC LIMIT 1
        DB-->>API: Latest availability record
    end

    API->>ML: predict_batch(carpark_ids, current_hour, weather)
    ML-->>API: Predicted vacancy rates [0.65, 0.42, 0.78, ...]

    API->>API: Composite scoring (vacancy × 0.4 + distance × 0.3 + trend × 0.2 + weather × 0.1)
    API-->>Browser: JSON { results: [...] }

    Browser->>Browser: Render markers on Leaflet map (green/yellow/red)
    Browser->>Browser: Render CarparkCard list with Chart.js trend
    Browser-->>Driver: Map + recommendation list visible

    Note over Driver,Ext: Authentication Flow (for favourites)

    Driver->>Browser: Click "Login"
    Browser->>API: POST /api/v1/auth/login { username, password }
    API->>DB: SELECT * FROM users WHERE username = ?
    DB-->>API: User record with bcrypt hash
    API->>API: verify_password(plain, hash)
    API->>API: create_access_token(user_id)
    API-->>Browser: Set-Cookie: token=JWT; HttpOnly; SameSite=Lax
    Browser-->>Driver: Logged in (no token in JS)

    Note over Driver,Ext: Favourite Toggle

    Driver->>Browser: Click star on carpark card
    Browser->>API: POST /api/v1/favourites { carpark_id } (Cookie: token=JWT)
    API->>API: decode JWT, extract user_id
    API->>DB: INSERT INTO favourites (user_id, carpark_id)
    API-->>Browser: 201 Created
    Browser->>Browser: Star fills yellow

    Note over Driver,Ext: ETL Pipeline (background, every 30 min)

    Ext->>Ext: GitHub Actions schedule triggers
    Ext->>Ext: Fetch Data.gov.sg carpark-availability
    Ext->>Ext: Fetch NEA 2-hour weather forecast
    Ext->>DB: INSERT INTO availability_logs (...) ON CONFLICT DO NOTHING
    Ext->>DB: INSERT INTO weather_records (...) ON CONFLICT UPDATE
    Ext->>DB: UPDATE availability_logs SET weather_condition = ...
```

## Key API Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/v1/recommend` | No | GPS-based nearby carpark search + ML predictions |
| GET | `/api/v1/carpark/search` | No | Address/area text search |
| GET | `/api/v1/carpark/{id}` | No | Single carpark detail with 24h history |
| POST | `/api/v1/auth/register` | No | New user registration |
| POST | `/api/v1/auth/login` | No | Login → httpOnly JWT cookie |
| POST | `/api/v1/auth/logout` | Yes | Clear JWT cookie |
| GET | `/api/v1/favourites` | Yes | List user's favourites |
| POST | `/api/v1/favourites` | Yes | Add favourite |
| DELETE | `/api/v1/favourites/{id}` | Yes | Remove favourite |
| GET | `/api/v1/health` | No | System health check |
