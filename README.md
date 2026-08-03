# ParkGuideSG

Real-time HDB carpark availability & ML-powered recommendations for Singapore drivers.

**Live Demo**: [parkguidesg.onrender.com](https://parkguidesg.onrender.com)

---

## Features

- **Real-time carpark search** — find nearby HDB carparks with live availability
- **ML predictions** — LightGBM model forecasts vacancy rates for future time slots
- **Dual-mode retrieval** — toggle between 🟢 Now (real-time) and 🔮 Plan (ML forecast)
- **Composite scoring** — ranks carparks by vacancy, distance, trend, and weather
- **Interactive map** — Leaflet map with color-coded markers (green/yellow/red)
- **Favourites** — save frequently-used carparks with one click
- **PWA support** — install to home screen, offline fallback
- **Mobile-first UI** — draggable bottom sheet, large touch targets

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 (Vite), Leaflet, Chart.js |
| Backend | FastAPI (Python 3.11) |
| Database | Neon PostgreSQL (serverless) |
| ML | LightGBM (MAE 0.070, R² ~0.71) |
| Deployment | Docker → Render |
| CI/CD | GitHub Actions (pytest + vitest) |
| Data | Data.gov.sg HDB API + NEA Weather API |

## Architecture

```
Driver opens app → GPS location → /api/v1/recommend
  ├── Geospatial query (PostgreSQL Haversine)
  ├── ML prediction (LightGBM → LLM → Heuristic)
  ├── Composite scoring (vacancy × distance × trend × weather)
  └── Ranked results with 3-hour trend forecast
```

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npx vite --port 5173
```

Open `http://localhost:5173`

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `MODEL_PATH` | Path to model file (default: `ml/model/carpark_predictor.joblib`) |
| `LLM_API_KEY` | DeepSeek API key (optional fallback predictor) |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Health check (DB + model status) |
| `GET /api/v1/recommend?lat=&lng=&n=&radius_m=&forecast_time=` | Top-N recommendations |
| `GET /api/v1/carpark/{id}` | Carpark detail + 24h history |
| `GET /api/v1/carpark/search?q=` | Address search |
| `POST /api/v1/auth/register` | User registration |
| `POST /api/v1/auth/login` | User login |
| `GET /api/v1/favourites` | List favourites |
| `POST /api/v1/favourites/{id}` | Add favourite |
| `DELETE /api/v1/favourites/{id}` | Remove favourite |

## ML Model

- **Algorithm**: LightGBM Regressor
- **Training data**: 607,480 rows, 1,997 EPS carparks, 2 months
- **Features**: carpark_id, hour, day_of_week, is_weekend, weather_condition, total_lots
- **CV MAE**: 0.0703 | **Hold-out R²**: ~0.71
- **Model file**: `ml/model/carpark_predictor.joblib` (2.64 MB)
- **Auto-download**: Backend fetches from [GitHub Releases](https://github.com/LuoX11a/CP3407-Project/releases/tag/final-model-v2) if file not found

## Data

- **Carparks**: 2,277 HDB carparks with coordinates
- **Availability logs**: 607,482 records (2026-05-29 to 2026-07-27)
- **Weather**: 31,302 records from 47 NEA stations
- **Source**: Data.gov.sg APIs, frozen for final demo on 2026-08-03

## Team

- LuoX11a | Vince-1206 | LauTszTsun
- CP3407 — James Cook University Singapore
