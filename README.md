# FloodGuard - Smart Storm-Drain Monitoring

FloodGuard is a local storm-drain and low-lying-area monitoring prototype for early warning of possible drainage overflow at one sensor node. It is not a city-wide flood forecasting system.

## Problem

Water-level-only monitoring can warn too late at a drain or low-lying point. Soil moisture-derived wetness and the rate at which water is rising provide local context before water reaches an overflow condition.

## Solution

FloodGuard combines water level, soil moisture as a wetness proxy, a wetness threshold flag, and rate of water-level rise with Random Forest classification to return `LOW`, `MODERATE`, or `HIGH` local drainage risk.

## Key Innovation

Sensor fusion and trend information can reveal escalating risk before water reaches a critical level.

## Architecture

### Current software prototype

```text
Sensor simulator → FastAPI → Random Forest model → Drainage risk → Dashboard
```

### Hardware integration code (physical validation pending)

```text
Sensors / Simulator → ESP8266 → Wi-Fi → FastAPI → Random Forest → Drainage risk → Dashboard / Blynk
```

No physical hardware has been tested. The simulator and ESP8266 firmware use the same API contract.

## Features

- Reproducible synthetic local-drainage development dataset and saved Random Forest model
- Validated FastAPI prediction API with latest/history endpoints
- Hardware-compatible software sensor simulator
- Responsive live dashboard with risk states, trend chart, and recent readings

## ML Model

`RandomForestClassifier` uses `water_level_cm`, `moisture_pct`, `rain_detected`, and `rise_rate_cm_min`. `moisture_pct` is calibrated soil wetness from 0% dry to 100% wet; it does not measure rainfall in mm/hour. The artifact is `ml/model.joblib`; the API loads it through `ml/model_loader.py` and does not retrain per request. Saved metrics are development results on synthetic labels only, not real-world accuracy.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API identification |
| GET | `/health` | Health check |
| POST | `/predict` | ML prediction |
| GET | `/latest` | Latest in-memory prediction |
| GET | `/history` | Up to 20 newest-first predictions |
| GET | `/dashboard/` | Web dashboard |

```json
POST /predict
{"water_level_cm":55,"moisture_pct":90,"rain_detected":true,"rise_rate_cm_min":6}
```

```json
{"risk":"HIGH","probabilities":{"HIGH":0.99,"LOW":0.0,"MODERATE":0.01},"input":{"water_level_cm":55.0,"moisture_pct":90.0,"rain_detected":true,"rise_rate_cm_min":6.0}}
```

Example values are synthetic-development outputs for a local drainage point, not real-world forecasts. Visit `http://127.0.0.1:8000/docs` for interactive documentation.

## Running the Project (Windows)

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000/dashboard/`. In a second PowerShell window:

```powershell
.\.venv\Scripts\Activate.ps1
python simulator\sensor_simulator.py --scenario rising_water
```

## Simulator

```powershell
python simulator\sensor_simulator.py --scenario normal_drainage
python simulator\sensor_simulator.py --scenario rising_water
python simulator\sensor_simulator.py --scenario rapid_water_rise
python simulator\sensor_simulator.py --scenario high_wetness_rising_water
python simulator\sensor_simulator.py --scenario potential_storm_drain_overflow
python simulator\sensor_simulator.py --scenario rapid_water_rise --interval 2
```

Use `Ctrl+C` to stop continuous mode.

## Limitations

- The ML development data is synthetic and cannot establish real-world accuracy.
- Moisture is a wetness/rain proxy only; it is not rainfall in mm/hour.
- Real drainage observations and hydrological validation are required.
- Physical sensors require calibration and environmental testing.
- The node needs Wi-Fi access to a LAN-reachable FastAPI host; the API and dashboard need a deployment host and network monitoring.
- No automated pumps or sluices are implemented.

## ESP8266 + Blynk integration

Firmware lives in `firmware/esp8266_floodguard/` and targets the NodeMCU ESP8266. Verified pins are TRIG=D5, ECHO=D6, MOISTURE=A0, BUZZER=D7, and LED=D2. Copy `secrets.h.example` to `secrets.h`, then set Wi-Fi, Blynk template/device token, and a LAN-reachable `FLOODGUARD_API_URL`. Set `MAX_WATER_DEPTH_CM` to the installed sensor-to-floor distance and calibrate the moisture dry/wet ADC values in the sketch. Common HC-SR04 modules output 5 V on Echo; the ESP8266 input requires a suitable voltage divider or level shifter before D6.

Create Blynk datastreams V0 water level (cm), V1 soil moisture/wetness (%), V2 rise rate (cm/min), V3 drainage risk (string), and V4 wetness detection (0/1). V4 publishes the moisture-derived wetness threshold state, not rainfall intensity. API input is `water_level_cm`, `moisture_pct` (0 dry, 100 wet), `rain_detected` (true at 75% wetness), and `rise_rate_cm_min`. The LED and buzzer activate for API risk `HIGH`. Device firmware and physical sensors have not been hardware-tested; verify wiring, calibration, voltage protection, network access, and alarm behavior on the actual installation.
