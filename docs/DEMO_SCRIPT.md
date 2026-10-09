# FloodGuard Demo Script (3–5 Minutes)

## 0:00–0:30 — Problem introduction

“Flood warnings based only on the current water level can be late. A water level may still look moderate while the wetness reading is high and the level is rising quickly. We wanted to demonstrate a clearer early-warning view that uses all three signals together.”

## 0:30–1:00 — FloodGuard solution

“FloodGuard is a smart storm-drain monitoring prototype for one local drain or low-lying area. It combines water level, soil moisture as a wetness proxy, a moisture-threshold wetness flag, and rate of water-level rise. The wetness flag is not rainfall in mm/hour. Our model returns a simple LOW, MODERATE, or HIGH drainage-risk label.”

## 1:00–1:30 — Architecture

“For today, our software sensor simulator sends a reading to FastAPI. FastAPI validates it and sends it to our saved Random Forest model. The result is stored for the dashboard, which shows the latest drainage risk and recent trend. The available ESP8266 firmware sends the same four-field JSON structure as the simulator.”

## 1:30–2:00 — Show dashboard

“This is the FloodGuard dashboard. It displays the current drainage risk, live water level, soil wetness, and rise rate. The chart and table use only readings returned by the API. The data source is clearly marked as the simulator, and the dashboard also shows API connection state.”

## 2:00–2:30 — Run LOW scenario

Run:

```powershell
python simulator\sensor_simulator.py --scenario normal_drainage
```

“This sends relatively stable local drainage values. The dashboard updates automatically and shows a LOW state with conditions currently stable.”

## 2:30–3:00 — Run MODERATE scenario

Run:

```powershell
python simulator\sensor_simulator.py --scenario rising_water
```

“Now the local water level, wetness, and rise rate are higher. The model returns MODERATE, and the dashboard changes to its monitoring state. This shows why a single water-level threshold is not enough.”

## 3:00–3:30 — Run HIGH scenario

Run:

```powershell
python simulator\sensor_simulator.py --scenario potential_storm_drain_overflow
```

“This scenario combines high water level, wetness, and rise rate. The dashboard changes to red and displays ‘Potential storm-drain overflow detected.’ It predicts local drainage risk; it does not claim overflow is guaranteed.”

## 3:30–4:00 — Demonstrate rapid rise

Run:

```powershell
python simulator\sensor_simulator.py --scenario rapid_water_rise --interval 2
```

“Rapid water rise is the key early-warning demonstration. The water level starts before an extreme value, while wetness and rise rate increase. As readings progress, the model can escalate local drainage risk. Press Ctrl+C after a few readings.”

## 4:00–4:30 — Explain hardware integration

“The current producer is a simulator, not a physical sensor. ESP8266 firmware is available for the HC-SR04, analog moisture input, API, Blynk V0-V4, LED, and buzzer. The firmware has not been tested on physical hardware, so calibration and field testing remain. HC-SR04 Echo needs a voltage divider or level shifter before D6.”

## 4:30–5:00 — Future scope and conclusion

“FloodGuard demonstrates how sensor fusion and trend information can make a flood-risk prototype more informative than level alone. Next steps are real hydrological datasets, field-calibrated sensors, multi-node communication, and alert integrations. This is a prototype, not an official warning system.”

## Likely Judge Questions

### 1. Why not just use a water-level threshold?

A threshold can be late and misses context. Wetness and rate of rise show whether conditions are escalating even before water reaches an extreme level.

### 2. Why use machine learning?

It provides a prototype way to combine several inputs and their interactions into one consistent risk class. It does not replace hydrological validation or expert decision-making.

### 3. What makes this an early-warning system?

The design considers wetness and the water-level trend, not only the present water level, so it can flag an increasing situation earlier.

### 4. Where did the training data come from?

The included training data is reproducible synthetic development data generated for this prototype.

### 5. Is the dataset real?

No. It is not a real historical flood dataset and should not be treated as real-world forecasting evidence.

### 6. How will this work with actual sensors?

The included ESP8266 firmware sends the same four-field JSON payload to `POST /predict`. Physical sensor calibration and field validation remain next steps.

### 7. What happens if the internet fails?

The current dashboard reports that the backend is disconnected and clears current values rather than showing invented data. A deployed system would need local buffering and a communication fallback such as LoRa or GSM.

### 8. Why Random Forest?

It is a reliable, interpretable baseline for tabular features, handles nonlinear relationships, and is lightweight enough for a hackathon prototype.

### 9. How is rise rate calculated?

It is the change in water level divided by elapsed time, expressed in centimetres per minute. A physical implementation should smooth readings and handle sensor noise.

### 10. How would this scale to multiple locations?

Each node can send location-associated readings to a backend designed for multi-site storage, monitoring, and alert routing. That requires a database and deployment design beyond this MVP.

### 11. What are the current limitations?

Synthetic data, no field-calibrated sensors, no real hydrological validation, and in-memory prototype history are the main limitations.

### 12. What will you improve next?

We would integrate calibrated ESP32 sensors, collect real historical and field data, evaluate models properly, add resilient communications, and deliver location-aware alerts.
