"""Reusable helpers for loading the trained FloodGuard ML artifact."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


MODEL_PATH = Path(__file__).resolve().with_name("model.joblib")


@lru_cache(maxsize=1)
def load_model_artifact(model_path: str | Path = MODEL_PATH) -> dict[str, Any]:
    """Load and cache the trained artifact; never retrain during prediction."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Trained model not found: {path}. Run ml/train_model.py first.")

    artifact = joblib.load(path)
    if not isinstance(artifact, dict) or "model" not in artifact or "feature_order" not in artifact:
        raise ValueError("Model artifact is invalid or missing required metadata.")
    return artifact


def predict_risk(
    water_level_cm: float,
    moisture_pct: float,
    rain_detected: bool,
    rise_rate_cm_min: float,
) -> str:
    """Return one risk label using the saved feature order."""
    artifact = load_model_artifact()
    features = pd.DataFrame(
        [[water_level_cm, moisture_pct, rain_detected, rise_rate_cm_min]],
        columns=artifact["feature_order"],
    )
    return str(artifact["model"].predict(features)[0])
