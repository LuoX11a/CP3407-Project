"""GET /api/v1/health — Health check endpoint."""

from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.services.geospatial import query_db_stats
from app.services.inference import is_model_loaded, get_model_meta

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    try:
        stats = query_db_stats()
        db_ok = True
    except Exception:
        stats = {"carpark_count": 0, "latest_data_ts": None}
        db_ok = False

    model_ok = is_model_loaded()

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db_connected=db_ok,
        model_loaded=model_ok,
        carpark_count=stats["carpark_count"],
        latest_data_ts=stats["latest_data_ts"],
    )
