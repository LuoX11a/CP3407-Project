"""Carpark detail, history, and address search endpoints."""

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    CarparkDetail, CarparkHistoryResponse, HistoryPoint,
    SearchResponse, SearchResult,
)
from app.services.geospatial import query_carpark_detail, query_carpark_history, search_carparks_by_address

router = APIRouter()


@router.get("/carpark/search", response_model=SearchResponse)
def carpark_search(
    q: str = Query(..., min_length=1, max_length=200, description="Address or area search query"),
    limit: int = Query(default=20, ge=1, le=50),
):
    rows = search_carparks_by_address(q, limit)
    return SearchResponse(results=[
        SearchResult(
            carpark_id=r["carpark_id"],
            address=r["address"],
            car_lots=r["car_lots"],
            lat=r["lat"],
            lng=r["lng"],
            available_lots=r.get("available_lots"),
            vacancy_rate=float(r["vacancy_rate"]) if r.get("vacancy_rate") is not None else None,
        )
        for r in rows
    ])


@router.get("/carpark/{carpark_id}", response_model=CarparkHistoryResponse)
def carpark_detail(carpark_id: str):
    detail = query_carpark_detail(carpark_id)

    if detail is None:
        raise HTTPException(status_code=404, detail=f"Carpark '{carpark_id}' not found")

    history = query_carpark_history(carpark_id, hours=24)

    return CarparkHistoryResponse(
        carpark=CarparkDetail(
            carpark_id=detail["carpark_id"],
            address=detail["address"],
            car_lots=detail["car_lots"],
            motorcycle_lots=detail.get("motorcycle_lots", 0),
            lat=detail["lat"],
            lng=detail["lng"],
            latest_available=detail.get("latest_available"),
            latest_vacancy=detail.get("latest_vacancy"),
            latest_weather=detail.get("latest_weather"),
            latest_updated=detail["latest_updated"].isoformat() if detail.get("latest_updated") else None,
        ),
        history=[
            HistoryPoint(
                timestamp=h["timestamp"].isoformat() if hasattr(h["timestamp"], "isoformat") else str(h["timestamp"]),
                available_lots=h["available_lots"],
                vacancy_rate=float(h["vacancy_rate"]),
                weather_condition=h.get("weather_condition"),
            )
            for h in history
        ],
    )
