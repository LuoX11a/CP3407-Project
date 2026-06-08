"""ML model inference engine with k-NN spatial proxy for non-EPS carparks."""

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import requests

# Allow importing from ml/ at project root
ML_DIR = Path(__file__).resolve().parents[3] / "ml"
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

SGT = timezone(timedelta(hours=8))
MODEL_PATH = Path(os.getenv("MODEL_PATH", "ml/model/carpark_predictor.joblib"))

_predictor = None
_predictor_meta: dict = {}

# LLM config
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

log = logging.getLogger(__name__)


def is_model_loaded() -> bool:
    return _predictor is not None


def get_model_meta() -> dict:
    return dict(_predictor_meta)


def load_model(path: str | Path | None = None) -> bool:
    global _predictor, _predictor_meta
    target = Path(path) if path else MODEL_PATH
    if not target.exists():
        log.warning("Model file not found: %s", target)
        return False
    try:
        from predict import ParkGuidePredictor
        _predictor = ParkGuidePredictor(str(target))
        _predictor_meta = {
            "trained_at": getattr(_predictor, "trained_at", "unknown"),
            "proxy_entries": len(getattr(_predictor, "proxy_map", {})),
            "non_eps_ids": sorted(getattr(_predictor, "non_eps_ids", set())),
        }
        log.info("Model loaded (trained %s, %d proxy entries)",
                 _predictor_meta["trained_at"], _predictor_meta["proxy_entries"])
        return True
    except Exception as e:
        log.error("Failed to load model: %s", e)
        return False


# ── LLM predictor ─────────────────────────────────────────

def _predict_with_llm(carparks: list[dict]) -> list[float]:
    """Use LLM to predict vacancy rates for a batch of carparks."""
    now = datetime.now(SGT)
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    lines = []
    for i, cp in enumerate(carparks):
        lines.append(
            f"{i+1}. {cp['carpark_id']} — "
            f"total_lots={cp.get('car_lots', cp.get('total_lots', 100))}, "
            f"currently_available={cp.get('available_lots', '?')}, "
            f"distance_from_user={cp.get('distance_m', '?')}m, "
            f"address={cp.get('address', '?')}"
        )

    prompt = f"""You are a parking demand analyst for Singapore HDB carparks.

Current conditions:
- Time: {now.strftime('%H:%M')} on {dow_names[now.weekday()]} ({"weekend" if now.weekday() >= 5 else "weekday"})
- Weather: {carparks[0].get('weather_condition', 'clear') if carparks else 'clear'}

Nearby carparks:
{chr(10).join(lines)}

For each carpark, predict the vacancy_rate (0.0 to 1.0). Consider:
- Work hours (9-18) on weekdays: office-area carparks fill up, residential areas stay empty
- Evenings and weekends: office areas empty out, residential areas fill up
- Rain reduces demand slightly
- Larger carparks tend to have more stable vacancy rates

Return ONLY a JSON array of numbers, one per carpark in the same order. No explanation.

Example response format:
[0.35, 0.72, 0.15, 0.88, 0.50]"""

    try:
        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 200,
            },
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        text = body["choices"][0]["message"]["content"].strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            preds = json.loads(text[start:end])
            return [round(max(0.0, min(1.0, float(p))), 3) for p in preds]
        else:
            log.warning("LLM returned non-JSON: %s", text[:200])
            return _heuristic_predict(carparks)
    except Exception as e:
        log.warning("LLM prediction failed: %s, using heuristic", e)
        return _heuristic_predict(carparks)


def _heuristic_predict(carparks: list[dict]) -> list[float]:
    """Rule-based fallback when both ML and LLM are unavailable."""
    now = datetime.now(SGT)
    hour = now.hour
    dow = now.weekday()

    results = []
    for cp in carparks:
        current = float(cp.get("vacancy_rate", cp.get("available_lots", 50) /
                         max(cp.get("car_lots", cp.get("total_lots", 100)), 1)) or 0.5)
        total = cp.get("car_lots", cp.get("total_lots", 100)) or 100
        base = current
        if total > 300:
            base = base * 0.7 + 0.5 * 0.3
        if dow < 5:
            if 7 <= hour <= 9:
                base -= 0.05
            elif 17 <= hour <= 19:
                base -= 0.05
        else:
            if 10 <= hour <= 16:
                base += 0.05
        results.append(round(max(0.0, min(1.0, base)), 3))
    return results


# ── Main predict ──────────────────────────────────────────

def predict(carparks: list[dict]) -> list[float]:
    """
    Predict vacancy rates for a list of carparks.
    Priority: ML model (with k-NN proxy for non-EPS) > LLM > heuristic.
    """
    if _predictor is not None:
        now = datetime.now(SGT)
        rows = []
        for cp in carparks:
            rows.append({
                "carpark_id": cp["carpark_id"],
                "hour": now.hour,
                "day_of_week": now.weekday(),
                "is_weekend": 1 if now.weekday() >= 5 else 0,
                "is_public_holiday": 0,
                "weather_condition": cp.get("weather_condition", "clear") or "clear",
                "total_lots": cp.get("car_lots", cp.get("total_lots", 100)),
            })

        df = pd.DataFrame(rows)
        preds = _predictor.predict_batch(df)
        return [round(float(p), 3) for p in preds]

    if LLM_API_KEY:
        log.info("Using LLM for prediction (%d carparks)", len(carparks))
        return _predict_with_llm(carparks)

    log.info("Using heuristic prediction (no ML model or LLM key)")
    return _heuristic_predict(carparks)
