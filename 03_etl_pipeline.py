"""
ParkGuideSG - ETL Pipeline
Fetches HDB carpark availability + NEA weather data every 5 minutes,
derives temporal features, and stores in the database.

Requirements: pip install psycopg2-binary requests pandas pyproj
"""

import os
import time
import logging
from datetime import datetime

import pandas as pd
import psycopg2
import psycopg2.extras
import requests
from pyproj import Transformer

# ---------------------------------------------------------------------------
# Configuration (override via environment variables)
# ---------------------------------------------------------------------------

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "dbname": os.getenv("PG_DB", "parkguidesg"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "parkguide"),
}

HDB_API_URL = "https://api.data.gov.sg/v1/transport/carpark-availability"
NEA_API_URL = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
NEA_TEMP_URL = "https://api.data.gov.sg/v1/environment/air-temperature"
NEA_HUMID_URL = "https://api.data.gov.sg/v1/environment/relative-humidity"
NEA_RAIN_URL = "https://api.data.gov.sg/v1/environment/rainfall"
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "300"))  # 5 minutes
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "90"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# SVY21 (EPSG:3414) to WGS84 (EPSG:4326) transformer
svy21_to_wgs84 = Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def fetch_carpark_availability() -> list[dict]:
    """Fetch live HDB carpark lot counts from data.gov.sg."""
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
    """Fetch NEA 2-hour weather forecast. Returns (stations, records)."""
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


def _haversine(lat1, lng1, lat2, lng2):
    """Distance in metres between two lat/lng points."""
    from math import radians, sin, cos, sqrt, atan2
    r = 6371000
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


def _fetch_measurement(url):
    """Fetch a single NEA measurement endpoint. Returns (readings, stations_meta)."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    stations = {}
    for s in data.get("metadata", {}).get("stations", []):
        loc = s.get("location", {})
        stations[s["id"]] = (loc.get("latitude", 0), loc.get("longitude", 0))
    readings = {}
    for item in data.get("items", []):
        for r in item.get("readings", []):
            readings[r["station_id"]] = r["value"]
    return readings, stations


def fetch_weather_measurements(forecast_areas):
    """
    Fetch temperature, humidity, rainfall from NEA measurement APIs.
    Maps each forecast area to the nearest measurement station's reading.
    """
    temp_readings, temp_stations = _fetch_measurement(NEA_TEMP_URL)
    hum_readings, hum_stations = _fetch_measurement(NEA_HUMID_URL)
    rain_readings, rain_stations = _fetch_measurement(NEA_RAIN_URL)

    result = {}
    for area in forecast_areas:
        name = area["name"]
        alat, alng = area["lat"], area["lng"]

        temp = hum = rain = None

        best_dist = float("inf")
        for sid, val in temp_readings.items():
            sloc = temp_stations.get(sid)
            if sloc:
                d = _haversine(alat, alng, sloc[0], sloc[1])
                if d < best_dist:
                    best_dist = d
                    temp = val

        best_dist = float("inf")
        for sid, val in hum_readings.items():
            sloc = hum_stations.get(sid)
            if sloc:
                d = _haversine(alat, alng, sloc[0], sloc[1])
                if d < best_dist:
                    best_dist = d
                    hum = val

        best_dist = float("inf")
        for sid, val in rain_readings.items():
            sloc = rain_stations.get(sid)
            if sloc:
                d = _haversine(alat, alng, sloc[0], sloc[1])
                if d < best_dist:
                    best_dist = d
                    rain = val

        result[name] = {"temperature": temp, "humidity": hum, "rainfall": rain}

    return result


def fetch_hdb_carpark_static() -> list[dict]:
    """
    Fetch static HDB carpark info (address + SVY21 coordinates) from data.gov.sg.
    This is a one-time bootstrap, not called every cycle.
    """
    url = "https://data.gov.sg/api/action/datastore_search"
    params = {
        "resource_id": "d_23f946fa557947f93a8043bbef41dd09",
        "limit": 2000,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    carparks = []
    for rec in data["result"]["records"]:
        carparks.append({
            "carpark_id": rec.get("car_park_no", ""),
            "address": rec.get("address", ""),
            "car_lots": int(rec.get("car_park_bays", 0) or 0),
            "svy21_x": float(rec.get("x_coord", 0) or 0),
            "svy21_y": float(rec.get("y_coord", 0) or 0),
        })
    return carparks


# ---------------------------------------------------------------------------
# ETL operations
# ---------------------------------------------------------------------------

def bootstrap_carparks(conn):
    """One-time load of static carpark data from data.gov.sg."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM carparks")
        count = cur.fetchone()[0]
        if count > 0:
            log.info("Carparks already bootstrapped: %d rows", count)
            return

    log.info("Bootstrapping carpark static data from data.gov.sg...")
    try:
        carparks = fetch_hdb_carpark_static()
    except Exception as e:
        log.warning("Could not fetch static carpark data: %s", e)
        log.warning("Carparks will be auto-registered as they appear in availability API")
        return

    with conn.cursor() as cur:
        sql = """
            INSERT INTO carparks (carpark_id, address, car_lots, svy21_x, svy21_y, lat, lng)
            VALUES %s
            ON CONFLICT (carpark_id) DO UPDATE
            SET address = EXCLUDED.address,
                car_lots = GREATEST(carparks.car_lots, EXCLUDED.car_lots),
                svy21_x  = EXCLUDED.svy21_x,
                svy21_y  = EXCLUDED.svy21_y,
                lat      = EXCLUDED.lat,
                lng      = EXCLUDED.lng
        """
        values = []
        for cp in carparks:
            if cp["svy21_x"] == 0 and cp["svy21_y"] == 0:
                continue
            lng, lat = svy21_to_wgs84.transform(cp["svy21_x"], cp["svy21_y"])
            values.append((
                cp["carpark_id"],
                cp["address"],
                cp["car_lots"],
                cp["svy21_x"],
                cp["svy21_y"],
                round(lat, 8),
                round(lng, 8),
            ))
        psycopg2.extras.execute_values(cur, sql, values)
    conn.commit()
    log.info("Bootstrapped %d carparks", len(values))


