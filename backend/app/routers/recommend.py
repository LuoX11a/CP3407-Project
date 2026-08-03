"""GET /api/v1/recommend — Top-N carpark recommendations with composite scoring."""

import time
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    CarparkResult,
    RecommendResponse,
    ScoreBreakdown,
    TrendPoint,
)
from app.services.geospatial import query_nearby_carparks
from app.services.inference import predict, is_model_loaded
from app.services.rate_info import get_hourly_rate, has_ev_charging

log = logging.getLogger(__name__)
router = APIRouter()
SGT = timezone(timedelta(hours=8))

# Scoring weights (tunable)
W_VACANCY = 0.40
W_DISTANCE = 0.30
W_TREND = 0.20
W_WEATHER = 0.10


def _status(vacancy: float) -> str:
    if vacancy > 0.5:
        return "GREEN"
    elif vacancy > 0.2:
        return "YELLOW"
    return "RED"


def _make_trend(hour_now: int, predicted: float) -> list[TrendPoint]:
    """Generate a 3-hour forecast trend from a single prediction."""
    trend = []
    for offset in range(1, 4):
        h = (hour_now + offset) % 24
        rate = round(predicted + (1.0 - predicted) * (3 - offset) / 3 * 0.1, 3)
        rate = max(0.0, min(1.0, rate))
        trend.append(TrendPoint(hour=f"{h:02d}:00", rate=rate))
    return trend


def _weather_penalty(weather: str) -> float:
    """Return a penalty factor for weather: worse weather → lower score."""
    w = (weather or "").lower()
    if "thundery" in w or "heavy" in w:
        return 0.5
    elif "rain" in w or "showers" in w:
        return 0.7
    return 1.0


@router.get("/recommend", response_model=RecommendResponse)
def recommend(
    lat: float = Query(..., ge=-90, le=90, description="User latitude (WGS84)"),
    lng: float = Query(..., ge=-180, le=180, description="User longitude (WGS84)"),
    n: int = Query(default=5, ge=1, le=10, description="Number of results"),
    radius_m: int = Query(default=3000, ge=100, le=5000, description="Search radius in metres"),
    forecast_time: str | None = Query(default=None, description="Target time for forecast (ISO 8601, e.g. 2026-08-04T18:00:00+08:00)"),
):
    t0 = time.perf_counter()

    # 0. Parse forecast_time → if provided, use for ML predictions
    target_dt: datetime | None = None
    is_forecast = False
    if forecast_time:
        try:
            target_dt = datetime.fromisoformat(forecast_time)
            if target_dt.tzinfo is None:
                target_dt = target_dt.replace(tzinfo=SGT)
            is_forecast = True
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid forecast_time: {forecast_time}")

    # 1. Geospatial query
    carparks = query_nearby_carparks(lat, lng, radius_m, n * 2)  # get more for scoring

    if not carparks:
        raise HTTPException(
            status_code=404,
            detail=f"No carparks found within {radius_m}m of your location",
        )

    # 2. Run predictions (ML model → LLM → heuristic fallback)
    try:
        preds = predict(carparks, target_time=target_dt)
    except Exception as e:
        log.warning("Prediction failed: %s, using DB values", e)
        preds = [
            round(float(cp.get("vacancy_rate", 0.5) or 0.5), 3)
            for cp in carparks
        ]

    # 3. Composite scoring
    max_dist = max(cp["distance_m"] for cp in carparks) or 1
    now_hour = target_dt.hour if target_dt else datetime.now(SGT).hour
    results = []

    for cp, pred in zip(carparks, preds):
        status = _status(pred)
        dist = cp["distance_m"]
        weather = (cp.get("weather_condition") or "Unknown").title()
        wp = _weather_penalty(weather)

        # Sub-scores (normalised to [0, 1])
        vacancy_score = round(min(pred, 1.0), 3)
        distance_score = round(1.0 - dist / max_dist, 3)
        trend_score = round(0.5 + 0.5 * (pred - 0.5), 3)  # centre around 0.5
        weather_score = round(wp, 3)

        composite = round(
            W_VACANCY * vacancy_score
            + W_DISTANCE * distance_score
            + W_TREND * trend_score
            + W_WEATHER * weather_score,
            3,
        )

        results.append((
            composite,
            CarparkResult(
                carpark_id=cp["carpark_id"],
                address=cp["address"],
                total_lots=cp["car_lots"],
                available_lots=cp.get("available_lots", 0) or 0,
                predicted_vacancy_rate=pred,
                status=status,
                distance_m=round(dist, 0),
                weather=weather,
                lat=cp["lat"],
                lng=cp["lng"],
                trend=_make_trend(now_hour, pred),
                composite_score=composite,
                score_breakdown=ScoreBreakdown(
                    vacancy_score=vacancy_score,
                    distance_score=distance_score,
                    trend_score=trend_score,
                    weather_score=weather_score,
                ),
                hourly_rate=get_hourly_rate(cp["carpark_id"], cp["lat"], cp["lng"]),
                ev_charging=has_ev_charging(cp["carpark_id"]),
            ),
        ))

    # Sort by composite score descending, take top N
    results.sort(key=lambda x: x[0], reverse=True)
    results = results[:n]

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return RecommendResponse(
        results=[r[1] for r in results],
        query_time_ms=round(elapsed_ms, 1),
        mode="forecast" if is_forecast else "realtime",
        forecast_time=forecast_time if is_forecast else None,
    )
