/**
 * main.cpp — Weather station node firmware
 *
 * Lifecycle:
 *   1. Wake from deep sleep (timer or external pin)
 *   2. Initialize LoRa + sensors
 *   3. Read all enabled sensors
 *   4. Serialize to JSON (or binary) and transmit via LoRa
 *   5. Enter deep sleep until next interval
 *
 * Connect serial monitor at 115200 baud to see debug output.
 * Set SLEEP_INTERVAL_S to 5 for testing, 120+ for production.
 */

#include <Arduino.h>
#include "config.h"
#include "lora.h"
#include "sensors.h"
#include "packet.h"

// ── Boot reason tracking ───────────────────────────────────────────
static void printWakeupReason() {
  esp_sleep_wakeup_cause_t reason = esp_sleep_get_wakeup_cause();
  Serial.print("Wake reason: ");
  switch (reason) {
    case ESP_SLEEP_WAKEUP_TIMER:
      Serial.println("timer");
      break;
    case ESP_SLEEP_WAKEUP_EXT0:
      Serial.println("external RTC IO");
      break;
    default:
      Serial.printf("other (%d)\n", reason);
  }
}

// ── Setup ──────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  // Small delay so serial monitor connects after flashing
  delay(100);

  Serial.println();
  Serial.println("══════════════════════════════════════");
  Serial.printf("  Weather Node %d — v%s\n", NODE_ID, FIRMWARE_VERSION);
  Serial.println("══════════════════════════════════════");

  printWakeupReason();

  // ── Init LoRa ──────────────────────────────────────────────────
  if (!loraInit()) {
    Serial.println("FATAL: LoRa init failed — sleeping and will retry");
    loraSleep();
    esp_sleep_enable_timer_wakeup(SLEEP_INTERVAL_US);
    esp_deep_sleep_start();
  }

  // ── Init sensors ───────────────────────────────────────────────
  sensorsInit();

  // ── Read sensors ───────────────────────────────────────────────
  SensorData data = sensorsRead(NODE_ID);

  // ── Serialize and transmit ─────────────────────────────────────
#if PACKET_JSON
  String payload = packetToJson(data);
  Serial.print("Payload: ");
  Serial.println(payload);

  if (loraSend(payload)) {
    Serial.println("TX success");
  } else {
    Serial.println("TX failed");
  }
#else
  uint8_t buf[32];
  size_t len = packetToBinary(data, buf, sizeof(buf));
  if (loraSend(buf, len)) {
    Serial.println("TX success");
  } else {
    Serial.println("TX failed");
  }
#endif

  // ── Deep sleep ─────────────────────────────────────────────────
  loraSleep();
  Serial.printf("Sleeping %d s...\n", SLEEP_INTERVAL_S);
  Serial.flush();  // Ensure all output before sleep

  esp_sleep_enable_timer_wakeup(SLEEP_INTERVAL_US);
  esp_deep_sleep_start();
}

void loop() {
  // Never reached — we deep sleep in setup().
  // If you remove deep sleep for testing, put the cycle here.
}
