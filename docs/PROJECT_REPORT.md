# FloodGuard - Smart Storm-Drain Monitoring

## Abstract

FloodGuard is a local storm-drain and low-lying-area monitoring prototype for communicating possible overflow risk clearly and early. It combines water level, moisture-derived wetness (not rainfall rate), and water-level rise rate to classify a reading as `LOW`, `MODERATE`, or `HIGH` drainage risk. A FastAPI service applies a trained Random Forest model; a hardware-compatible simulator demonstrates the data flow; and a live dashboard presents the result. FloodGuard is based on synthetic development data, not an official warning system or city-wide forecast.

## Problem Statement

Monitoring only the current water level at a storm drain can provide a late warning. A level may still appear moderate while high soil wetness and a rapid upward trend indicate that local drainage conditions are deteriorating.

## Proposed Solution

FloodGuard uses three sensor measurements plus a wetness flag derived from the moisture sensor:

- Water level (`water_level_cm`)
- Soil moisture wetness (`moisture_pct`, 0% dry to 100% wet) and `rain_detected` (true at 75% wetness; not rainfall intensity or mm/hour)
- Rate of water-level rise (`rise_rate_cm_min`)

The model produces one of three understandable risk classes: `LOW`, `MODERATE`, or `HIGH`. The dashboard displays the latest metrics, class probabilities, risk state, and recent trend history.

## Key Innovation

The early-warning concept is sensor fusion plus trend awareness at one local drainage point. `rain_detected` is true at 75% moisture and is derived from, not separate from, the analog moisture reading. Moisture is a wetness proxy and is not rainfall in mm/hour. The model considers wetness and rise rate alongside level. It estimates prototype overflow risk only; it does not guarantee that flooding will occur.

## System Architecture

### Current software prototype

```text
Sensor Simulator
      ↓
FastAPI
      ↓
Random Forest ML
      ↓
Risk Prediction
      ↓
Dashboard + Alerts View
```

### ESP8266 firmware integration (physical validation pending)

```text
Sensors
   ↓
ESP8266
   ↓
Wi-Fi
   ↓
FastAPI
   ↓
Random Forest ML
   ↓
Risk Prediction
   ↓
Dashboard + Alerts
```

The simulator is the current data source for this software demo. ESP8266 firmware is included, but physical sensors have not been tested by this project.

## Hardware

Firmware targets these field components:

- ESP8266 NodeMCU
- HC-SR04 ultrasonic water-level sensor
- Analog moisture sensor used as a wetness proxy
- Buzzer
- LEDs

Firmware preserves TRIG=D5, ECHO=D6, MOISTURE=A0, BUZZER=D7, and LED=D2. It publishes V0 water level, V1 moisture/wetness, V2 rise rate, V3 risk, and V4 wetness threshold state to Blynk. Calibration and physical hardware testing remain outstanding. HC-SR04 Echo requires a voltage divider or level shifter before the ESP8266 input.

## Software

- Python
- FastAPI and Uvicorn
- Pandas and NumPy
- Scikit-learn and Joblib
- Vanilla HTML, CSS, and JavaScript

## Machine Learning

FloodGuard uses a `RandomForestClassifier` with the sensor features listed above. The target classes are `LOW`, `MODERATE`, and `HIGH`. The model was trained and evaluated with a stratified train/test split on a reproducible synthetic development dataset. The saved model is loaded for prediction; it is not retrained for each API request.

The dataset is intended to demonstrate the local drainage software concept. Its evaluation results measure agreement with synthetic labels, not real-world overflow or flood-forecasting performance.

## Backend

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Identifies the FloodGuard API |
| GET | `/health` | Returns service health |
| POST | `/predict` | Validates a reading and returns an ML prediction |
| GET | `/latest` | Returns the newest in-memory prediction |
| GET | `/history` | Returns up to 20 newest-first predictions |

## Dashboard

The dashboard presents live API-produced water level, soil moisture/wetness, rise rate, dynamic LOW/MODERATE/HIGH drainage risk, water-level and rise-rate trend chart, recent-readings table, latest update time, and API connection state. It polls the API and does not communicate directly with the simulator.

## Simulator

The simulator sends the same JSON contract used by the available ESP8266 firmware. Its drainage scenarios are:

- `normal_drainage`: stable local conditions
- `rising_water`: increasing local water level
- `rapid_water_rise`: fast trend for early warning
- `high_wetness_rising_water`: wetness plus rising water
- `potential_storm_drain_overflow`: combined high-risk conditions

## Current Validation

Verified project facts:

- Automated tests cover API validation, history, dashboard serving, wetness semantics, and all simulator scenario payloads.
- API endpoints were validated.
- All simulator scenarios were validated against the API and model.
- The dashboard route and simulator-to-API-to-ML-to-history flow were validated.

## Limitations

- The current ML dataset is synthetic; its metrics are development results only.
- Real hydrological data is required for meaningful deployment validation.
- Physical sensor calibration is required.
- Real local drainage validation requires field data, calibration, monitoring, and domain expertise.
- Deployment requires a Wi-Fi network and a FastAPI host reachable from the node; no pumps or sluices are automated.
- FloodGuard is a prototype and not an official warning system.

## Future Scope

- Real ESP8266 integration
- Calibrated rain gauge
- LoRa or GSM communication
- Multiple sensing nodes
- Real historical flood datasets
- Improved ML models and evaluation
- Cloud deployment
- SMS or app alerts
- ESP8266 + Blynk publishing for the configured sensor node
