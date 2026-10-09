# FloodGuard Technical Architecture - Smart Storm-Drain Monitoring

## A. Component Architecture

```text
Simulator (current) / ESP8266 firmware (available; untested on hardware)
                ↓
          FastAPI backend
                ↓
     Saved Random Forest artifact
                ↓
  Prediction history + latest reading
                ↓
        Vanilla JavaScript dashboard
```

The simulator and ESP8266 firmware are data producers. The dashboard is an API consumer; it never communicates directly with a producer.

## B. Data Flow

1. A producer creates one reading.
2. It sends `POST /predict` to FastAPI.
3. FastAPI validates the reading with Pydantic.
4. The backend loads the cached saved model artifact and predicts risk/probabilities.
5. It stores a timestamped prediction in an in-memory newest-first history capped at 20 readings.
6. The dashboard polls `/history` every two seconds to update its cards, chart, and table.

## C. API Contract

Every producer must send exactly this sensor contract:

```json
{
  "water_level_cm": <float>,
  "moisture_pct": <float>,
  "rain_detected": <boolean>,
  "rise_rate_cm_min": <float>
}
```

ESP8266 firmware sends this same structure. The fields describe one local drain or low-lying monitoring point. `POST /predict` responds with a drainage overflow risk label, class probabilities, and the validated input. `GET /latest` and `GET /history` expose timestamped stored predictions for the dashboard.

## D. ML Pipeline

`ml/generate_dataset.py` creates reproducible synthetic normal-drainage, rising-water, and potential-overflow scenarios for one local point. `ml/train_model.py` trains a `RandomForestClassifier`, evaluates it using a stratified train/test split, and saves `ml/model.joblib` with the exact feature order and synthetic-development metadata. `ml/model_loader.py` caches and reuses the artifact; it does not retrain during serving.

Feature order:

1. `water_level_cm`
2. `moisture_pct`
3. `rain_detected` (true when moisture is at least 75%)
4. `rise_rate_cm_min`

## E. Simulator Architecture

`simulator/sensor_simulator.py` accepts `normal_drainage`, `rising_water`, `rapid_water_rise`, `high_wetness_rising_water`, and `potential_storm_drain_overflow` scenarios. Legacy names remain accepted. It generates bounded, slightly varying values, POSTs only the shared sensor contract, and displays the actual API result. The API URL and interval are configurable by command line.

## F. Dashboard Architecture

The dashboard is served at `/dashboard/` by FastAPI and consists of static HTML, CSS, and vanilla JavaScript. Its JavaScript polls `/history`; successful responses update the current risk, metric cards, chart, and newest-first table. Failed requests set a disconnected state and clear current metrics rather than inventing data.

## G. Hardware Integration Code

The firmware chain is HC-SR04 + analog soil-moisture wetness proxy -> ESP8266 -> Wi-Fi -> FastAPI, with measurements and returned risk also published to Blynk. Firmware is available; physical hardware testing and calibration remain outstanding.


## H. ESP8266 + Blynk firmware

`firmware/esp8266_floodguard/esp8266_floodguard.ino` samples an HC-SR04 and analog moisture sensor, converts configured distance to water level and moisture ADC to 0-100% wetness, calculates positive level rise per minute, derives `rain_detected` at >=75% wetness, and POSTs the four-field API input. The API response risk is shown in Blynk V3 and drives the LED/buzzer for HIGH. Pins remain TRIG=D5, ECHO=D6, MOISTURE=A0, BUZZER=D7, and LED=D2. Blynk mapping: V0 water level (cm), V1 moisture/wetness (%), V2 rise rate (cm/min), V3 drainage risk (string), V4 wetness threshold state (0/1, not rainfall rate). Local credentials belong in an untracked `secrets.h` copied from `secrets.h.example`. Set the API URL to a host reachable from the ESP8266. HC-SR04 Echo commonly outputs 5 V and must pass through a voltage divider or level shifter before D6. Sensor calibration, network setup, and physical testing remain required.
