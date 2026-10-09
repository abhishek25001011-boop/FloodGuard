"""Request and response models for local storm-drain monitoring."""

from pydantic import BaseModel, Field, model_validator


WETNESS_DETECTION_THRESHOLD_PCT = 75.0


class SensorData(BaseModel):
    """Validated readings from one monitored drain or low-lying area."""

    water_level_cm: float = Field(ge=0, le=1_000, allow_inf_nan=False, description="Water level in centimetres")
    moisture_pct: float = Field(ge=0, le=100, allow_inf_nan=False, description="Calibrated wetness from 0% dry to 100% wet")
    rain_detected: bool = Field(description="Wetness threshold flag; not rainfall intensity in mm/hour")
    rise_rate_cm_min: float = Field(ge=0, le=50, allow_inf_nan=False, description="Water-level rise rate in centimetres per minute")

    @model_validator(mode="after")
    def rain_flag_matches_moisture(self) -> "SensorData":
        expected = self.moisture_pct >= WETNESS_DETECTION_THRESHOLD_PCT
        if self.rain_detected != expected:
            raise ValueError("rain_detected must match the 75% moisture wetness threshold")
        return self


class PredictionResponse(BaseModel):
    """Local storm-drain overflow risk and the validated source readings."""

    risk: str
    probabilities: dict[str, float]
    input: SensorData


class StoredPrediction(PredictionResponse):
    """A prediction retained in memory for the dashboard."""

    timestamp: str
