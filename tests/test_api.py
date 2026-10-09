"""Integration tests for the FloodGuard FastAPI backend."""

from fastapi.testclient import TestClient

from backend.main import app
from simulator.sensor_simulator import generate_reading
import numpy as np


client = TestClient(app)


def test_root_identifies_the_project() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "FloodGuard API"}


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_returns_risk_probabilities_and_input() -> None:
    payload = {"water_level_cm": 55, "moisture_pct": 72, "rain_detected": False, "rise_rate_cm_min": 6}
    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["risk"] in {"LOW", "MODERATE", "HIGH"}
    assert set(body) == {"risk", "probabilities", "input"}
    assert set(body["probabilities"]) == {"LOW", "MODERATE", "HIGH"}
    assert body["input"] == {key: float(value) for key, value in payload.items()}
    assert "moisture_pct" in body["input"] and "rain_detected" in body["input"]


def test_predict_rejects_negative_values() -> None:
    response = client.post(
        "/predict",
        json={"water_level_cm": -1, "moisture_pct": 20, "rain_detected": False, "rise_rate_cm_min": 1},
    )

    assert response.status_code == 422


def test_predict_rejects_missing_required_field() -> None:
    response = client.post("/predict", json={"water_level_cm": 20, "moisture_pct": 5})

    assert response.status_code == 422


def test_predict_requires_rain_detected_flag() -> None:
    response = client.post(
        "/predict",
        json={"water_level_cm": 20, "moisture_pct": 5, "rise_rate_cm_min": 1},
    )
    assert response.status_code == 422


def test_history_and_latest_expose_api_predictions() -> None:
    payload = {"water_level_cm": 55, "moisture_pct": 72, "rain_detected": False, "rise_rate_cm_min": 6}
    client.post("/predict", json=payload)

    latest = client.get("/latest")
    history = client.get("/history")

    assert latest.status_code == 200
    assert latest.json()["input"] == {key: float(value) for key, value in payload.items()}
    assert "timestamp" in latest.json()
    assert history.status_code == 200
    assert history.json()[0] == latest.json()


def test_dashboard_is_served_by_fastapi() -> None:
    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert "FloodGuard" in response.text


def test_predict_rejects_moisture_above_percent_range() -> None:
    response = client.post("/predict", json={"water_level_cm": 20, "moisture_pct": 101, "rain_detected": True, "rise_rate_cm_min": 1})
    assert response.status_code == 422


def test_predict_rejects_rain_flag_inconsistent_with_moisture() -> None:
    response = client.post("/predict", json={"water_level_cm": 20, "moisture_pct": 80, "rain_detected": False, "rise_rate_cm_min": 1})
    assert response.status_code == 422


def test_simulator_drainage_scenarios_match_api_contract() -> None:
    rng = np.random.default_rng(42)
    scenarios = (
        "normal_drainage",
        "rising_water",
        "rapid_water_rise",
        "high_wetness_rising_water",
        "potential_storm_drain_overflow",
    )
    for scenario in scenarios:
        reading = generate_reading(scenario, 4, rng)
        assert set(reading) == {"water_level_cm", "moisture_pct", "rain_detected", "rise_rate_cm_min"}
        assert reading["rain_detected"] is (reading["moisture_pct"] >= 75)
        response = client.post("/predict", json=reading)
        assert response.status_code == 200
        assert response.json()["input"] == reading


def test_legacy_simulator_scenarios_remain_supported() -> None:
    rng = np.random.default_rng(42)
    for scenario in ("low", "moderate", "high", "rapid_rise"):
        reading = generate_reading(scenario, 4, rng)
        assert client.post("/predict", json=reading).status_code == 200
