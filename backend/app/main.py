"""ParkGuideSG Backend API — FastAPI application entry point."""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

# Load .env from project root
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parents[2] / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import recommend, carpark, health, auth, favourites
from app.services.inference import load_model, is_model_loaded

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: run migrations, load ML model. Shutdown: clean up."""
    log.info("Starting ParkGuideSG API server...")

    # Auto-run pending SQL migrations
    _migrations_dir = Path(__file__).resolve().parents[2]
    _db_url = os.getenv("DATABASE_URL", "")
    # Strip channel_binding param not supported by all libpq versions
    if "channel_binding=" in _db_url:
        import re
        _db_url = re.sub(r"[&?]channel_binding=[^&]*", "", _db_url)

    for _sql_file in sorted(_migrations_dir.glob("*.sql")):
        try:
            import psycopg2
            _conn = psycopg2.connect(_db_url)
            _cur = _conn.cursor()
            _cur.execute(_sql_file.read_text(encoding="utf-8"))
            _conn.commit()
            _conn.close()
            log.info("Migration applied: %s", _sql_file.name)
        except Exception as _e:
            log.error("Migration FAILED — %s: %s", _sql_file.name, _e)

    model_path = os.getenv("MODEL_PATH", "ml/model/carpark_predictor.joblib")
    try:
        if os.path.exists(model_path):
            load_model(model_path)
        else:
            log.warning(
                "Model not found at %s — recommendations will use heuristic fallback.",
                model_path,
            )
    except Exception as _e:
        log.warning("Model load failed: %s", _e)

    log.info("API ready. Model loaded: %s", is_model_loaded())
    yield
    log.info("Shutting down.")


app = FastAPI(
    title="ParkGuideSG",
    description="Real-time parking recommendation API for Singapore HDB carparks",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api/v1
app.include_router(recommend.router, prefix="/api/v1", tags=["Recommendations"])
app.include_router(carpark.router, prefix="/api/v1", tags=["Carpark"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(favourites.router, prefix="/api/v1", tags=["Favourites"])


# Serve frontend static files (production)
_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
