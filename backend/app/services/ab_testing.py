"""
Model A/B testing framework.

Routes prediction requests to model variant A (production) or B (candidate)
based on a stable hash of user/session identifiers.  Results are logged for
offline comparison — no real-time dashboard dependency.

Usage in recommend router:
    from app.services.ab_testing import get_model_variant, log_prediction

    variant, model = get_model_variant(user_id_hash=request.client.host)
    prediction = model.predict(features)
    log_prediction(variant, carpark_id, actual_vacancy, predicted_vacancy)
"""

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Tuple, Any

log = logging.getLogger(__name__)

# Traffic split: fraction routed to model B (0.0 = all A, 1.0 = all B)
B_TRAFFIC_FRACTION = 0.20  # 20% to candidate model B

# In-memory log buffer (flushed to DB periodically in production)
_prediction_log: list[dict] = []


def get_model_variant(identifier: str) -> Tuple[str, int]:
    """Return ('A', bucket) or ('B', bucket) for a given identifier.

    Uses a stable MD5 hash of the identifier so the same user always
    gets the same variant (sticky assignment).
    """
    h = hashlib.md5(identifier.encode()).hexdigest()
    bucket = int(h[:8], 16) % 100
    if bucket < int(B_TRAFFIC_FRACTION * 100):
        return "B", bucket
    return "A", bucket


def log_prediction(
    variant: str,
    carpark_id: str,
    actual_vacancy: float,
    predicted_vacancy: float,
    model_version: str = "v1",
):
    """Record a prediction for offline A/B metric comparison."""
    _prediction_log.append({
        "variant": variant,
        "carpark_id": carpark_id,
        "actual": actual_vacancy,
        "predicted": predicted_vacancy,
        "model_version": model_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def get_ab_stats() -> dict:
    """Return current A/B comparison stats from the in-memory log."""
    if not _prediction_log:
        return {"total": 0, "a_count": 0, "b_count": 0}

    a_preds = [p for p in _prediction_log if p["variant"] == "A"]
    b_preds = [p for p in _prediction_log if p["variant"] == "B"]

    def mae(preds):
        if not preds:
            return 0
        return sum(abs(p["actual"] - p["predicted"]) for p in preds) / len(preds)

    return {
        "total": len(_prediction_log),
        "a_count": len(a_preds),
        "b_count": len(b_preds),
        "a_mae": round(mae(a_preds), 4),
        "b_mae": round(mae(b_preds), 4),
    }
