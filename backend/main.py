"""FastAPI prediction service for local storm-drain overflow monitoring."""

from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd

from backend.schemas import PredictionResponse, SensorData, StoredPrediction
from ml.model_loader import load_model_artifact


EXPECTED_FEATURE_ORDER = ["water_level_cm", "moisture_pct", "rain_detected", "rise_rate_cm_min"]
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
RECENT_PREDICTIONS: deque[StoredPrediction] = deque(maxlen=20)

app = FastAPI(title="FloodGuard API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    """Identify the service."""
    return {"message": "FloodGuard API"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a lightweight service-health response."""
    return {"status": "ok"}


@app.get("/latest", response_model=StoredPrediction)
def latest_prediction() -> StoredPrediction:
    """Return the newest API-produced prediction for the dashboard."""
    if not RECENT_PREDICTIONS:
        raise HTTPException(status_code=404, detail="No sensor readings have been received yet.")
    return RECENT_PREDICTIONS[0]


@app.get("/history", response_model=list[StoredPrediction])
def prediction_history() -> list[StoredPrediction]:
    """Return up to 20 newest-first predictions retained in memory."""
    return list(RECENT_PREDICTIONS)


@app.post("/predict", response_model=PredictionResponse)
def predict(sensor_data: SensorData) -> PredictionResponse:
    """Return local drainage overflow risk for validated sensor data."""
    try:
        artifact = load_model_artifact()
        feature_order = artifact["feature_order"]
        if feature_order != EXPECTED_FEATURE_ORDER:
            raise ValueError("The trained model has an unexpected feature order.")

        model = artifact["model"]
        # A one-row DataFrame is used so model columns always match saved training order.
        input_frame = sensor_data.model_dump()
        features = pd.DataFrame([[input_frame[name] for name in feature_order]], columns=feature_order)
        risk = str(model.predict(features)[0])
        probabilities = {
            str(label): round(float(probability), 4)
            for label, probability in zip(model.classes_, model.predict_proba(features)[0], strict=True)
        }
    except Exception as error:
        raise HTTPException(status_code=503, detail="Prediction model is unavailable.") from error

    prediction = PredictionResponse(risk=risk, probabilities=probabilities, input=sensor_data)
    RECENT_PREDICTIONS.appendleft(
        StoredPrediction(
            **prediction.model_dump(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    return prediction


app.mount("/dashboard", StaticFiles(directory=FRONTEND_DIR, html=True), name="dashboard")
