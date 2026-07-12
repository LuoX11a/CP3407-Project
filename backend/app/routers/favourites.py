"""Favourites CRUD — protected endpoints."""

import psycopg2.extras
from fastapi import APIRouter, Depends, HTTPException

from app.services.auth import get_current_user
from app.database import get_sync_conn

router = APIRouter()


@router.get("/favourites")
def list_favourites(user: dict = Depends(get_current_user)):
    with get_sync_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT c.carpark_id, c.address, c.car_lots, c.lat, c.lng,
                       l.available_lots, l.vacancy_rate, l.weather_condition,
                       f.created_at AS favourited_at
                FROM favourites f
                JOIN carparks c ON f.carpark_id = c.carpark_id
                LEFT JOIN v_carpark_latest l ON c.carpark_id = l.carpark_id
                WHERE f.user_id = %s
                ORDER BY f.created_at DESC
                """,
                (user["user_id"],),
            )
            rows = cur.fetchall()

    return {"favourites": [
        {
            "carpark_id": r["carpark_id"],
            "address": r["address"],
            "car_lots": r["car_lots"],
            "lat": r["lat"],
            "lng": r["lng"],
            "available_lots": r.get("available_lots") or 0,
            "vacancy_rate": float(r.get("vacancy_rate") or 0),
            "weather_condition": r.get("weather_condition"),
        }
        for r in rows
    ]}


@router.post("/favourites/{carpark_id}")
def add_favourite(carpark_id: str, user: dict = Depends(get_current_user)):
    with get_sync_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM carparks WHERE carpark_id = %s", (carpark_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Carpark not found")
            cur.execute(
                "INSERT INTO favourites (user_id, carpark_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (user["user_id"], carpark_id),
            )
    return {"status": "ok"}


@router.delete("/favourites/{carpark_id}")
def remove_favourite(carpark_id: str, user: dict = Depends(get_current_user)):
    with get_sync_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM favourites WHERE user_id = %s AND carpark_id = %s",
                (user["user_id"], carpark_id),
            )
    return {"status": "ok"}
