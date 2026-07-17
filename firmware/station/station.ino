// Panen Pay intake station — ESP32 firmware
// Targets Arduino IDE with ESP32 core 3.x.
// Libraries: HX711 (bogde), WiFi, HTTPClient, ArduinoJson,
//            Adafruit_SSD1306 + Adafruit_GFX (0.96" OLED).
//
// Wiring:
//   HX711 load cell amp: DT  -> GPIO16
//                        SCK -> GPIO4
//   Passive buzzer:      +   -> GPIO25
//   0.96" OLED (I2C):    SDA -> GPIO21
//                        SCL -> GPIO22   (VCC 3.3V, addr 0x3C)
//
// Behavior:
//   - 10 Hz scale reads, 8-sample moving average.
//   - stable = window spread < 5 g held for 1.5 s -> POST /ingest/weight, chirp.
//   - Polls /station/feedback every 2 s and plays the tier tone (read-once
//     server-side, so a tone never replays).
//   - OLED mirrors weight/stability/last tier at 4 Hz. It is display-only:
//     if the panel is absent the station runs headless (R7) — the web UI
//     remains the authoritative surface.

// ================== EDIT BEFORE FLASHING ==================
#define WIFI_SSID "your-hotspot-ssid"
#define WIFI_PASS "your-hotspot-password"
#define API_BASE "http://192.168.1.100:8000"
#define STATION_ID "station-1"

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <HX711.h>
#include <WiFi.h>
#include <Wire.h>

const int HX711_DT_PIN = 16;
const int HX711_SCK_PIN = 4;
const int BUZZER_PIN = 25;
const int OLED_SDA_PIN = 21;
const int OLED_SCL_PIN = 22;

const int OLED_WIDTH = 128;
const int OLED_HEIGHT = 64;
const uint8_t OLED_ADDR = 0x3C;

const unsigned long DISPLAY_INTERVAL_MS = 250;

Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
bool displayReady = false;
unsigned long lastDisplayAt = 0;
String lastTier = "";

const float CALIBRATION_FACTOR = 420.0f;

const unsigned long READ_INTERVAL_MS = 100;
const int WINDOW_SIZE = 8;
const float STABLE_SPREAD_G = 5.0f;
const unsigned long STABLE_HOLD_MS = 1500;
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

String tierLabel(const String &tier) {
  if (tier == "fresh") return "SEGAR";
  if (tier == "sell_today") return "JUAL HARI INI";
  if (tier == "wilted") return "LAYU";
  return "";
}

void splash(const String &line) {
  if (!displayReady) return;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("PANEN PAY");
  display.setCursor(0, 16);
  display.println(line);
  display.display();
}

void drawScreen(float grams, bool stable) {
  if (!displayReady) return;

  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("PANEN PAY");
  display.setCursor(98, 0);
  display.print(WiFi.status() == WL_CONNECTED ? "WIFI" : "----");
  display.drawLine(0, 10, 127, 10, SSD1306_WHITE);

  display.setTextSize(3);
  display.setCursor(0, 16);
  display.print(grams / 1000.0f, 2);
  display.setTextSize(1);
  display.print(" kg");

  display.setTextSize(1);
  display.setCursor(0, 42);
  display.print(stable ? "STABIL" : "menimbang...");

  if (lastTier.length() > 0) {
    display.drawLine(0, 52, 127, 52, SSD1306_WHITE);
    display.setCursor(0, 56);
    display.print(tierLabel(lastTier));
  }

  display.display();
}

void setup() {
  Serial.begin(115200);

  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);

  displayReady = display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR, true, false);
  if (!displayReady) {
    Serial.println("oled: not found at 0x3C — running headless");
  } else {
    splash("boot...");
  }

  scale.begin(HX711_DT_PIN, HX711_SCK_PIN);
  scale.set_scale(CALIBRATION_FACTOR);
  splash("tare - kosongkan");
  scale.tare();

  ledcAttach(BUZZER_PIN, 2000, 10);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("wifi: connecting");
  splash("wifi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.printf("\nwifi: connected, ip=%s\n", WiFi.localIP().toString().c_str());
  splash(WiFi.localIP().toString());
}

void playTone(int freqHz, int durationMs) {
  ledcWriteTone(BUZZER_PIN, freqHz);
  delay(durationMs);
  ledcWriteTone(BUZZER_PIN, 0);
}

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

void postWeight(float grams, bool stable) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(String(API_BASE) + "/api/v1/ingest/weight");
  http.addHeader("Content-Type", "application/json");

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

        if (strcmp(tone, "error") != 0) lastTier = String(tone);
        playFeedbackTone(String(tone));
      }
    }
  }
  http.end();
}

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
        playTone(1568, 80);
      }
    } else {
      spreadOkSince = 0;
      stableReported = false;
      if (now - lastUnstablePostAt >= UNSTABLE_POST_INTERVAL_MS) {
        lastUnstablePostAt = now;
        postWeight(avg, false);
      }
    }

    if (now - lastDisplayAt >= DISPLAY_INTERVAL_MS) {
      lastDisplayAt = now;
      drawScreen(avg, stableReported);
    }
  }

  if (now - lastFeedbackPollAt >= FEEDBACK_POLL_INTERVAL_MS) {
    lastFeedbackPollAt = now;
    pollFeedback();
  }
}
