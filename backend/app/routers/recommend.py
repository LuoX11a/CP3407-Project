"""GET /api/v1/recommend — Top-N carpark recommendations."""

import time
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    CarparkResult,
    RecommendResponse,
    TrendPoint,
)
from app.services.geospatial import query_nearby_carparks
from app.services.inference import predict, is_model_loaded

log = logging.getLogger(__name__)
router = APIRouter()
SGT = timezone(timedelta(hours=8))


def _status(vacancy: float) -> str:
    if vacancy > 0.5:
        return "GREEN"
    elif vacancy > 0.2:
        return "YELLOW"
    return "RED"


def _make_trend(hour_now: int, predicted: float) -> list[TrendPoint]:
    """Generate a simple 3-hour forecast trend from a single prediction."""
    trend = []
    for offset in range(1, 4):
        h = (hour_now + offset) % 24
        # Linear decay toward the predicted rate
        rate = round(predicted + (1.0 - predicted) * (3 - offset) / 3 * 0.1, 3)
        rate = max(0.0, min(1.0, rate))
        trend.append(TrendPoint(hour=f"{h:02d}:00", rate=rate))
    return trend


@router.get("/recommend", response_model=RecommendResponse)
def recommend(
    lat: float = Query(..., ge=-90, le=90, description="User latitude (WGS84)"),
    lng: float = Query(..., ge=-180, le=180, description="User longitude (WGS84)"),
    n: int = Query(default=5, ge=1, le=10, description="Number of results"),
    radius_m: int = Query(default=1000, ge=100, le=5000, description="Search radius in metres"),
):
    t0 = time.perf_counter()

    # 1. Geospatial query
    carparks = query_nearby_carparks(lat, lng, radius_m, n)

    if not carparks:
        raise HTTPException(
            status_code=404,
            detail=f"No carparks found within {radius_m}m of your location",
        )

    # 2. Run predictions (ML model → LLM → heuristic fallback)
    try:
        preds = predict(carparks)
    except Exception as e:
        log.warning("Prediction failed: %s, using DB values", e)
        preds = [
            round(float(cp.get("vacancy_rate", 0.5) or 0.5), 3)
            for cp in carparks
        ]

    # 3. Assemble results
    now_hour = datetime.now(SGT).hour
    results = []
    for cp, pred in zip(carparks, preds):
        status = _status(pred)
        results.append(CarparkResult(
            carpark_id=cp["carpark_id"],
            address=cp["address"],
            total_lots=cp["car_lots"],
            available_lots=cp.get("available_lots", 0) or 0,
            predicted_vacancy_rate=pred,
            status=status,
            distance_m=round(cp["distance_m"], 0),
            weather=(cp.get("weather_condition") or "Unknown").title(),
            lat=cp["lat"],
            lng=cp["lng"],
            trend=_make_trend(now_hour, pred),
        ))

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return RecommendResponse(
        results=results,
        query_time_ms=round(elapsed_ms, 1),
    )
