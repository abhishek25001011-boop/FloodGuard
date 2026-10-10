#include "secrets.h"

#define BLYNK_TEMPLATE_ID TMPL3ja_qopWD
#define BLYNK_TEMPLATE_NAME "FloodGuard"
#define BLYNK_AUTH_TOKEN 3-HG6X8c3QmkO2ckrR1OqUkh62PutG8w

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <BlynkSimpleEsp8266.h>
#include <math.h>

// =====================================================
// PIN CONFIGURATION — CURRENT WIRING
// =====================================================

constexpr uint8_t TRIG_PIN = D5;
constexpr uint8_t ECHO_PIN = D6;       // ECHO currently disconnected
constexpr uint8_t MOISTURE_PIN = A0;
constexpr uint8_t BUZZER_PIN = D7;

// LED removed. No LED pin is configured.

// =====================================================
// SENSOR CONFIGURATION
// =====================================================

constexpr float MAX_WATER_DEPTH_CM = 150.0f;

constexpr int MOISTURE_DRY_ADC = 850;
constexpr int MOISTURE_WET_ADC = 350;

constexpr unsigned long SAMPLE_INTERVAL_MS = 5000;
constexpr unsigned long ECHO_TIMEOUT_US = 30000;

constexpr float MAX_RISE_RATE_CM_MIN = 50.0f;
constexpr float WETNESS_THRESHOLD_PCT = 75.0f;

constexpr float MODERATE_LEVEL_CM = 75.0f;
constexpr float HIGH_LEVEL_CM = 120.0f;

// =====================================================
// GLOBAL VARIABLES
// =====================================================

BlynkTimer timer;

float previousLevelCm = NAN;
unsigned long previousSampleMs = 0;

String currentRisk = "UNKNOWN";

// =====================================================
// READ HC-SR04 DISTANCE
// =====================================================

float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(3);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration =
      pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);

  if (duration == 0) {
    return NAN;
  }

  return duration * 0.0343f / 2.0f;
}

// =====================================================
// READ WATER LEVEL
// =====================================================

float readWaterLevelCm() {
  float readings[3];
  int count = 0;

  for (int i = 0; i < 3; i++) {
    float distance = readDistanceCm();

    if (!isnan(distance) &&
        distance >= 2.0f &&
        distance <= MAX_WATER_DEPTH_CM) {
      readings[count++] = distance;
    }

    delay(30);
  }

  if (count == 0) {
    return NAN;
  }

  // Sort readings to obtain median.
  for (int i = 0; i < count - 1; i++) {
    for (int j = i + 1; j < count; j++) {
      if (readings[j] < readings[i]) {
        float temp = readings[i];
        readings[i] = readings[j];
        readings[j] = temp;
      }
    }
  }

  float medianDistance = readings[count / 2];

  // Assumes the sensor is mounted 150 cm above the bottom.
  float level = MAX_WATER_DEPTH_CM - medianDistance;

  return constrain(level, 0.0f, MAX_WATER_DEPTH_CM);
}

// =====================================================
// READ SOIL MOISTURE
// =====================================================

float readMoisturePct() {
  int raw = analogRead(MOISTURE_PIN);

  float denominator =
      (float)(MOISTURE_DRY_ADC - MOISTURE_WET_ADC);

  if (denominator == 0) {
    return 0.0f;
  }

  float percentage =
      100.0f *
      (MOISTURE_DRY_ADC - raw) /
      denominator;

  percentage = constrain(percentage, 0.0f, 100.0f);

  Serial.print("Moisture ADC: ");
  Serial.print(raw);
  Serial.print(" | Wetness proxy: ");
  Serial.print(percentage);
  Serial.println("%");

  return percentage;
}

// =====================================================
// LOCAL RISK ESTIMATE
// =====================================================

String calculateLocalRisk(float level,
                          float moisture,
                          float riseRate) {
  if (level >= HIGH_LEVEL_CM ||
      riseRate >= MAX_RISE_RATE_CM_MIN) {
    return "HIGH";
  }

  if (level >= MODERATE_LEVEL_CM ||
      moisture >= WETNESS_THRESHOLD_PCT) {
    return "MODERATE";
  }

  return "LOW";
}

// =====================================================
// BUZZER CONTROL — NO LED
// =====================================================

void updateBuzzer(const String& risk) {
  if (risk == "HIGH") {
    tone(BUZZER_PIN, 2000);
  } else {
    noTone(BUZZER_PIN);
  }
}

// =====================================================
// SEND DATA TO FASTAPI
// =====================================================

