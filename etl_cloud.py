"""
ParkGuideSG - Cloud ETL Pipeline (GitHub Actions)
Single-cycle mode: fetch once, insert, then exit.
Triggered every 30 minutes by GitHub Actions schedule.

Requirements: pip install psycopg2-binary requests pandas pyproj
"""

import os
import time
import logging
from datetime import datetime
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

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
NEA_TEMP_URL = "https://api.data.gov.sg/v1/environment/air-temperature"
NEA_HUMID_URL = "https://api.data.gov.sg/v1/environment/relative-humidity"
NEA_RAIN_URL = "https://api.data.gov.sg/v1/environment/rainfall"

# Retry config
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, exponential

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

# Strip channel_binding=require for psycopg2/libpq compatibility.
# Neon's connection string includes this parameter, but psycopg2's
# underlying libpq does not support it.
DATABASE_URL = DATABASE_URL.replace("&channel_binding=require", "").replace(
    "?channel_binding=require&", "?"
).replace("?channel_binding=require", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

svy21_to_wgs84 = Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------

HARD_TIMEOUT = 120  # seconds — absolute wall-clock deadline per fetch

def _fetch_with_hard_timeout(fn, *args, timeout=HARD_TIMEOUT, **kwargs):
    """Run fn in a thread and enforce a hard wall-clock timeout.

    requests timeout=(connect, read) is per-socket-operation, not total.
    If the server dribbles bytes slowly enough, the total call can exceed
    the configured timeout.  This wrapper kills the whole attempt after
    `timeout` seconds regardless.
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeoutError:
            log.error("Hard timeout (%ds) exceeded – aborting fetch", timeout)
            raise TimeoutError(
                f"Fetch did not complete within {timeout} seconds"
            )


def with_retry(fn, max_retries=MAX_RETRIES, backoff=RETRY_BACKOFF):
    """Decorator: retry on HTTP or connection errors with exponential backoff."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except (requests.RequestException, Exception) as e:
                last_exc = e
                if attempt < max_retries:
                    wait = backoff ** attempt
                    log.warning(
                        "%s failed (attempt %d/%d), retrying in %ds: %s",
                        fn.__name__, attempt, max_retries, wait, e,
                    )
                    time.sleep(wait)
        log.error("%s failed after %d attempts: %s", fn.__name__, max_retries, last_exc)
        raise last_exc
    return wrapper


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def _fetch_json(url, connect_timeout=10, read_timeout=90):
    """Fetch JSON from URL. (connect, read) timeout prevents TCP hangs."""
    resp = requests.get(
        url,
        timeout=(connect_timeout, read_timeout),
        headers={"User-Agent": "ParkGuideSG-ETL/1.0"},
    )
    resp.raise_for_status()
    return resp.json()


def fetch_carpark_availability() -> list[dict]:
    """Fetch live HDB carpark lot counts. Retries on failure.

    Wrapped in a hard 120 s wall-clock timeout.  The requests timeout
    tuple (connect=10s, read=90s) handles the socket level; the hard
    timeout catches the case where the server sends data slowly enough
    to never trigger the socket timeout.
    """
    log.info("Calling Data.gov.sg carpark-availability API (timeout: connect=10s, read=90s, hard=120s)...")
    data = with_retry(
        lambda: _fetch_with_hard_timeout(_fetch_json, HDB_API_URL)
    )()
    log.info("API response received, parsing %d items...", len(data.get("items", [])))

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
    """Fetch NEA 2-hour weather forecast. Retries on failure."""
    data = with_retry(lambda: _fetch_with_hard_timeout(_fetch_json, NEA_API_URL))()

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
    data = with_retry(lambda: _fetch_json(url))()
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

    forecast_areas: list of {station_id, name, lat, lng} from fetch_weather()
    Returns: dict[area_name, {temperature, humidity, rainfall}]
    """
    try:
        temp_readings, temp_stations = with_retry(_fetch_measurement)(NEA_TEMP_URL)
        hum_readings, hum_stations = with_retry(_fetch_measurement)(NEA_HUMID_URL)
        rain_readings, rain_stations = with_retry(_fetch_measurement)(NEA_RAIN_URL)
    except Exception:
        log.warning("Weather measurement APIs failed, proceeding without measurements")
        return {}

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


# ---------------------------------------------------------------------------
# ETL operations
# ---------------------------------------------------------------------------

def ensure_stations_present(conn, stations: list[dict]):
    if not stations:
        return
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
    """Insert availability records. Includes weather condition from the fetch."""
    if not records:
        return 0
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
    return len(values)


def load_weather_records(conn, records: list[dict], measurements: dict = None):
    if not records:
        return 0
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
        seen = set()
        values = []
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
    return len(values)


def update_weather_on_availability(conn):
    """Backfill weather_condition from nearest weather record within +/- 2 hours."""
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
    if cur.rowcount:
        log.info("Weather backfill: %d rows updated", cur.rowcount)


def update_public_holiday_flags(conn):
    """Mark availability records that fall on a public holiday."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE availability_logs a
            SET is_public_holiday = TRUE
            FROM public_holidays h
            WHERE DATE(a.timestamp AT TIME ZONE 'Asia/Singapore') = h.date
              AND a.is_public_holiday = FALSE
              AND a.timestamp >= now() - INTERVAL '7 days'
            """
        )
    conn.commit()


def cleanup_old_records(conn):
    """Remove availability logs older than 90 days."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM availability_logs WHERE timestamp < now() - INTERVAL '90 days'"
        )
    conn.commit()
    if cur.rowcount:
        log.info("Cleaned up %d old records", cur.rowcount)


