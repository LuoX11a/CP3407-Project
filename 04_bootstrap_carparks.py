"""
One-shot script: fetch HDB Carpark Information from data.gov.sg
and populate the carparks table with address + coordinates.
"""
import psycopg2
import psycopg2.extras
import requests
from pyproj import Transformer

API_URL = "https://data.gov.sg/api/action/datastore_search"
RESOURCE_ID = "d_23f946fa557947f93a8043bbef41dd09"

DB_CONFIG = {
    "host": "localhost",
    "dbname": "parkguidesg",
    "user": "postgres",
    "password": "parkguide",
}

svy21_to_wgs84 = Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)


def fetch_all_records():
    """Paginate through all records from the datastore API."""
    records = []
    offset = 0
    limit = 500
    while True:
        params = {"resource_id": RESOURCE_ID, "limit": limit, "offset": offset}
        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        batch = data["result"]["records"]
        records.extend(batch)
        print(f"Fetched {len(records)} / {data['result']['total']} records")
        if len(batch) < limit:
            break
        offset += limit
    return records


def main():
    print("Fetching HDB Carpark Information...")
    records = fetch_all_records()
    print(f"Total: {len(records)} records")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    sql = """
        INSERT INTO carparks (carpark_id, address, car_lots, svy21_x, svy21_y, lat, lng)
        VALUES %s
        ON CONFLICT (carpark_id) DO UPDATE
        SET address = EXCLUDED.address,
            svy21_x = EXCLUDED.svy21_x,
            svy21_y = EXCLUDED.svy21_y,
            lat      = EXCLUDED.lat,
            lng      = EXCLUDED.lng
    """

    updated = 0
    skipped = 0
    inserted = 0
    values = []

    for r in records:
        cp_id = r["car_park_no"]
        address = r["address"]
        x_str = r.get("x_coord", "0")
        y_str = r.get("y_coord", "0")

        try:
            x = float(x_str) if x_str else 0.0
            y = float(y_str) if y_str else 0.0
        except (ValueError, TypeError):
            x, y = 0.0, 0.0

        if x == 0 or y == 0:
            skipped += 1
            continue

        car_lots = 0  # the static dataset doesn't have lot counts; API provides them

        lng, lat = svy21_to_wgs84.transform(x, y)

        values.append((cp_id, address, car_lots, x, y, round(lat, 8), round(lng, 8)))

    # Batch upsert
    psycopg2.extras.execute_values(cur, sql, values)
    conn.commit()

    print(f"Upserted: {len(values)}, skipped (no coords): {skipped}")
    print("Done!")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
