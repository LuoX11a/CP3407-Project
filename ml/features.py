"""
Feature engineering for ParkGuideSG ML pipeline.
Pulls training data from the database, constructs feature matrix and target vector.
Identifies non-EPS carparks (always-zero availability) and builds k-NN spatial proxy map.
"""
import math
import pandas as pd
from sqlalchemy import create_engine
from typing import Optional, Tuple

# Columns used as features
FEATURE_COLS = [
    "carpark_id",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_public_holiday",
    "weather_condition",
    "total_lots",
]

CATEGORICAL_COLS = ["carpark_id", "weather_condition"]

TARGET_COL = "vacancy_rate"

# Default k for nearest-neighbour proxy
PROXY_K = 3


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance in metres between two (lat, lng) points."""
    r = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def identify_non_eps_carparks(db_url: str, before_date: str | None = None) -> list[str]:
    """Return carpark_ids that have always-zero available_lots (non-EPS carparks).

    Parameters
    ----------
    db_url : str
        PostgreSQL connection string.
    before_date : str or None
        Only consider data before this date (e.g. '2026-06-07') to exclude
        synthetic/filled data. If None, uses all data.
    """
    engine = create_engine(db_url)
    date_filter = ""
    params = {}
    if before_date:
        date_filter = "AND a.timestamp < %(before_date)s"
        params["before_date"] = before_date
    query = f"""
        SELECT c.carpark_id
        FROM availability_logs a
        JOIN carparks c ON a.carpark_id = c.carpark_id
        WHERE c.lat != 0
          {date_filter}
        GROUP BY c.carpark_id
        HAVING MAX(a.available_lots) = 0
    """
    df = pd.read_sql_query(query, engine, params=params)
    engine.dispose()
    return df["carpark_id"].tolist()


def build_proxy_map(
    db_url: str,
    non_eps_ids: list[str],
    k: int = PROXY_K,
) -> dict:
    """
    For each non-EPS carpark, find the k nearest EPS carparks and compute
    distance-based weights. Returns a proxy map:
        {non_eps_id: {"neighbors": [(eps_id, distance_m), ...], "weights": [w1, ...]}}
    """
    if not non_eps_ids:
        return {}

    engine = create_engine(db_url)

    # EPS carparks: those with at least some availability data
    non_eps_tuple = tuple(non_eps_ids)
    query = f"""
        SELECT c.carpark_id, c.lat, c.lng
        FROM carparks c
        WHERE c.lat != 0
          AND c.carpark_id NOT IN %(non_eps)s
    """
    eps_df = pd.read_sql_query(query, engine, params={"non_eps": non_eps_tuple})
    engine.dispose()

    eps_list = [(r.carpark_id, r.lat, r.lng) for r in eps_df.itertuples()]

    # For non-EPS carparks, we need their lat/lng. Query separately or use
    # the carparks table. We'll look them up from the training data load step,
    # but for now build from carparks table.
    engine = create_engine(db_url)
    non_eps_query = f"""
        SELECT carpark_id, lat, lng
        FROM carparks
        WHERE carpark_id IN %(ids)s
    """
    non_eps_locs = pd.read_sql_query(
        non_eps_query, engine, params={"ids": non_eps_tuple}
    )
    engine.dispose()
    loc_lookup = {r.carpark_id: (r.lat, r.lng) for r in non_eps_locs.itertuples()}

    proxy_map = {}
    for nid in non_eps_ids:
        loc = loc_lookup.get(nid)
        if loc is None:
            continue
        nlat, nlng = loc

        distances = []
        for eid, elat, elng in eps_list:
            d = _haversine(nlat, nlng, elat, elng)
            distances.append((eid, d))

        distances.sort(key=lambda x: x[1])
        top_k = distances[:k]

        # Weight = 1 / distance; guard against zero distance
        weights = [1.0 / max(d[1], 1.0) for d in top_k]
        total_w = sum(weights)
        weights = [w / total_w for w in weights]

        proxy_map[nid] = {
            "neighbors": [(d[0], d[1]) for d in top_k],
            "weights": weights,
        }

    return proxy_map


def load_training_data(
    db_url: str,
    months: int = 3,
    carpark_limit: Optional[int] = None,
    exclude_ids: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Fetch training data from the database.

    Parameters
    ----------
    db_url : str
        PostgreSQL connection string.
    months : int
        Number of months of history to pull.
    carpark_limit : int or None
        Limit number of carparks for faster iteration (None = all).
    exclude_ids : list[str] or None
        Carpark IDs to exclude from training (e.g. non-EPS carparks).

    Returns
    -------
    pd.DataFrame with all feature columns + target column.
    """
    engine = create_engine(db_url)

    exclude_clause = ""
    if exclude_ids:
        exclude_tuple = tuple(exclude_ids)
        exclude_clause = f"AND a.carpark_id NOT IN %(exclude)s"

    carpark_clause = ""
    if carpark_limit:
        carpark_clause = (
            f"AND a.carpark_id IN ("
            f"  SELECT carpark_id FROM carparks WHERE lat != 0 LIMIT {carpark_limit}"
            f")"
        )

    query = f"""
        SELECT
            a.carpark_id,
            a.hour,
            a.day_of_week,
            a.is_weekend::int,
            a.is_public_holiday::int,
            COALESCE(a.weather_condition, 'unknown') AS weather_condition,
            c.car_lots AS total_lots,
            a.vacancy_rate
        FROM availability_logs a
        JOIN carparks c ON a.carpark_id = c.carpark_id
        WHERE a.timestamp >= now() - INTERVAL '{months} months'
          AND c.lat != 0
          {exclude_clause}
          {carpark_clause}
        ORDER BY a.timestamp
    """

    params = {}
    if exclude_ids:
        params["exclude"] = exclude_tuple
    df = pd.read_sql_query(query, engine, params=params)
    engine.dispose()

    # Ensure correct dtypes for LightGBM categorical handling
    df["carpark_id"] = df["carpark_id"].astype("category")
    df["weather_condition"] = df["weather_condition"].astype("category")
    df["is_weekend"] = df["is_weekend"].astype("int8")
    df["is_public_holiday"] = df["is_public_holiday"].astype("int8")
    df["hour"] = df["hour"].astype("int8")
    df["day_of_week"] = df["day_of_week"].astype("int8")

    return df


def split_xy(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Split DataFrame into feature matrix X and target vector y."""
    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()
    return X, y
