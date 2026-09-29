/**
 * main.cpp — Weather Station Node (ESP32-S3 N16R8 + E22-900T22D)
 *
 * Status LED (WS2812/GPIO48) always active:
 *   Blue pulse   → booting
 *   Cyan breathe → config portal open
 *   Dim blue blip→ idle (portal closed / TEST_MODE)
 *   Yellow       → reading sensors (production)
 *   Green flash  → TX success
 *   Red blink    → error
 *   Off          → deep sleep
 */

#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include "config.h"
#include "config_server.h"
#include "lora.h"
#include "sensors.h"
#include "packet.h"

// ── RGB LED ───────────────────────────────────────────────────────
Adafruit_NeoPixel rgb(1, PIN_RGB_LED, NEO_GRB + NEO_KHZ800);

void ledSet(uint8_t r, uint8_t g, uint8_t b) {
  rgb.setPixelColor(0, rgb.Color(r, g, b)); rgb.show();
}
void ledOff()       { ledSet(0,0,0); }
void ledBoot()      { rgb.setBrightness(32); for(int i=0;i<128;i++){ledSet(0,0,i/2);delay(8);} ledOff(); }
void ledSensor()    { ledSet(255,140,0); }
void ledTXOk()      { ledSet(0,255,0); delay(300); ledOff(); }
void ledTXFail()    { ledSet(255,0,0); delay(500); ledOff(); }
void ledError()     { for(int i=0;i<3;i++){ledSet(255,0,0);delay(200);ledOff();delay(200);}}

// Breathing cyan for portal mode
void ledPortalHeartbeat() {
  static unsigned long last = 0;
  static int brightness = 0;
  static int dir = 1;
  if (millis() - last > 15) {
    last = millis();
    brightness += dir * 2;
    if (brightness >= 48) dir = -1;
    if (brightness <= 4)  dir = 1;
    ledSet(0, brightness, brightness);
  }
}

// ── Setup ──────────────────────────────────────────────────────────
void setup() {
  rgb.begin();
  rgb.setBrightness(32);
  ledOff();

  Serial.begin(115200);
  delay(2000);
  ledBoot();

  Serial.println();
  Serial.println("======================================");
  Serial.printf("  Weather Node %d — v%s\n", NODE_ID, FIRMWARE_VERSION);
  Serial.printf("  %s | %s\n",
    ESP.getChipModel(), TEST_MODE ? "TEST MODE" : "PRODUCTION");
  Serial.println("======================================");

#if TEST_MODE
  Serial.println("[TEST] Starting config portal...");
  configPortalStart();
#else
  configLoad();
  runProductionCycle();
#endif
}

// ── Production Cycle ───────────────────────────────────────────────
void runProductionCycle() {
  esp_sleep_wakeup_cause_t reason = esp_sleep_get_wakeup_cause();
  Serial.printf("Wake reason: %s\n",
    reason == ESP_SLEEP_WAKEUP_TIMER ? "timer" : "other");

  if (!loraInit()) {
    Serial.println("FATAL: LoRa init failed");
    ledError();
    loraSleep();
    esp_sleep_enable_timer_wakeup(rtConfig.sleep_interval_s * 1000000ULL);
    esp_deep_sleep_start();
  }

  ledSensor();
  sensorsInit();
  SensorData data = sensorsRead(rtConfig.node_id);

#if PACKET_JSON
  String payload = packetToJson(data);
  Serial.print("Payload: "); Serial.println(payload);
  loraSend(payload) ? (Serial.println("TX OK"), ledTXOk())
                    : (Serial.println("TX FAIL"), ledTXFail());
#else
  uint8_t buf[32];
  size_t len = packetToBinary(data, buf, sizeof(buf));
  loraSend(buf,len) ? (Serial.println("TX OK"), ledTXOk())
                    : (Serial.println("TX FAIL"), ledTXFail());
#endif

  ledOff();
  loraSleep();
  Serial.printf("Sleeping %d s...\n", rtConfig.sleep_interval_s);
  Serial.flush();
  esp_sleep_enable_timer_wakeup(rtConfig.sleep_interval_s * 1000000ULL);
  esp_deep_sleep_start();
}

// ── Loop ───────────────────────────────────────────────────────────
void loop() {
#if TEST_MODE
  if (configPortalLoop()) {
    // Portal active — breathe cyan
    ledPortalHeartbeat();
    delay(5);
    return;
  }
  // Portal closed — dim blue blip every 5s
  static unsigned long lastBlip = 0;
  if (millis() - lastBlip > 5000) {
    lastBlip = millis();
    ledSet(0, 0, 16); delay(60); ledOff();
  }
  delay(50);
#endif
}
