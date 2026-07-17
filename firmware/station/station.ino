// Panen Pay intake station — ESP32 firmware
// Targets Arduino IDE with ESP32 core 3.x.
// Libraries: HX711 (bogde), WiFi, HTTPClient, ArduinoJson.
//
// Wiring:
//   HX711 load cell amp: DT  -> GPIO16
//                        SCK -> GPIO4
//   Passive buzzer:      +   -> GPIO25
//
// Behavior:
//   - 10 Hz scale reads, 8-sample moving average.
//   - stable = window spread < 5 g held for 1.5 s -> POST /ingest/weight, chirp.
//   - Polls /station/feedback every 2 s and plays the tier tone (read-once
//     server-side, so a tone never replays).

// ================== EDIT BEFORE FLASHING ==================
#define WIFI_SSID "your-hotspot-ssid"
#define WIFI_PASS "your-hotspot-password"
#define API_BASE "http://192.168.1.100:8000" // laptop running the backend
#define STATION_ID "station-1"
// ==========================================================

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <HX711.h>
#include <WiFi.h>

// ---- pins ----
const int HX711_DT_PIN = 16;
const int HX711_SCK_PIN = 4;
const int BUZZER_PIN = 25;

// Calibrate against a full 600 ml water bottle ≈ 617 g:
// place the bottle, read scale.get_units(10), then
// CALIBRATION_FACTOR *= (reading / 617.0).
const float CALIBRATION_FACTOR = 420.0f;

// ---- timing / stability (mirrors scripts/simulate_station.py) ----
const unsigned long READ_INTERVAL_MS = 100;      // 10 Hz
const int WINDOW_SIZE = 8;                       // moving average window
const float STABLE_SPREAD_G = 5.0f;              // spread < 5 g ...
const unsigned long STABLE_HOLD_MS = 1500;       // ... held 1.5 s
const unsigned long UNSTABLE_POST_INTERVAL_MS = 300;
const unsigned long FEEDBACK_POLL_INTERVAL_MS = 2000;

HX711 scale;

float window[WINDOW_SIZE];
int windowCount = 0;
int windowIndex = 0;

unsigned long lastReadAt = 0;
unsigned long lastUnstablePostAt = 0;
unsigned long lastFeedbackPollAt = 0;
unsigned long spreadOkSince = 0;
bool stableReported = false;

void setup() {
  Serial.begin(115200);

  scale.begin(HX711_DT_PIN, HX711_SCK_PIN);
  scale.set_scale(CALIBRATION_FACTOR);
  scale.tare();

  // ESP32 core 3.x pin-based LEDC API
  ledcAttach(BUZZER_PIN, 2000, 10);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("wifi: connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.printf("\nwifi: connected, ip=%s\n", WiFi.localIP().toString().c_str());
}

// ---- buzzer ----

void playTone(int freqHz, int durationMs) {
  ledcWriteTone(BUZZER_PIN, freqHz);
  delay(durationMs);
  ledcWriteTone(BUZZER_PIN, 0);
}

// Tone table (locked):
//   weight stable : 1568 Hz, 80 ms chirp
//   fresh         : 1047 -> 1319 Hz, 120 ms each (ascending)
//   sell_today    : 880 Hz, 200 ms
//   wilted        : 587 -> 440 Hz, 150 ms each (descending)
//   error         : 220 Hz, 500 ms
void playFeedbackTone(const String &tone) {
  if (tone == "fresh") {
    playTone(1047, 120);
    playTone(1319, 120);
  } else if (tone == "sell_today") {
    playTone(880, 200);
  } else if (tone == "wilted") {
    playTone(587, 150);
    playTone(440, 150);
  } else if (tone == "error") {
    playTone(220, 500);
  }
}

// ---- http ----

void postWeight(float grams, bool stable) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(String(API_BASE) + "/api/v1/ingest/weight");
  http.addHeader("Content-Type", "application/json");

  // Payload matches the backend's WeightIngest model exactly.
  JsonDocument doc;
  doc["station_id"] = STATION_ID;
  doc["weight_grams"] = grams;
  doc["stable"] = stable;
  String body;
  serializeJson(doc, body);

  int status = http.POST(body);
  if (status != 200) {
    Serial.printf("ingest/weight -> HTTP %d\n", status);
  }
  http.end();
}

void pollFeedback() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(String(API_BASE) + "/api/v1/station/feedback?station_id=" STATION_ID);
  int status = http.GET();
  if (status == 200) {
    JsonDocument doc;
    if (deserializeJson(doc, http.getString()) == DeserializationError::Ok) {
      const char *tone = doc["tone"] | "none";
      if (strcmp(tone, "none") != 0) {
        Serial.printf("feedback tone: %s\n", tone);
        playFeedbackTone(String(tone));
      }
    }
  }
  http.end();
}

// ---- stability ----

float windowAverage() {
  float sum = 0;
  for (int i = 0; i < windowCount; i++) sum += window[i];
  return windowCount > 0 ? sum / windowCount : 0;
}

float windowSpread() {
  if (windowCount == 0) return 1e9f;
  float lo = window[0], hi = window[0];
  for (int i = 1; i < windowCount; i++) {
    if (window[i] < lo) lo = window[i];
    if (window[i] > hi) hi = window[i];
  }
  return hi - lo;
}

void loop() {
  unsigned long now = millis();

  if (now - lastReadAt >= READ_INTERVAL_MS) {
    lastReadAt = now;

    float grams = scale.get_units(1);
    window[windowIndex] = grams;
    windowIndex = (windowIndex + 1) % WINDOW_SIZE;
    if (windowCount < WINDOW_SIZE) windowCount++;

    float avg = windowAverage();
    bool spreadOk = windowCount == WINDOW_SIZE && windowSpread() < STABLE_SPREAD_G;

    if (spreadOk) {
      if (spreadOkSince == 0) spreadOkSince = now;
      if (!stableReported && now - spreadOkSince >= STABLE_HOLD_MS) {
        stableReported = true;
        postWeight(avg, true);
        playTone(1568, 80); // stable chirp
      }
    } else {
      spreadOkSince = 0;
      stableReported = false;
      if (now - lastUnstablePostAt >= UNSTABLE_POST_INTERVAL_MS) {
        lastUnstablePostAt = now;
        postWeight(avg, false);
      }
    }
  }

  if (now - lastFeedbackPollAt >= FEEDBACK_POLL_INTERVAL_MS) {
    lastFeedbackPollAt = now;
    pollFeedback();
  }
}
