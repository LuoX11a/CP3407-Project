# ParkGuideSG

An intelligent, real-time parking recommendation system for Singapore's HDB carparks. The system ingests live government open data, runs geospatial queries, predicts vacancy rates, and presents personalized top-N recommendations through an interactive map interface.

## Team Members

| Name | Student ID |
|------|------------|
| Renxian Tang | 14889930 |
| Han-Wei Lin | 14775857 |
| Lau Tsz Tsun | 13955562 |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)               │
│  Leaflet.js (OneMap SG tiles) + Chart.js sparklines     │
│  GPS → Map Markers (Green/Yellow/Red) → Recommendation List │
└──────────────────────┬──────────────────────────────────┘
                       │  GET /api/v1/recommend?lat=&lng=&n=5
                       v
┌─────────────────────────────────────────────────────────┐
│                  BACKEND API (FastAPI + Uvicorn)          │
│  ┌─ Geospatial Router: haversine kNN query               │
│  └─ Inference Engine: LightGBM model (planned)           │
│                       LLM via DeepSeek API (current)     │
└──────┬──────────────────────────────┬───────────────────┘
       │                              │
       v                              v
┌──────────────────┐    ┌─────────────────────────────────┐
│  DATABASE (Neon)  │    │       ML PIPELINE               │
│  PostgreSQL 17    │    │  LightGBM regressor             │
│  haversine kNN    │    │  TimeSeriesSplit CV             │
│  6 tables + views │    │  Serialized .joblib artifact    │
└──────┬───────────┘    └─────────────────────────────────┘
       │
       ^
┌─────────────────────────────────────────────────────────┐
│              ETL PIPELINE (GitHub Actions)               │
│  Every 30 min: fetch HDB + NEA APIs → clean → store     │
│  SVY21 → WGS84 transform · weather alignment · features │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Status |
|-------|-----------|--------|
| **Frontend** | React 19, Vite, Leaflet.js (OneMap SG), Chart.js | 待开发 |
| **Backend** | Python 3.13, FastAPI, Uvicorn | 待开发 |
| **Database** | PostgreSQL 17 (Neon cloud), haversine-based kNN | Done |
| **ETL Pipeline** | Python, Pandas, GitHub Actions (30-min schedule) | 待开发 |
| **ML Engine** | LightGBM (training ready, awaiting data accumulation) | 待开发 |
| **Inference** | DeepSeek LLM API (temporary fallback until ML model trained) | 待开发 |
| **Map Service** | OneMap API (Singapore Official Map tiles) | 待开发 |

## Project Structure

```
CP3407-Project/
├── frontend/                     # React SPA (Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── MapView.jsx       # Leaflet map + OneMap tiles + color markers
│   │   │   ├── CarparkCard.jsx   # Sidebar card with Chart.js trend chart
│   │   │   └── RecommendationList.jsx  # Loading / error / result list
│   │   ├── services/
│   │   │   └── api.js            # Backend API client
│   │   ├── App.jsx               # Main: GPS, state, layout
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js            # Dev proxy /api → :8000
│   └── package.json
├── backend/                      # FastAPI application
│   ├── app/
│   │   ├── routers/
│   │   │   ├── recommend.py      # GET /api/v1/recommend
│   │   │   ├── carpark.py        # GET /api/v1/carpark/{id}
│   │   │   └── health.py         # GET /api/v1/health
│   │   ├── models/
│   │   │   └── schemas.py        # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── geospatial.py     # haversine kNN + carpark queries
│   │   │   └── inference.py      # ML model loader + LLM fallback
│   │   └── main.py               # App entry, CORS, lifespan
│   └── requirements.txt
├── ml/                           # ML training pipeline
│   ├── features.py               # Pull training data, build X/y
│   ├── train.py                  # TimeSeriesSplit + LightGBM training
│   ├── evaluate.py               # Hold-out eval, per-hour/weather breakdown
│   ├── requirements.txt
│   └── model/                    # Serialized .joblib artifacts
├── etl_cloud.py                  # Cloud ETL script (GitHub Actions)
├── 01_schema.sql                 # Database DDL (6 tables, 2 views, haversine fn)
├── 02_seed_holidays.sql          # Singapore public holidays
├── 04_bootstrap_carparks.py      # Static carpark data import
├── .github/workflows/etl.yml     # GitHub Actions: ETL every 30 min
└── .gitignore
```