def ensure_stations_present(conn, stations: list[dict]):
    """Upsert weather station metadata."""
    with conn.cursor() as cur:
        sql = """
            INSERT INTO weather_stations (station_id, name, lat, lng)
            VALUES %s
            ON CONFLICT (station_id) DO UPDATE
            SET name = EXCLUDED.name,
                lat  = EXCLUDED.lat,
                lng  = EXCLUDED.lng
        """
        values = [(s["station_id"], s["name"], s["lat"], s["lng"]) for s in stations]
        psycopg2.extras.execute_values(cur, sql, values)
    conn.commit()


def ensure_carpark_exists(conn, carpark_id: str, total_lots: int):
    """Auto-register a carpark if it appears in the API but not in our static table."""
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
    """Insert availability records with derived temporal features."""
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

            # pandas: Monday=0, Sunday=6
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

            # Ensure carpark exists in static table
            ensure_carpark_exists(conn, r["carpark_id"], r["total_lots"])

        psycopg2.extras.execute_values(cur, sql, values)
    conn.commit()
    log.info("Inserted %d availability records", len(values))


def load_weather_records(conn, records: list[dict], measurements: dict = None):
    """Insert weather records — deduplicate by (station, timestamp)."""
    with conn.cursor() as cur:
        sql = """
            INSERT INTO weather_records (station_id, timestamp, weather_condition,
                                         temperature, humidity, rainfall)
            VALUES %s
            ON CONFLICT (station_id, timestamp) DO UPDATE
            SET temperature = COALESCE(EXCLUDED.temperature, weather_records.temperature),
                humidity    = COALESCE(EXCLUDED.humidity, weather_records.humidity),
                rainfall    = COALESCE(EXCLUDED.rainfall, weather_records.rainfall)
        """
        values = []
        seen = set()
        for r in records:
            key = (r["station_id"], r["timestamp"])
            if key not in seen:
                seen.add(key)
                m = measurements.get(r["station_id"], {}) if measurements else {}
                values.append((
                    r["station_id"],
                    r["timestamp"].to_pydatetime(),
                    r["weather_condition"],
                    m.get("temperature"),
                    m.get("humidity"),
                    m.get("rainfall"),
                ))
        psycopg2.extras.execute_values(cur, sql, values)
    conn.commit()
    log.info("Inserted %d weather records", len(values))


def update_weather_on_availability(conn):
    """
    Backfill weather_condition on availability_logs.
    Joins each availability record to the weather record from the nearest
    station at the closest timestamp, using the haversine_distance function.
    """
    log.info("Updating weather conditions on availability_logs...")
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE availability_logs a
            SET weather_condition = wr.weather_condition
            FROM (
                SELECT DISTINCT ON (a2.id)
                    a2.id,
                    r.weather_condition
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
    log.info("Weather update complete, %d rows affected", cur.rowcount)


def update_public_holiday_flags(conn):
    """Mark availability records that fall on a public holiday."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE availability_logs a
            SET is_public_holiday = TRUE
            FROM public_holidays h
            WHERE a.timestamp::date = h.date
              AND a.is_public_holiday = FALSE
              AND a.timestamp >= now() - INTERVAL '7 days'
            """
        )
    conn.commit()


def cleanup_old_records(conn):
    """Remove availability logs older than RETENTION_DAYS."""
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM availability_logs WHERE timestamp < now() - INTERVAL '{RETENTION_DAYS} days'"
        )
    conn.commit()
    log.info("Cleaned up %d old availability records", cur.rowcount)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    log.info("Starting ParkGuideSG ETL pipeline")
    log.info("Fetch interval: %ds, retention: %dd", FETCH_INTERVAL, RETENTION_DAYS)

    conn = get_connection()
    log.info("Connected to database %s", DB_CONFIG["dbname"])

    # One-time: load static carpark data
    bootstrap_carparks(conn)

    try:
        while True:
            cycle_start = time.monotonic()

            try:
                # 1. Weather
                stations, weather_records = fetch_weather()
                measurements = fetch_weather_measurements(stations)
                ensure_stations_present(conn, stations)
                load_weather_records(conn, weather_records, measurements)

                # 2. HDB carpark availability
                carpark_records = fetch_carpark_availability()
                load_carpark_availability(conn, carpark_records)

                # 3. Backfill weather on new availability records
                update_weather_on_availability(conn)

                # 4. Holiday flags
                update_public_holiday_flags(conn)

                elapsed = time.monotonic() - cycle_start
                log.info("Cycle complete in %.1fs", elapsed)

            except Exception as e:
                log.error("Cycle failed: %s", e, exc_info=True)

            # Periodic cleanup
            if datetime.now().minute == 0:
                cleanup_old_records(conn)

            elapsed = time.monotonic() - cycle_start
            sleep_time = max(0, FETCH_INTERVAL - elapsed)
            log.info("Sleeping %.0fs until next cycle", sleep_time)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        log.info("ETL pipeline stopped by user")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
