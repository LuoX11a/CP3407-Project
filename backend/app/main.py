"""ParkGuideSG Backend API — FastAPI application entry point."""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

# Load .env from project root
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parents[3] / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import recommend, carpark, health
from app.services.inference import load_model, is_model_loaded

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load ML model. Shutdown: clean up."""
    log.info("Starting ParkGuideSG API server...")

    model_path = os.getenv("MODEL_PATH", "ml/model/carpark_predictor.joblib")
    if os.path.exists(model_path):
        load_model(model_path)
    else:
        log.warning(
            "Model not found at %s — recommendations will use heuristic fallback. "
            "Train a model with 'python ml/train.py --months 3' once enough data is collected.",
            model_path,
        )

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


# Root redirect to docs
@app.get("/")
def root():
    return {
        "app": "ParkGuideSG API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
