"""
Feature engineering for ParkGuideSG ML pipeline.
Pulls training data from the database, constructs feature matrix and target vector.
"""
import pandas as pd
from sqlalchemy import create_engine
from typing import Optional

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


def load_training_data(
    db_url: str,
    months: int = 3,
    carpark_limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Fetch training data from the database.

    Parameters
    ----------
    db_url : str
        PostgreSQL connection string.
    months : int
        Number of months of history to pull (1-3).
    carpark_limit : int or None
        Limit number of carparks for faster iteration (None = all).

    Returns
    -------
    pd.DataFrame with all feature columns + target column.
    """
    engine = create_engine(db_url)

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
          {carpark_clause}
        ORDER BY a.timestamp
    """

    df = pd.read_sql_query(query, engine)
    engine.dispose()

    # Ensure correct dtypes for LightGBM categorical handling
    df["carpark_id"] = df["carpark_id"].astype("category")
    df["weather_condition"] = df["weather_condition"].astype("category")
    df["is_weekend"] = df["is_weekend"].astype("int8")
    df["is_public_holiday"] = df["is_public_holiday"].astype("int8")
    df["hour"] = df["hour"].astype("int8")
    df["day_of_week"] = df["day_of_week"].astype("int8")

    return df


def split_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Split DataFrame into feature matrix X and target vector y."""
    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()
    return X, y
