# ParkGuideSG


An intelligent, real-time parking recommendation system for Singapore's Housing & Development Board (HDB) carparks. The system ingests live government open data, runs geospatial queries against a PostGIS database, predicts future vacancy rates with a lightweight gradient-boosted ML model, and presents personalized top-N recommendations through an interactive map interface.

## Team Members

| Name | Student ID |
|------|------------|
| Renxian Tang | 14889930 |
| Han-Wei Lin | 14775857 |
| Lau Tsz Tsun | 13955562 |


## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [System Layers](#system-layers)
  - [Frontend Layer](#frontend-layer)
  - [Backend API Layer](#backend-api-layer)
  - [Database Layer](#database-layer)
  - [Data Pipeline (ETL)](#data-pipeline-etl)
  - [Machine Learning Pipeline](#machine-learning-pipeline)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Data Sources](#data-sources)
- [License](#license)


## Architecture Overview

```
+--------------------------------------------------------------+
|                      FRONTEND LAYER                          |
|  React/Vue.js + Leaflet.js (OneMap)  |  Chart.js + HTML5    |
|  User GPS -> Map Markers             |  Recommendation List  |
+--------------------------+-----------------------------------+
                           |  HTTP GET (lat, lng)
                           v
+--------------------------------------------------------------+
|                    BACKEND API LAYER                         |
|           FastAPI + Uvicorn                                  |
|  +-----------------------+  +-----------------------------+  |
|  |  Geospatial Router    |  |  Model Inference Engine     |  |
|  |  PostGIS kNN query    |  |  GBDT (LightGBM/XGBoost)   |  |
|  |  within 1km radius    |  |  Batch prediction < 10ms   |  |
|  +-----------------------+  +-----------------------------+  |
+--------------+--------------------------+--------------------+
               |                          |
               v                          v
+---------------------------+  +--------------------------------+
|    DATABASE LAYER         |  |      DATA PIPELINE (ETL)       |
|  PostgreSQL +             |  |  Python Requests + Pandas +    |
|  PostGIS                  |  |  APScheduler (every 5 min)     |
|  - Static tables          |  |  - Data.gov.sg APIs            |
|  - Historical logs        |  |  - SVY21 -> WGS84 transform    |
|  - GIST spatial index     |  |  - Weather station alignment   |
+---------------------------+  +--------------------------------+
```


## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React / Vue.js, Leaflet.js (OneMap SG), Chart.js, HTML5/CSS3 |
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **Database** | PostgreSQL 15+ with PostGIS extension |
| **ETL Pipeline** | Python, Pandas, APScheduler |
| **ML Engine** | LightGBM / XGBoost / Scikit-learn, Joblib |
| **Map Service** | OneMap API (Singapore Official Map) |
| **DevOps** | Docker, GitHub Actions (CI/CD) |


## System Layers


### Frontend Layer

The user-facing single-page application provides:

- **Live Map View** — Invokes the browser Geolocation API to capture user GPS coordinates, renders the OneMap tile layer, and places color-coded markers (Green/Yellow/Red) on recommended HDB carparks.

- **Recommendation Panel** — Displays the top 3-5 nearest or most available carparks in a structured list layout, with popup cards showing real-time vacancy stats and forecast hourly trends via Chart.js sparklines.


### Backend API Layer

Two core modules run inside a single FastAPI process:

1. **Geospatial Router** — Accepts `(lat, lng)` from the frontend, executes a PostGIS `ST_DWithin` + kNN query to retrieve the nearest carparks, and assembles candidate details for scoring.

2. **Model Inference Engine** — Loads the serialized ML model into RAM at startup (`@app.on_event('startup')`), evaluates each candidate carpark against live temporal features (hour, day-of-week, holiday flag) and weather conditions (rain, overcast, clear), then runs a batch `model.predict(X_live)` returning per-carpark predicted vacancy rates. Target inference latency is under **10 ms**.


### Database Layer

PostgreSQL with PostGIS serves a dual role:

| Table Type | Purpose |
|------------|---------|
| **Static Table** | Permanent carpark definitions: address, capacity (total lots), WGS84 geometry points (latitude/longitude). |
| **Historical Table** | Cleaned, aggregated time-series records: carpark_id, timestamp, available_lots, weather label. |

A **GIST (Generalized Search Tree) spatial index** on the geometry column enables millisecond-range k-nearest-neighbor (kNN) lookups.


### Data Pipeline (ETL)

A scheduled cron-job pipeline refreshes the database every **5 minutes**:

1. **Ingestion** — Fetches live JSON from two government open-data endpoints:

   - HDB Carpark Availability API — real-time lot counts per carpark.

   - NEA Weather API — 2-hour nowcast weather conditions across Singapore weather stations.

2. **Cleaning & Transformation** — Normalizes dirty/missing records; converts local **SVY21** (EPSG:3414) coordinate grids to generic **WGS84** (EPSG:4326) latitude/longitude; maps each carpark to its nearest weather station.

3. **Aggregation** — Resamples minute-level data to **15- or 30-minute** intervals using averaging metrics to limit database footprint.

4. **Feature Derivation** — Extracts deterministic temporal attributes (`hour`, `day_of_week`, `is_weekend`, `is_public_holiday`).

5. **Persistence** — Bulk-inserts cleaned records into PostgreSQL for real-time serving and periodic ML re-training.


### Machine Learning Pipeline

A lightweight regression pipeline predicts future lot availability rates (0.0 to 1.0).

| Stage | Description |
|-------|------------|
| **Feature Engineering** | Temporal features (hour, day-of-week, weekend flag, Singapore public holidays); spatial features (label-encoded `carpark_id`, `total_lots`); weather features (one-hot encoded: light rain, heavy rain, overcast, clear). |
| **Target Variable** | `Y = available_lots / total_lots` — a continuous value in `[0.0, 1.0]`. |
| **Algorithm** | Gradient-boosted trees: **LightGBM**, **XGBoost**, or Scikit-learn **RandomForestRegressor**. |
| **Training Strategy** | 1 to 3 months of historical logs; single global model with `carpark_id` as a categorical feature to capture location-specific parking patterns. |
| **Validation** | Time Series Split cross-validation to prevent look-ahead leakage; evaluated via **MAE** and **RMSE**. |
| **Deployment** | Serialized artifact (`.joblib` or `.json`) loaded into FastAPI memory at startup; prediction runtime via `model.predict()` with under 10 ms latency. |


## Project Structure

```
CP3407-Project/
├── frontend/                # React/Vue.js SPA
│   ├── public/
│   ├── src/
│   │   ├── components/      # MapView, RecommendationList, CarparkCard
│   │   ├── services/        # API client, geolocation helper
│   │   └── App.js
│   └── package.json
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── routers/         # /recommend endpoint
│   │   ├── models/          # Pydantic schemas, ML model loader
│   │   ├── services/        # PostGIS query builder, inference engine
│   │   └── main.py          # App entry point, startup events
│   ├── tests/
│   └── requirements.txt
├── etl/                     # Data pipeline
│   ├── ingestion.py         # API fetchers (HDB + NEA)
│   ├── transform.py         # SVY21 to WGS84, weather alignment
│   ├── aggregate.py         # Time-window resampling
│   └── scheduler.py         # APScheduler cron configuration
├── ml/                      # Model training and evaluation
│   ├── notebooks/           # Exploratory analysis
│   ├── train.py             # Training script
│   ├── evaluate.py          # Cross-validation and metrics
│   └── model/               # Serialized .joblib artifacts
├── db/                      # Database migrations and seed data
│   └── migrations/
├── docker-compose.yml
└── README.md
```


## Getting Started


### Prerequisites

- **Python** 3.11+

- **Node.js** 18+

- **PostgreSQL** 15+ with **PostGIS** extension

- **Docker** (optional, for containerized setup)


### Local Development

1. **Clone the repository**

   ```bash
   git clone https://github.com/LuoX11a/CP3407-Project.git
   cd CP3407-Project
   ```

2. **Setup environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL credentials and Data.gov.sg API keys
   ```

3. **Start the database**

   ```bash
   docker-compose up -d postgres
   # Or connect to an existing PostgreSQL + PostGIS instance
   ```

4. **Run database migrations**

   ```bash
   cd db && alembic upgrade head
   ```

5. **Install backend dependencies and start API server**

   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Start the ETL scheduler**

   ```bash
   cd etl
   python scheduler.py
   ```

7. **Install frontend dependencies and start dev server**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

8. **Train the ML model (optional, first-time setup)**

   ```bash
   cd ml
   python train.py --months 3 --output model/carpark_predictor.joblib
   ```


### Docker (All-in-One)

```bash
docker-compose up --build
```


## API Endpoints


### `GET /api/v1/recommend`

Returns top-N carpark recommendations for a given user location.


**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | float | Yes | User latitude (WGS84) |
| `lng` | float | Yes | User longitude (WGS84) |
| `n` | int | No | Number of results (default: 5, max: 10) |
| `radius_m` | int | No | Search radius in metres (default: 1000) |


**Example Request**

```
GET /api/v1/recommend?lat=1.3521&lng=103.8198&n=5
```


**Example Response**

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
      "weather": "Clear",
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

Returns detailed information and historical trends for a specific carpark.


### `GET /api/v1/health`

Health-check endpoint returning database connectivity and model load status.


## Data Sources

This project uses Singapore government open data, accessed via [Data.gov.sg](https://data.gov.sg) APIs:

| API | Purpose | Refresh Rate |
|-----|---------|--------------|
| HDB Carpark Availability | Real-time available lots per carpark | Every 5 min |
| NEA 2-Hour Weather Forecast | Nowcast weather conditions per station | Every 5 min |
| OneMap API | Official Singapore basemap tiles and geocoding | Static / On-demand |

> All data is provided under the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence).


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
