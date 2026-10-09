# 🌊 FloodGuard
### IoT-Based Smart Storm-Drain Monitoring & Early Flood Warning System

FloodGuard is an IoT and Machine Learning-based prototype designed to monitor water levels and wetness near storm drains and low-lying areas. It classifies conditions into **LOW, MODERATE, or HIGH risk** to support early awareness of potential overflow conditions.

The system integrates sensor data collection, an ESP8266 microcontroller, a FastAPI prediction backend, a machine learning model, and a web dashboard. Optional Blynk integration can provide additional IoT monitoring.

> **Note:** This is a prototype, not a field-validated flood forecasting system. The current ML model uses synthetic training data. Soil moisture is used as a wetness indicator and does not directly measure rainfall in mm/hr.

---

## ✨ Key Features

- 🌊 **Water-Level Monitoring:** Uses an HC-SR04 ultrasonic sensor to estimate water level.
- 🌱 **Wetness Monitoring:** Uses a soil-moisture sensor as a wetness proxy.
- 📡 **IoT Connectivity:** ESP8266 NodeMCU communicates over Wi-Fi.
- 🤖 **ML-Based Risk Classification:** Categorizes conditions into LOW, MODERATE, or HIGH risk.
- ⚡ **FastAPI Backend:** Receives sensor readings and generates predictions.
- 📊 **Web Dashboard:** Displays monitoring information and risk status.
- 🔔 **Alert Support:** Buzzer and optional Blynk integration.
- 🧪 **Sensor Simulator:** Allows software testing without physical hardware.
- ✅ **Automated Tests:** Includes API tests for development and verification.

---

## 🧰 Technology Stack

| Component | Technology |
|---|---|
| Microcontroller | ESP8266 NodeMCU |
| Ultrasonic Sensor | HC-SR04 |
| Wetness Sensor | Soil-Moisture Sensor |
| Firmware | Arduino C++ / PlatformIO |
| Backend | Python, FastAPI |
| Machine Learning | scikit-learn, joblib |
| Frontend | HTML, CSS, JavaScript |
| Testing | pytest |
| IoT Monitoring | Blynk (optional) |
| Version Control | Git and GitHub |

---

## 🏗️ System Architecture

```text
       HC-SR04 + Soil-Moisture Sensor
                     |
                     v
              ESP8266 NodeMCU
                     |
                  Wi-Fi
                     |
                     v
              FastAPI Backend
                /predict
                     |
                     v
             ML Risk Classifier
                     |
           +---------+---------+
           |                   |
           v                   v
     Risk Classification   API / History
     LOW / MODERATE / HIGH     |
           |                   |
           +---------+---------+
                     |
                     v
               Web Dashboard
                     |
                     v
           Optional Blynk Alerts
```

A sensor simulator is also available to test the software pipeline without connected hardware.

---

## 📁 Project Structure

