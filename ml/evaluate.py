#!/usr/bin/env python
"""
Evaluate a trained model: cross-validation metrics, residual analysis, feature importance plot.
"""
import argparse
import os
import sys
import joblib
import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import load_training_data, split_xy, CATEGORICAL_COLS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def parse_args():
    p = argparse.ArgumentParser(description="Evaluate ParkGuideSG ML model")
    p.add_argument("model_path", help="Path to .joblib artifact")
    p.add_argument("--db-url", default=os.getenv("DATABASE_URL"),
                   help="PostgreSQL connection string (or set DATABASE_URL env var)")
    p.add_argument("--months", type=int, default=3)
    p.add_argument("--carpark-limit", type=int, default=None)
    return p.parse_args()


def main():
    args = parse_args()

    artifact = joblib.load(args.model_path)
    model = artifact["model"]
    log.info("Loaded model trained at %s", artifact.get("trained_at", "unknown"))
    log.info("Training rows: %d, CV MAE: %.4f",
             artifact.get("training_rows", 0),
             artifact["cv_metrics"]["mae"])

    # Load eval data (full window)
    log.info("Loading evaluation data...")
    df = load_training_data(args.db_url, months=args.months, carpark_limit=args.carpark_limit)
    X, y = split_xy(df)

    # Time-series hold-out: train on first 80%, test on last 20%
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # Re-fit on train portion for fair evaluation
    from lightgbm import LGBMRegressor
    eval_model = LGBMRegressor(
        n_estimators=300, max_depth=8, num_leaves=64, learning_rate=0.05,
        verbose=-1, random_state=42, force_col_wise=True,
    )
    eval_model.fit(X_train, y_train, categorical_feature=CATEGORICAL_COLS)

    y_pred = eval_model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    log.info("=== Hold-out Evaluation (last 20%%) ===")
    log.info("MAE:   %.4f  (avg prediction error in vacancy rate)", mae)
    log.info("RMSE:  %.4f  (penalizes large errors)", rmse)
    log.info("R²:    %.4f  (variance explained)", r2)

    # Residual analysis
    residuals = y_test.values - y_pred
    log.info("Residual mean: %.4f  std: %.4f", np.mean(residuals), np.std(residuals))

    # By hour
    by_hour = pd.DataFrame({"hour": X_test["hour"], "residual": np.abs(residuals)})
    hour_mae = by_hour.groupby("hour")["residual"].mean()
    worst_hour = hour_mae.idxmax()
    best_hour = hour_mae.idxmin()
    log.info("Best hour:  %d:00 (MAE=%.4f)", best_hour, hour_mae[best_hour])
    log.info("Worst hour: %d:00 (MAE=%.4f)", worst_hour, hour_mae[worst_hour])

    # By weather
    by_weather = pd.DataFrame({"weather": X_test["weather_condition"], "residual": np.abs(residuals)})
    weather_mae = by_weather.groupby("weather")["residual"].mean().sort_values(ascending=False)
    log.info("MAE by weather:")
    for w, m in weather_mae.items():
        log.info("  %-20s %.4f", w, m)


if __name__ == "__main__":
    main()
