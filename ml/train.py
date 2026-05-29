#!/usr/bin/env python
"""
Train the ParkGuideSG ML model.

Usage:
    python train.py --months 3 --output model/carpark_predictor.joblib
    python train.py --months 1 --carpark-limit 100 --output model/test.joblib
"""
import argparse
import os
import sys
import joblib
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error
import lightgbm as lgb

# Allow importing features.py from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import load_training_data, split_xy, CATEGORICAL_COLS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# Default database URL — override with env var or CLI
DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_yUEZOnYd93gw@ep-crimson-bread-ao6pswy8.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require",
)


def parse_args():
    p = argparse.ArgumentParser(description="Train ParkGuideSG parking predictor")
    p.add_argument("--db-url", default=DEFAULT_DB_URL, help="PostgreSQL connection string")
    p.add_argument("--months", type=int, default=3, help="Training data window in months")
    p.add_argument("--carpark-limit", type=int, default=None,
                   help="Limit carparks for fast experiments")
    p.add_argument("--output", default="model/carpark_predictor.joblib",
                   help="Output path for serialized model")
    p.add_argument("--n-estimators", type=int, default=300, help="Number of boosting rounds")
    p.add_argument("--max-depth", type=int, default=8, help="Max tree depth")
    p.add_argument("--num-leaves", type=int, default=64, help="Max leaves per tree")
    p.add_argument("--lr", type=float, default=0.05, help="Learning rate")
    p.add_argument("--early-stopping", type=int, default=50, help="Early stopping rounds")
    return p.parse_args()


def main():
    args = parse_args()
    log.info("Loading training data (months=%d)...", args.months)
    df = load_training_data(args.db_url, months=args.months, carpark_limit=args.carpark_limit)
    X, y = split_xy(df)

    log.info("Training set: %d rows, %d features", len(X), X.shape[1])
    log.info("Target: mean=%.3f, std=%.3f, min=%.3f, max=%.3f",
             y.mean(), y.std(), y.min(), y.max())
    log.info("Carpark count: %d, weather conditions: %d",
             X["carpark_id"].nunique(), X["weather_condition"].nunique())

    # Time-series cross-validation
    tscv = TimeSeriesSplit(n_splits=3)
    cv_scores = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = lgb.LGBMRegressor(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            num_leaves=args.num_leaves,
            learning_rate=args.lr,
            verbose=-1,
            random_state=42,
            force_col_wise=True,
        )

        model.fit(
            X_train, y_train,
            categorical_feature=CATEGORICAL_COLS,
            eval_set=[(X_val, y_val)],
            eval_metric="mae",
            callbacks=[lgb.early_stopping(args.early_stopping, verbose=False)],
        )

        y_pred = model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        cv_scores.append({"fold": fold + 1, "mae": mae, "rmse": rmse, "n_trees": model.best_iteration_})
        log.info("Fold %d: MAE=%.4f  RMSE=%.4f  trees=%d", fold + 1, mae, rmse, model.best_iteration_)

    # Summary
    avg_mae = np.mean([s["mae"] for s in cv_scores])
    avg_rmse = np.mean([s["rmse"] for s in cv_scores])
    log.info("CV average: MAE=%.4f  RMSE=%.4f", avg_mae, avg_rmse)

    # Train final model on all data
    log.info("Training final model on full dataset...")
    final_model = lgb.LGBMRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        num_leaves=args.num_leaves,
        learning_rate=args.lr,
        verbose=-1,
        random_state=42,
        force_col_wise=True,
    )
    final_model.fit(X, y, categorical_feature=CATEGORICAL_COLS)

    # Save model + metadata
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    artifact = {
        "model": final_model,
        "feature_cols": X.columns.tolist(),
        "categorical_cols": CATEGORICAL_COLS,
        "cv_metrics": {"mae": avg_mae, "rmse": avg_rmse, "folds": cv_scores},
        "training_rows": len(X),
        "training_months": args.months,
        "trained_at": datetime.now().isoformat(),
    }
    joblib.dump(artifact, args.output)
    log.info("Model saved to %s", args.output)

    # Feature importance
    importance = pd.DataFrame({
        "feature": X.columns,
        "gain": final_model.booster_.feature_importance(importance_type="gain"),
    }).sort_values("gain", ascending=False)
    log.info("Feature importance:\n%s", importance.to_string(index=False))


if __name__ == "__main__":
    main()
