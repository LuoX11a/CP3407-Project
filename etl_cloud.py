"""
ParkGuideSG - Cloud ETL Pipeline (GitHub Actions)
Single-cycle mode: fetch once, insert, then exit.
Triggered every 30 minutes by GitHub Actions schedule.

Requirements: pip install psycopg2-binary requests pandas pyproj
"""

import os
import logging
from datetime import datetime

import pandas as pd
import psycopg2
import psycopg2.extras
import requests
from pyproj import Transformer

# ---------------------------------------------------------------------------
# Configuration (all from environment variables)
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")  # Neon connection string
HDB_API_URL = "https://api.data.gov.sg/v1/transport/carpark-availability"
NEA_API_URL = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

svy21_to_wgs84 = Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def fetch_carpark_availability() -> list[dict]:
    resp = requests.get(HDB_API_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    records = []
    ts_str = data["items"][0]["timestamp"]
    timestamp = pd.Timestamp(ts_str)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("Asia/Singapore")
    else:
        timestamp = timestamp.tz_convert("Asia/Singapore")

    for item in data["items"]:
        for cp in item["carpark_data"]:
            for info in cp["carpark_info"]:
                if info["lot_type"] == "C":
                    records.append({
                        "carpark_id": cp["carpark_number"],
                        "timestamp": timestamp,
                        "total_lots": int(info["total_lots"]),
                        "available_lots": int(info["lots_available"]),
                    })
    return records


def fetch_weather() -> tuple[list[dict], list[dict]]:
    resp = requests.get(NEA_API_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    stations = []
    for s in data.get("area_metadata", []):
        stations.append({
            "station_id": s["name"],
            "name": s["name"],
            "lat": s["label_location"]["latitude"],
            "lng": s["label_location"]["longitude"],
        })

    ts_str = data["items"][0]["timestamp"]
    timestamp = pd.Timestamp(ts_str)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("Asia/Singapore")
    else:
        timestamp = timestamp.tz_convert("Asia/Singapore")

    records = []
    for f in data["items"][0]["forecasts"]:
        records.append({
            "station_id": f["area"],
            "timestamp": timestamp,
            "weather_condition": f["forecast"].lower(),
        })

    return stations, records


# ---------------------------------------------------------------------------
# ETL operations
# ---------------------------------------------------------------------------

def ensure_stations_present(conn, stations: list[dict]):
    with conn.cursor() as cur:
        sql = """
            INSERT INTO weather_stations (station_id, name, lat, lng)
            VALUES %s
            ON CONFLICT (station_id) DO UPDATE
            SET name = EXCLUDED.name, lat = EXCLUDED.lat, lng = EXCLUDED.lng
        """
        values = [(s["station_id"], s["name"], s["lat"], s["lng"]) for s in stations]
        psycopg2.extras.execute_values(cur, sql, values)
    conn.commit()


def ensure_carpark_exists(conn, carpark_id: str, total_lots: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO carparks (carpark_id, address, car_lots, svy21_x, svy21_y, lat, lng)
            VALUES (%s, %s, %s, 0, 0, 0, 0)
            ON CONFLICT (carpark_id) DO UPDATE
            SET car_lots = GREATEST(carparks.car_lots, EXCLUDED.car_lots)
            """,
            (carpark_id, f"Carpark {carpark_id}", total_lots),
        )
    conn.commit()


def load_carpark_availability(conn, records: list[dict]):
    with conn.cursor() as cur:
        sql = """
            INSERT INTO availability_logs
                (carpark_id, timestamp, available_lots, vacancy_rate,
                 hour, day_of_week, is_weekend, is_public_holiday)
            VALUES %s
            ON CONFLICT DO NOTHING
        """
        values = []
        for r in records:
            ts = r["timestamp"]
            vacancy = r["available_lots"] / r["total_lots"] if r["total_lots"] > 0 else 0
            vacancy = round(min(max(vacancy, 0), 1), 3)
            dow = ts.dayofweek

            values.append((
                r["carpark_id"],
                ts.to_pydatetime(),
                r["available_lots"],
                vacancy,
                ts.hour,
                dow,
                dow >= 5,
                False,
            ))
            ensure_carpark_exists(conn, r["carpark_id"], r["total_lots"])

        psycopg2.extras.execute_values(cur, sql, values)
    conn.commit()
    log.info("Inserted %d availability records", len(values))


def load_weather_records(conn, records: list[dict]):
    with conn.cursor() as cur:
        sql = """
            INSERT INTO weather_records (station_id, timestamp, weather_condition)
            VALUES %s
            ON CONFLICT DO NOTHING
        """
        seen = set()
        values = []
        for r in records:
            key = (r["station_id"], r["timestamp"])
            if key not in seen:
                seen.add(key)
                values.append((r["station_id"], r["timestamp"].to_pydatetime(), r["weather_condition"]))
        psycopg2.extras.execute_values(cur, sql, values)
    conn.commit()
    log.info("Inserted %d weather records", len(values))


def update_weather_on_availability(conn):
    log.info("Updating weather conditions...")
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE availability_logs a
            SET weather_condition = wr.weather_condition
            FROM (
                SELECT DISTINCT ON (a2.id)
                    a2.id, r.weather_condition
                FROM availability_logs a2
                CROSS JOIN LATERAL (
                    SELECT r2.weather_condition
                    FROM weather_records r2
                    WHERE r2.timestamp <= a2.timestamp
                      AND r2.timestamp >= a2.timestamp - INTERVAL '2 hours'
                    ORDER BY ABS(EXTRACT(EPOCH FROM a2.timestamp - r2.timestamp))
                    LIMIT 1
                ) r
                WHERE a2.weather_condition IS NULL
            ) wr
            WHERE a.id = wr.id
            """
        )
    conn.commit()
    log.info("Weather update: %d rows affected", cur.rowcount)


def update_public_holiday_flags(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE availability_logs a
            SET is_public_holiday = TRUE
            FROM public_holidays h
            WHERE a.timestamp::date = h.date
              AND a.is_public_holiday = FALSE
            """
        )
    conn.commit()


def cleanup_old_records(conn):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM availability_logs WHERE timestamp < now() - INTERVAL '90 days'"
        )
    conn.commit()
    if cur.rowcount:
        log.info("Cleaned up %d old records", cur.rowcount)


# ---------------------------------------------------------------------------
# Main — single cycle, then exit
# ---------------------------------------------------------------------------

def main():
    log.info("=== ParkGuideSG Cloud ETL Cycle ===")

    conn = psycopg2.connect(DATABASE_URL)
    log.info("Connected to cloud database")

    # 1. Weather
    stations, weather_records = fetch_weather()
    ensure_stations_present(conn, stations)
    load_weather_records(conn, weather_records)
    log.info("Weather: %d stations, %d records", len(stations), len(weather_records))

    # 2. HDB availability
    carpark_records = fetch_carpark_availability()
    load_carpark_availability(conn, carpark_records)
    log.info("Availability: %d records", len(carpark_records))

    # 3. Backfill weather
    update_weather_on_availability(conn)

    # 4. Holiday flags
    update_public_holiday_flags(conn)

    # 5. Cleanup
    cleanup_old_records(conn)

    conn.close()
    log.info("=== Cycle complete ===")


if __name__ == "__main__":
    main()
