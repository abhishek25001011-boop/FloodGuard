#include "secrets.h"

#define BLYNK_TEMPLATE_ID BLYNK_TEMPLATE_ID_VALUE
#define BLYNK_TEMPLATE_NAME BLYNK_TEMPLATE_NAME_VALUE
#define BLYNK_AUTH_TOKEN BLYNK_AUTH_TOKEN_VALUE

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <BlynkSimpleEsp8266.h>

// ================= PIN CONFIGURATION =================

// ESP8266 NodeMCU
constexpr uint8_t TRIG_PIN = D5;       // GPIO14
constexpr uint8_t ECHO_PIN = D6;       // GPIO12
constexpr uint8_t MOISTURE_PIN = A0;   // Analog input
constexpr uint8_t BUZZER_PIN = D7;     // GPIO13
constexpr uint8_t LED_PIN = D2;        // GPIO4

// ================= SENSOR CONFIGURATION =================

constexpr float MAX_WATER_DEPTH_CM = 150.0f;

// ESP8266 A0 calibration.
// CHANGE THESE AFTER ACTUAL DRY/WET TESTING.
constexpr int MOISTURE_DRY_ADC = 850;
constexpr int MOISTURE_WET_ADC = 350;

constexpr unsigned long SAMPLE_INTERVAL_MS = 5000;
constexpr unsigned long ECHO_TIMEOUT_US = 30000;

constexpr float MAX_RISE_RATE_CM_MIN = 50.0f;
constexpr float WETNESS_DETECTION_THRESHOLD_PCT = 75.0f;

// =======================================================

BlynkTimer timer;

float previousLevelCm = NAN;
unsigned long previousSampleMs = 0;

// -------------------------------------------------------
// Read HC-SR04 distance
// -------------------------------------------------------

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

// -------------------------------------------------------
// Read water level
// -------------------------------------------------------

float readWaterLevelCm() {

  float values[3];
  int count = 0;

  for (int i = 0; i < 3; i++) {

    float distance = readDistanceCm();

    if (!isnan(distance) &&
        distance >= 2.0f &&
        distance <= MAX_WATER_DEPTH_CM) {

      values[count++] = distance;
    }

    delay(30);
  }

  if (count == 0) {
    return NAN;
  }

  // Sort readings
  for (int i = 0; i < count; i++) {

    for (int j = i + 1; j < count; j++) {

      if (values[j] < values[i]) {

        float temp = values[i];
        values[i] = values[j];
        values[j] = temp;
      }
    }
  }

  float medianDistance = values[count / 2];

  float waterLevel =
      MAX_WATER_DEPTH_CM - medianDistance;

  return constrain(
      waterLevel,
      0.0f,
      MAX_WATER_DEPTH_CM
  );
}

// -------------------------------------------------------
// Read calibrated soil wetness proxy
// -------------------------------------------------------

float readMoisturePct() {

  int raw = analogRead(MOISTURE_PIN);

  float pct =
      100.0f *
      (MOISTURE_DRY_ADC - raw) /
      (float)(MOISTURE_DRY_ADC - MOISTURE_WET_ADC);

  pct = constrain(pct, 0.0f, 100.0f);

  Serial.print("Moisture ADC: ");
  Serial.print(raw);

  Serial.print(" | Wetness proxy %: ");
  Serial.println(pct);

  return pct;
}

// -------------------------------------------------------
// Send sensor data
// -------------------------------------------------------