```text
FloodGuard/
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   └── schemas.py
│
├── data/
│   └── flood_data.csv
│
├── docs/
│   ├── DEMO_SCRIPT.md
│   ├── PROJECT_REPORT.md
│   └── TECHNICAL_ARCHITECTURE.md
│
├── firmware/
│   └── esp8266_floodguard/
│       ├── esp8266_floodguard.ino
│       ├── platformio.ini
│       └── secrets.h.example
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── ml/
│   ├── __init__.py
│   ├── feature_order.json
│   ├── generate_dataset.py
│   ├── model.joblib
│   ├── model_loader.py
│   └── train_model.py
│
├── simulator/
│   ├── __init__.py
│   └── sensor_simulator.py
│
├── tests/
│   ├── __init__.py
│   └── test_api.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🚀 Getting Started

### Prerequisites

Install the following:

- Python 3.10+ with a version compatible with the project dependencies
- Git
- VS Code (recommended)
- PlatformIO extension if you want to build and upload ESP8266 firmware

### 1. Clone the Repository

```bash
git clone https://github.com/abhishek25001011-boop/FloodGuard.git
```

Navigate to the project directory:

```bash
cd FloodGuard
```

### 2. Create a Virtual Environment

On Windows:

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the Backend

From the project root, run:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

If the application starts successfully, try these endpoints:

| Endpoint | Purpose |
|---|---|
| `/health` | Backend health check |
| `/predict` | Risk prediction endpoint |
| `/latest` | Latest monitoring information, if enabled |
| `/history` | Historical readings, if enabled |
| `/dashboard/` | Web dashboard, if enabled |

For local testing, use:

```text
http://127.0.0.1:8000
```

FastAPI interactive documentation may be available at:

```text
http://127.0.0.1:8000/docs
```

The exact endpoints depend on the implementation in `backend/main.py`.

### 5. Run Automated Tests

```bash
python -m pytest -q
```

### 6. Test with the Sensor Simulator

The simulator is located at:

```text
simulator/sensor_simulator.py
```

Start the backend first. Then inspect the simulator's supported arguments and API URL before running it.

The simulator can help test the API and prediction pipeline without physical sensors.

---

## 🔌 Hardware Components

The current firmware targets an **ESP8266 NodeMCU**.

| Component | Purpose |
|---|---|
| ESP8266 NodeMCU | Main controller and Wi-Fi connectivity |
| HC-SR04 | Measures distance to the water surface |
| Soil-Moisture Sensor | Provides a wetness-related reading |
| Passive Buzzer | Audible alert output |
| LED (optional) | Visual status indicator |
| Breadboard and jumper wires | Circuit connections |
| Resistors or suitable level shifter | Protect the ESP8266 Echo input |

---

## 📌 ESP8266 Wiring

| Component Pin | NodeMCU Pin |
|---|---|
| HC-SR04 VCC | VIN / 5V supply |
| HC-SR04 GND | GND |
| HC-SR04 TRIG | D5 / GPIO14 |
| HC-SR04 ECHO | D6 / GPIO12 through a voltage divider or suitable level shifter |
| Soil-Moisture VCC | 3V3, if supported by the module |
| Soil-Moisture GND | GND |
| Soil-Moisture AO | A0 |
| Buzzer Positive | D7 / GPIO13 |
| Buzzer Negative | GND |
| Optional LED Positive | D2 / GPIO4 through a current-limiting resistor |
| Optional LED Negative | GND |

### ⚠️ Electrical Safety

A standard HC-SR04 Echo output may be approximately 5V, while ESP8266 GPIO pins use 3.3V logic and are not 5V tolerant.

**Do not connect a standard HC-SR04 Echo output directly to D6.** Use a correctly wired voltage divider or a suitable level shifter.

Also verify the analog input voltage range of your specific NodeMCU board before connecting the soil-moisture sensor to A0. Connect the grounds of the modules together.

---

## ⚙️ Firmware Configuration

Firmware files are located in:

```text
firmware/esp8266_floodguard/
```

### Configuration Steps

1. Open the firmware folder in VS Code with PlatformIO installed.
2. Copy `secrets.h.example` to `secrets.h`.
3. Enter your own Wi-Fi credentials.
4. Configure Blynk credentials if using Blynk.
5. Configure the backend URL according to the firmware.
6. Build the project before uploading it to the ESP8266.

### Important Security Notes

- Never upload your real `secrets.h`.
- Never commit Wi-Fi passwords, Blynk authentication tokens, or private API keys.
- Keep `secrets.h.example` free of real credentials.
- If the ESP8266 communicates with a backend running on your laptop, use the laptop's local network IP address rather than `127.0.0.1`.
- Keep the laptop and ESP8266 on the same accessible network and configure firewall access if necessary.

---

## 🤖 Machine Learning

FloodGuard includes scripts for dataset generation, model training, and model loading.

Relevant files:

```text
ml/
├── feature_order.json
├── generate_dataset.py
├── model.joblib
├── model_loader.py
└── train_model.py
```

The model uses sensor-related features to classify the current prototype's risk categories.

### Current Limitations

- The current model is trained on synthetic data.
- Real-world calibration and field validation are still required.
- Soil moisture is not a direct measurement of rainfall intensity.
- Risk labels are prototype classifications, not official emergency warnings.
- Performance may vary with sensor placement, turbulence, drain geometry, and environmental conditions.
- Automated pumps, gates, and other mitigation mechanisms are not implemented unless separately developed and validated.

---

## 🧪 Testing and Demonstration

A software demonstration can show:

1. Simulated sensor readings.
2. Data submitted to the prediction API.
3. Machine-learning risk classification.
4. Dashboard updates.
5. Configured alert output.

For a physical demonstration, use actual sensor readings and clearly distinguish them from simulated data.

Additional documentation:

- [Demo Script](docs/DEMO_SCRIPT.md)
- [Project Report](docs/PROJECT_REPORT.md)
- [Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)

---

## 🔮 Future Scope

- Collect and label real-world sensor data.
- Calibrate water-level measurements for specific storm-drain geometry.
- Integrate suitable rainfall and water-flow sensors.
- Evaluate the model using held-out, field-collected data.
- Improve alert reliability and deployment monitoring.
- Develop weather-resistant enclosures and power management.
- Explore automated mitigation only after safety analysis and field validation.

---

## 👨‍💻 Author

**Abhishek Kumar**

GitHub: [@abhishek25001011-boop](https://github.com/abhishek25001011-boop)

Project Repository: [FloodGuard](https://github.com/abhishek25001011-boop/FloodGuard)

---

## 📄 License

No license has been added yet. Unless a license is added, the repository's code is not automatically granted an open-source license.