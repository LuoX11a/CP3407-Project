"""
ParkGuideSG inference module.
Handles prediction for both EPS carparks (direct model) and
non-EPS carparks (k-NN spatial proxy via neighbouring EPS carparks).

Usage:
    from predict import ParkGuidePredictor

    predictor = ParkGuidePredictor("model/carpark_predictor.joblib")
    pred = predictor.predict_single("A11", hour=18, day_of_week=1,
                                     is_weekend=False, is_public_holiday=False,
                                     weather_condition="partly cloudy", total_lots=410)
"""
import logging
import joblib
import pandas as pd
import numpy as np

log = logging.getLogger(__name__)


class ParkGuidePredictor:
    """Loads a trained model artifact and serves predictions."""

    def __init__(self, model_path: str):
        artifact = joblib.load(model_path)
        self.model = artifact["model"]
        self.feature_cols = artifact["feature_cols"]
        self.categorical_cols = artifact["categorical_cols"]
        self.non_eps_ids = set(artifact.get("non_eps_ids", []))
        self.proxy_map = artifact.get("proxy_map", {})
        self.trained_at = artifact.get("trained_at", "unknown")
        log.info(
            "Loaded model trained at %s | EPS carparks: %d | proxy entries: %d",
            self.trained_at,
            len(self.feature_cols),  # approximate
            len(self.proxy_map),
        )

    def predict_single(
        self,
        carpark_id: str,
        hour: int,
        day_of_week: int,
        is_weekend: bool,
        is_public_holiday: bool,
        weather_condition: str,
        total_lots: int,
    ) -> float:
        """Predict vacancy_rate (0-1) for a single carpark at given time/weather."""
        result = self.predict_batch(pd.DataFrame([{
            "carpark_id": carpark_id,
            "hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "is_public_holiday": is_public_holiday,
            "weather_condition": weather_condition,
            "total_lots": total_lots,
        }]))
        return float(result[0])

    def predict_batch(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict vacancy_rate for a batch of records.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain columns matching FEATURE_COLS:
            carpark_id, hour, day_of_week, is_weekend, is_public_holiday,
            weather_condition, total_lots.
            is_weekend and is_public_holiday can be bool or int (0/1).

        Returns
        -------
        np.ndarray of predicted vacancy_rate values (0-1).
        """
        df = df.copy()

        # Normalise bool -> int
        for col in ("is_weekend", "is_public_holiday"):
            if col in df.columns and df[col].dtype == bool:
                df[col] = df[col].astype(int)

        # Split into EPS and non-EPS rows
        eps_mask = ~df["carpark_id"].isin(self.non_eps_ids)
        non_eps_mask = ~eps_mask

        predictions = np.empty(len(df), dtype=float)

        # Direct prediction for EPS carparks
        if eps_mask.any():
            eps_df = df.loc[eps_mask, self.feature_cols].copy()
            eps_df["carpark_id"] = eps_df["carpark_id"].astype("category")
            eps_df["weather_condition"] = eps_df["weather_condition"].astype("category")
            predictions[eps_mask.values] = self.model.predict(eps_df)

        # Proxy prediction for non-EPS carparks
        if non_eps_mask.any():
            non_eps_df = df.loc[non_eps_mask]
            for i, idx in enumerate(non_eps_df.index):
                row = non_eps_df.loc[idx]
                predictions[idx] = self._proxy_predict(row)

        return predictions

    def _proxy_predict(self, row: pd.Series) -> float:
        """
        Predict vacancy_rate for a non-EPS carpark using k-NN spatial proxy.
        For each neighbouring EPS carpark, we construct a feature row with the
        neighbour's carpark_id and the same time/weather context, then take
        the weighted average of the model's predictions.
        """
        nid = row["carpark_id"]
        proxy_info = self.proxy_map.get(nid)

        if proxy_info is None:
            # Fallback: return global neutral prediction
            log.warning("No proxy entry for %s, returning 0.5", nid)
            return 0.5

        neighbors = proxy_info["neighbors"]
        weights = proxy_info["weights"]

        # Build feature rows for each neighbour
        rows = []
        for eid, _ in neighbors:
            r = row.copy()
            r["carpark_id"] = eid
            rows.append(r)

        neighbor_df = pd.DataFrame(rows)
        neighbor_df = neighbor_df[self.feature_cols].copy()
        neighbor_df["carpark_id"] = neighbor_df["carpark_id"].astype("category")
        neighbor_df["weather_condition"] = neighbor_df["weather_condition"].astype("category")

        neighbor_preds = self.model.predict(neighbor_df)
        weighted_pred = float(np.dot(neighbor_preds, weights))

        return weighted_pred