# ---------------------------------------------------------------------------
# Main — each step independent, failures in non-critical steps don't abort
# ---------------------------------------------------------------------------

def main():
    log.info("=== ParkGuideSG Cloud ETL Cycle ===")
    cycle_start = time.monotonic()

    conn = psycopg2.connect(DATABASE_URL)
    log.info("Connected to cloud database")

    # Track per-step status for summary
    status = {
        "weather_forecast": False,
        "weather_measurements": False,
        "carpark": False,
        "weather_backfill": False,
        "holiday_flags": False,
        "cleanup": False,
    }

    # ── Step 1: Weather (non-critical — failure won't block carpark data) ──
    try:
        stations, weather_records = fetch_weather()
        ensure_stations_present(conn, stations)
        measurements = fetch_weather_measurements(stations)
        load_weather_records(conn, weather_records, measurements)
        log.info("Weather OK: %d stations, %d forecast records",
                 len(stations), len(weather_records))
        status["weather_forecast"] = True
        if measurements:
            status["weather_measurements"] = True
    except Exception as e:
        log.error("Weather step failed (non-critical): %s", e, exc_info=True)

    # ── Step 2: HDB availability (CRITICAL) ──
    try:
        log.info("Step 2: HDB carpark availability...")
        carpark_records = fetch_carpark_availability()
        log.info("Fetched %d raw carpark records from API", len(carpark_records))
        n_carpark = load_carpark_availability(conn, carpark_records)

        # Validate: expect ~2000 carparks; warn if significantly fewer
        unique_cps = len(set(r["carpark_id"] for r in carpark_records))
        if unique_cps < 500:
            log.warning(
                "Low carpark count: %d unique carparks, %d records — API may be partial",
                unique_cps, len(carpark_records),
            )
        else:
            log.info("Carpark OK: %d unique, %d records", unique_cps, n_carpark)

        status["carpark"] = n_carpark > 0
    except Exception as e:
        log.critical("CRITICAL: carpark fetch failed: %s", e, exc_info=True)

    # ── Step 3: Backfill weather on availability ──
    if status["weather_forecast"]:
        try:
            update_weather_on_availability(conn)
            status["weather_backfill"] = True
        except Exception as e:
            log.warning("Weather backfill failed (non-critical): %s", e)

    # ── Step 4: Holiday flags ──
    try:
        update_public_holiday_flags(conn)
        status["holiday_flags"] = True
    except Exception as e:
        log.warning("Holiday flag update failed (non-critical): %s", e)

    # ── Step 5: Periodic cleanup (first cycle of each hour) ──
    if datetime.now().minute < 30:
        try:
            cleanup_old_records(conn)
            status["cleanup"] = True
        except Exception as e:
            log.warning("Cleanup failed (non-critical): %s", e)

    conn.close()

    elapsed = time.monotonic() - cycle_start

    # ── Summary ──
    ok = sum(1 for v in status.values() if v)
    total = len(status)
    log.info("=== Cycle complete in %.1fs | %d/%d steps OK ===", elapsed, ok, total)
    for step, passed in status.items():
        marker = "OK" if passed else "FAIL"
        log.info("  [%s] %s", marker, step)

    # Exit non-zero if critical step (carpark) failed — lets GitHub Actions detect failures
    if not status["carpark"]:
        log.critical("CRITICAL: carpark data fetch failed — returning exit code 1")
        exit(1)


if __name__ == "__main__":
    main()