String sendToBackend(float level,
                     float moisture,
                     float riseRate,
                     bool wetnessDetected) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected.");
    return "";
  }

  WiFiClient client;
  HTTPClient http;

  http.setTimeout(5000);

  if (!http.begin(client, FLOODGUARD_API_URL)) {
    Serial.println("Unable to initialize API request.");
    return "";
  }

  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> request;

  request["water_level_cm"] = level;
  request["moisture_pct"] = moisture;
  request["rain_detected"] = wetnessDetected;
  request["rise_rate_cm_min"] = riseRate;

  String payload;
  serializeJson(request, payload);

  Serial.println("Sending sensor data:");
  Serial.println(payload);

  int httpCode = http.POST(payload);
  String returnedRisk = "";

  if (httpCode > 0) {
    String response = http.getString();

    Serial.print("API HTTP status: ");
    Serial.println(httpCode);

    Serial.print("API response: ");
    Serial.println(response);

    if (httpCode >= 200 && httpCode < 300) {
      StaticJsonDocument<512> result;

      DeserializationError error =
          deserializeJson(result, response);

      if (!error) {
        if (result["risk"].is<const char*>()) {
          returnedRisk = result["risk"].as<String>();
        } else if (result["risk_level"].is<const char*>()) {
          returnedRisk = result["risk_level"].as<String>();
        }

        returnedRisk.toUpperCase();

        if (returnedRisk != "LOW" &&
            returnedRisk != "MODERATE" &&
            returnedRisk != "HIGH") {
          returnedRisk = "";
        }
      } else {
        Serial.println("Could not parse API JSON.");
      }
    }
  } else {
    Serial.print("HTTP request failed: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();

  return returnedRisk;
}

// =====================================================
// UPDATE BLYNK DASHBOARD
// =====================================================

void updateBlynk(bool waterLevelValid,
                 float level,
                 float moisture,
                 float riseRate,
                 const String& risk,
                 bool wetnessDetected) {
  if (!Blynk.connected()) {
    Serial.println("Blynk disconnected.");
    return;
  }

  if (waterLevelValid) {
    Blynk.virtualWrite(V0, level);
    Blynk.virtualWrite(V2, riseRate);
  }

  Blynk.virtualWrite(V1, moisture);
  Blynk.virtualWrite(V3, risk);
  Blynk.virtualWrite(V4, wetnessDetected ? 1 : 0);

  Serial.println("Blynk dashboard updated.");
}

// =====================================================
// MAIN SENSOR CYCLE
// =====================================================

void sampleAndSend() {
  float moisture = readMoisturePct();

  bool wetnessDetected =
      moisture >= WETNESS_THRESHOLD_PCT;

  float level = readWaterLevelCm();

  Serial.println();
  Serial.println("========== FLOODGUARD ==========");

  Serial.print("Moisture: ");
  Serial.print(moisture);
  Serial.println("%");

  Serial.print("Wetness detected: ");
  Serial.println(wetnessDetected ? "YES" : "NO");

  // Do not send fake water-level values if ECHO is invalid.
  if (isnan(level)) {
    Serial.println(
        "Water level unavailable: no valid HC-SR04 ECHO reading."
    );

    Serial.println(
        "Skipping water-level-based prediction."
    );

    currentRisk = "UNKNOWN";

    noTone(BUZZER_PIN);

    updateBlynk(
        false,
        0.0f,
        moisture,
        0.0f,
        currentRisk,
        wetnessDetected
    );

    Serial.println("================================");
    return;
  }

  unsigned long now = millis();
  float riseRate = 0.0f;

  if (!isnan(previousLevelCm) &&
      now > previousSampleMs) {
    float elapsedMinutes =
        (now - previousSampleMs) / 60000.0f;

    if (elapsedMinutes > 0.0f) {
      riseRate =
          (level - previousLevelCm) / elapsedMinutes;

      if (riseRate < 0.0f) {
        riseRate = 0.0f;
      }

      riseRate = constrain(
          riseRate,
          0.0f,
          MAX_RISE_RATE_CM_MIN
      );
    }
  }

  previousLevelCm = level;
  previousSampleMs = now;

  Serial.print("Water level: ");
  Serial.print(level);
  Serial.println(" cm");

  Serial.print("Rise rate: ");
  Serial.print(riseRate);
  Serial.println(" cm/min");

  currentRisk =
      calculateLocalRisk(level, moisture, riseRate);

  String apiRisk = sendToBackend(
      level,
      moisture,
      riseRate,
      wetnessDetected
  );

  if (apiRisk.length() > 0) {
    currentRisk = apiRisk;
    Serial.println("Risk source: Backend API");
  } else {
    Serial.println("Risk source: Local fallback");
  }

  Serial.print("Flood risk: ");
  Serial.println(currentRisk);

  updateBuzzer(currentRisk);

  updateBlynk(
      true,
      level,
      moisture,
      riseRate,
      currentRisk,
      wetnessDetected
  );

  Serial.println("================================");
}

// =====================================================
// SETUP
// =====================================================

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println();
  Serial.println("===== FloodGuard ESP8266 =====");

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(TRIG_PIN, LOW);
  noTone(BUZZER_PIN);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to WiFi...");

  unsigned long startTime = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - startTime < 20000) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected.");

    Serial.print("ESP8266 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi connection failed.");
  }

  Blynk.config(BLYNK_AUTH_TOKEN);

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Connecting to Blynk...");
    Blynk.connect(10000);
  }

  timer.setInterval(
      SAMPLE_INTERVAL_MS,
      sampleAndSend
  );

  Serial.println("FloodGuard initialized.");
}

// =====================================================
// LOOP
// =====================================================

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
  }

  Blynk.run();
  timer.run();
}