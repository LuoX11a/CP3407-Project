"""Database query service — geospatial lookup, carpark details, history.

Uses the shared connection pool from app.database (psycopg2 sync pool).
For async routes, use the SQLAlchemy session directly via get_db().
"""

import psycopg2.extras

from app.database import get_sync_conn


def query_nearby_carparks(lat: float, lng: float, radius_m: int, limit: int) -> list[dict]:
    """
    Find nearest carparks within radius_m using haversine distance.
    Returns carparks ordered by distance, joined with latest availability.
    """
    with get_sync_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                WITH nearby AS (
                    SELECT
                        c.carpark_id,
                        c.address,
                        c.car_lots,
                        c.lat,
                        c.lng,
                        l.available_lots,
                        l.vacancy_rate,
                        l.weather_condition,
                        l.timestamp AS last_updated,
                        haversine_distance(c.lat, c.lng, %s, %s) AS distance_m
                    FROM carparks c
                    LEFT JOIN v_carpark_latest l ON c.carpark_id = l.carpark_id
                    WHERE c.lat != 0
                      AND haversine_distance(c.lat, c.lng, %s, %s) < %s
                    ORDER BY distance_m
                    LIMIT %s
                )
                SELECT * FROM nearby
                """,
                (lat, lng, lat, lng, radius_m, limit),
            )
            return cur.fetchall()


def query_carpark_detail(carpark_id: str) -> dict | None:
    """Get full details for a single carpark including latest availability."""
    with get_sync_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    c.carpark_id, c.address, c.car_lots, c.motorcycle_lots,
                    c.lat, c.lng,
                    l.available_lots AS latest_available,
                    l.vacancy_rate   AS latest_vacancy,
                    l.weather_condition AS latest_weather,
                    l.timestamp      AS latest_updated
                FROM carparks c
                LEFT JOIN v_carpark_latest l ON c.carpark_id = l.carpark_id
                WHERE c.carpark_id = %s
                """,
                (carpark_id,),
            )
            return cur.fetchone()


def query_carpark_history(carpark_id: str, hours: int = 24) -> list[dict]:
    """Get recent availability history for a carpark."""
    with get_sync_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    timestamp AT TIME ZONE 'Asia/Singapore' AS timestamp,
                    available_lots,
                    vacancy_rate,
                    weather_condition
                FROM availability_logs
                WHERE carpark_id = %s
                  AND timestamp >= now() - INTERVAL '%s hours'
                ORDER BY timestamp DESC
                LIMIT 288
                """,
                (carpark_id, hours),
            )
            return cur.fetchall()


def search_carparks_by_address(query: str, limit: int = 20) -> list[dict]:
    """Full-text search carparks by address (ILIKE match)."""
    with get_sync_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT c.carpark_id, c.address, c.car_lots, c.lat, c.lng,
                       l.available_lots, l.vacancy_rate
                FROM carparks c
                LEFT JOIN v_carpark_latest l ON c.carpark_id = l.carpark_id
                WHERE c.address ILIKE %s
                ORDER BY c.carpark_id
                LIMIT %s
                """,
                (f"%{query}%", limit),
            )
            return cur.fetchall()


def query_db_stats() -> dict:
    """Check database health and return basic stats."""
    with get_sync_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM carparks WHERE lat != 0")
            carpark_count = cur.fetchone()["cnt"]

            cur.execute("SELECT MAX(timestamp) AS ts FROM availability_logs")
            latest = cur.fetchone()["ts"]

    return {
        "carpark_count": carpark_count,
        "latest_data_ts": latest.isoformat() if latest else None,
    }
