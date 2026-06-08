"""GET /api/v1/carpark/{id} — Single carpark detail and history."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import CarparkDetail, CarparkHistoryResponse, HistoryPoint
from app.services.geospatial import query_carpark_detail, query_carpark_history

router = APIRouter()


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