void sampleAndSend() {

  unsigned long now = millis();

  float level = readWaterLevelCm();

  if (isnan(level)) {

    Serial.println(
      "HC-SR04 reading invalid. Skipping update."
    );

    return;
  }

  float moisture = readMoisturePct();

  // This is a wetness threshold flag, not rainfall intensity in mm/hour.
  bool rainDetected =
      moisture >= WETNESS_DETECTION_THRESHOLD_PCT;

  // Calculate water rise rate
  float riseRate = 0.0f;

  if (!isnan(previousLevelCm) &&
      now > previousSampleMs) {

    float timeDifference =
        (now - previousSampleMs) / 60000.0f;

    float levelDifference =
        level - previousLevelCm;

    riseRate =
        levelDifference / timeDifference;

    // We only care about increasing water level
    if (riseRate < 0.0f) {
      riseRate = 0.0f;
    }

    riseRate =
        constrain(
            riseRate,
            0.0f,
            MAX_RISE_RATE_CM_MIN
        );
  }

  previousLevelCm = level;
  previousSampleMs = now;

  Serial.println("----------------------------");

  Serial.print("Water Level: ");
  Serial.print(level);
  Serial.println(" cm");

  Serial.print("Moisture: ");
  Serial.print(moisture);
  Serial.println(" %");

  Serial.print("Rain/Wetness Detected: ");
  Serial.println(
      rainDetected ? "YES" : "NO"
  );

  Serial.print("Rise Rate: ");
  Serial.print(riseRate);
  Serial.println(" cm/min");

  // -----------------------------------------------------
  // WiFi + API
  // -----------------------------------------------------

  if (WiFi.status() == WL_CONNECTED) {

    WiFiClient client;
    HTTPClient http;

    if (http.begin(client, FLOODGUARD_API_URL)) {

      http.addHeader(
          "Content-Type",
          "application/json"
      );

      StaticJsonDocument<256> doc;

      doc["water_level_cm"] = level;
      doc["moisture_pct"] = moisture;
      doc["rain_detected"] = rainDetected;
      doc["rise_rate_cm_min"] = riseRate;

      String payload;

      serializeJson(doc, payload);

      Serial.println("Sending API request...");
      Serial.println(payload);

      int httpCode =
          http.POST(payload);

      String risk = "UNAVAILABLE";

      if (httpCode > 0) {

        Serial.print("API HTTP Code: ");
        Serial.println(httpCode);

        String response =
            http.getString();

        Serial.print("API Response: ");
        Serial.println(response);

        StaticJsonDocument<512> result;

        DeserializationError error =
            deserializeJson(
                result,
                response
            );

        if (!error) {

          risk =
              result["risk"]
              | "UNAVAILABLE";
        }
      }
      else {

        Serial.print(
            "HTTP POST failed: "
        );

        Serial.println(
            http.errorToString(httpCode)
        );
      }

      http.end();

      Serial.print("Flood Risk: ");
      Serial.println(risk);

      // ---------------------------------------------------
      // Local alarm
      // ---------------------------------------------------

      bool highRisk =
          (risk == "HIGH");

      digitalWrite(
          LED_PIN,
          highRisk ? HIGH : LOW
      );

      if (highRisk) {

        // Passive buzzer alarm
        tone(BUZZER_PIN, 2000);

      } else {

        noTone(BUZZER_PIN);
      }

      // ---------------------------------------------------
      // Blynk
      // ---------------------------------------------------

      if (Blynk.connected()) {

        Blynk.virtualWrite(
            V0,
            level
        );

        Blynk.virtualWrite(
            V1,
            moisture
        );

        Blynk.virtualWrite(
            V2,
            riseRate
        );

        Blynk.virtualWrite(
            V3,
            risk
        );

        // V4 = moisture-derived wetness threshold state, not rainfall rate.
        Blynk.virtualWrite(
            V4,
            rainDetected ? 1 : 0
        );

        Serial.println(
            "Blynk updated."
        );
      }
      else {

        Serial.println(
            "Blynk disconnected."
        );
      }
    }
    else {

      Serial.println(
          "Unable to connect to API."
      );
    }
  }
  else {

    Serial.println(
        "WiFi disconnected."
    );
  }
}

// -------------------------------------------------------
// SETUP
// -------------------------------------------------------

void setup() {

  Serial.begin(115200);

  delay(500);

  Serial.println();
  Serial.println(
      "===== FloodGuard ESP8266 ====="
  );

  pinMode(
      TRIG_PIN,
      OUTPUT
  );

  pinMode(
      ECHO_PIN,
      INPUT
  );

  pinMode(
      BUZZER_PIN,
      OUTPUT
  );

  pinMode(
      LED_PIN,
      OUTPUT
  );

  digitalWrite(
      TRIG_PIN,
      LOW
  );

  digitalWrite(
      LED_PIN,
      LOW
  );

  noTone(BUZZER_PIN);

  // -----------------------------------------------------
  // WiFi
  // -----------------------------------------------------

  Serial.print(
      "Connecting to WiFi..."
  );

  WiFi.mode(WIFI_STA);

  WiFi.begin(
      WIFI_SSID,
      WIFI_PASSWORD
  );

  unsigned long startTime =
      millis();

  while (
      WiFi.status() != WL_CONNECTED &&
      millis() - startTime < 20000
  ) {

    delay(500);

    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {

    Serial.println(
        "WiFi Connected!"
    );

    Serial.print(
        "ESP8266 IP: "
    );

    Serial.println(
        WiFi.localIP()
    );
  }
  else {

    Serial.println(
        "WiFi connection failed."
    );
  }

  // -----------------------------------------------------
  // Blynk
  // -----------------------------------------------------

  Blynk.config(
      BLYNK_AUTH_TOKEN
  );

  if (WiFi.status() == WL_CONNECTED) {

    Serial.println(
        "Connecting to Blynk..."
    );

    Blynk.connect(10000);
  }

  // -----------------------------------------------------
  // Timer
  // -----------------------------------------------------

  timer.setInterval(
      SAMPLE_INTERVAL_MS,
      sampleAndSend
  );

  Serial.println(
      "FloodGuard initialized."
  );
}

// -------------------------------------------------------
// LOOP
// -------------------------------------------------------

void loop() {

  if (
      WiFi.status() != WL_CONNECTED
  ) {

    WiFi.reconnect();
  }

  Blynk.run();

  timer.run();
}