## API Endpoints

### `GET /api/v1/recommend`

Returns top-N carpark recommendations near a user location.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | float | Yes | User latitude (WGS84) |
| `lng` | float | Yes | User longitude (WGS84) |
| `n` | int | No | Number of results (default: 5, max: 10) |
| `radius_m` | int | No | Search radius in metres (default: 1000) |

**Example**

```
GET /api/v1/recommend?lat=1.3521&lng=103.8198&n=5
```

```json
{
  "results": [
    {
      "carpark_id": "T01",
      "address": "Blk 101 Towner Road",
      "total_lots": 450,
      "available_lots": 120,
      "predicted_vacancy_rate": 0.28,
      "status": "YELLOW",
      "distance_m": 342,
      "weather": "Cloudy",
      "lat": 1.3234,
      "lng": 103.8567,
      "trend": [
        {"hour": "14:00", "rate": 0.31},
        {"hour": "15:00", "rate": 0.25},
        {"hour": "16:00", "rate": 0.18}
      ]
    }
  ],
  "query_time_ms": 45,
  "attribution": "Data sourced from Data.gov.sg and NEA"
}
```

### `GET /api/v1/carpark/{id}`

Returns detailed information and 24-hour history for a specific carpark.

### `GET /api/v1/health`

Health-check returning database connectivity and model load status.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (local) or Neon cloud database

### 1. Database Setup

```bash
# Option A: Neon cloud (recommended)
# Create a free database at https://neon.tech, then:
psql "$NEON_DATABASE_URL" -f 01_schema.sql
psql "$NEON_DATABASE_URL" -f 02_seed_holidays.sql
python 04_bootstrap_carparks.py

# Option B: Local PostgreSQL
createdb parkguidesg
psql -d parkguidesg -f 01_schema.sql
psql -d parkguidesg -f 02_seed_holidays.sql
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt

# Required environment variables:
export DATABASE_URL="postgresql://..."
export LLM_API_KEY="sk-..."           # DeepSeek API key for predictions
# Optional: set LLM_BASE_URL / LLM_MODEL for other providers

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev        # Starts on http://localhost:3000
```

### 4. ETL Pipeline (data collection)

Runs automatically via GitHub Actions every 30 minutes. For local testing:

```bash
export DATABASE_URL="postgresql://..."
python etl_cloud.py     # Runs one cycle and exits
```

### 5. ML Training (once 1+ months of data collected)

```bash
cd ml
pip install -r requirements.txt
export DATABASE_URL="postgresql://..."
python train.py --months 3 --output model/carpark_predictor.joblib
python evaluate.py model/carpark_predictor.joblib
```

Place the trained `.joblib` at `ml/model/carpark_predictor.joblib` and restart the backend to use the ML model instead of the LLM fallback.

## Prediction Strategy

The inference engine uses a 3-tier fallback:

| Priority | Method | Latency | Status |
|----------|--------|---------|--------|
| 1 | LightGBM model (.joblib) | <10 ms | Awaiting data accumulation (1–3 months) |
| 2 | DeepSeek LLM API | ~1.5 s | Current active fallback |
| 3 | Heuristic (time + lot size) | <1 ms | Final fallback |

## Data Sources

| API | Purpose | Refresh |
|-----|---------|---------|
| HDB Carpark Availability | Real-time lot counts per carpark | Every 5 min |
| NEA 2-Hour Weather Forecast | Weather conditions per station | Every 5 min |
| HDB Carpark Information | Static carpark addresses and coordinates | One-time |
| OneMap API | Official Singapore basemap tiles | On-demand |

All data provided under the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence).

## Database Schema

| Table | Description | Rows |
|-------|-------------|------|
| `carparks` | Static carpark info + WGS84 coordinates | 2,265 |
| `availability_logs` | Time-series availability with derived temporal features | Growing (GH Actions) |
| `weather_stations` | NEA weather station locations | 47 |
| `weather_records` | Timestamped weather readings | Growing |
| `public_holidays` | Singapore public holidays | 11 |
| `ml_predictions` | Cached prediction results | Future use |
| `ml_models` | Model version tracking | Future use |

Spatial queries use the built-in `haversine_distance()` SQL function for kNN lookups (portable, no PostGIS requirement).

## License

MIT License. See [LICENSE](LICENSE) file.
