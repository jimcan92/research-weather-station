/**
 * main.cpp — Weather Station Node (ESP32-S3 N16R8 + E22-900T22D)
 *
 * Diagnostic Test Mode:
 *   - Live sensor telemetry output to Serial (115200 baud) every 2 seconds
 *   - Interactive Serial commands ('s'=scan I2C, 'r'=reset rain, 'm'=toggle MOSFET)
 *   - RGB LED (WS2812/GPIO48) green flash on each reading cycle
 */

#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include "config.h"
#include "config_server.h"
#include "lora.h"
#include "sensors.h"
#include "packet.h"

// ── RGB LED (Native ESP32-S3 Hardware RMT) ────────────────────────
void ledSet(uint8_t r, uint8_t g, uint8_t b) {
  neopixelWrite(PIN_RGB_LED, r, g, b);
}

void ledOff() {
  neopixelWrite(PIN_RGB_LED, 0, 0, 0);
}

void ledBoot() {
  for (int i = 0; i < 30; i++) {
    ledSet(0, 0, i);
    delay(10);
  }
  ledOff();
}

void ledSensor() {
  ledSet(0, 10, 15); // Calm dim cyan
}

void ledTXOk() {
  ledSet(0, 20, 0); // Gentle green blip
  delay(60);
  ledOff();
}

void ledTXFail() {
  ledSet(25, 0, 0); // Gentle red
  delay(150);
  ledOff();
}

void ledError() {
  for (int i = 0; i < 3; i++) {
    ledSet(25, 0, 0);
    delay(100);
    ledOff();
    delay(100);
  }
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
  loraSend(buf, len) ? (Serial.println("TX OK"), ledTXOk())
                     : (Serial.println("TX FAIL"), ledTXFail());
#endif

  ledOff();
  loraSleep();
  Serial.printf("Sleeping %d s...\n", rtConfig.sleep_interval_s);
  Serial.flush();
  esp_sleep_enable_timer_wakeup(rtConfig.sleep_interval_s * 1000000ULL);
  esp_deep_sleep_start();
}

// ── Setup ──────────────────────────────────────────────────────────
void setup() {
  ledOff();

  Serial.begin(115200);
  delay(1500);
  ledBoot();

  Serial.println();
  Serial.println("======================================================");
  Serial.printf("  Weather Node %d Diagnostic Firmware — v%s\n", NODE_ID, FIRMWARE_VERSION);
  Serial.printf("  Chip: %s | Mode: %s\n",
    ESP.getChipModel(), TEST_MODE ? "HARDWARE DIAGNOSTIC TEST" : "PRODUCTION");
  Serial.println("======================================================");

#if TEST_MODE
  Serial.println("\n[WEB] Starting LittleFS Web Server & Dual WiFi...");
  configPortalStart();
  Serial.println("\n[READY] Web Server ready. Accessible at:");
  Serial.println("  -> http://weather.local");
  Serial.println("  -> http://192.168.4.1 (Connect to WiFi 'WeatherNode-1')");

  Serial.println("\n[INIT] Initializing hardware peripherals and sensors...");
  sensorsInit();

  Serial.println("\nType commands in Serial Monitor:");
  Serial.println("  's' -> Re-scan I2C bus");
  Serial.println("  'r' -> Reset rain gauge tips count");
  Serial.println("  'm' -> Toggle MOSFET sensor power switch");
  Serial.println("------------------------------------------------------\n");
#else
  configLoad();
  runProductionCycle();
#endif
}

// ── Diagnostic Loop (Runs when TEST_MODE is true) ──────────────────
#if TEST_MODE
static unsigned long lastReadingTime = 0;
static bool mosfetState = true;

void handleSerialCommands() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 's' || c == 'S') {
      Serial.println("\n--- MANUAL I2C RESCAN ---");
      sensorsScanI2C();
      Serial.println("-------------------------\n");
    } else if (c == 'r' || c == 'R') {
      getRainTips(); // Reset counter
      Serial.println("\n[Rain] Tips counter reset to 0.\n");
    } else if (c == 'm' || c == 'M') {
      mosfetState = !mosfetState;
      if (mosfetState) {
        sensorsPowerOn();
        Serial.println("\n[MOSFET] Power rail turned ON (HIGH).\n");
      } else {
        sensorsPowerOff();
        Serial.println("\n[MOSFET] Power rail turned OFF (LOW).\n");
      }
    }
  }
}
#endif

void loop() {
#if TEST_MODE
  configPortalLoop();
  handleSerialCommands();

  if (!isBmeWorking()) {
    static unsigned long lastI2cRetry = 0;
    if (millis() - lastI2cRetry >= 3000) {
      lastI2cRetry = millis();
      sensorsScanI2C();
    }
  }

  if (millis() - lastReadingTime >= 2000) {
    lastReadingTime = millis();

    ledSensor();
    SensorData d = sensorsRead(NODE_ID);

    // Read the averaged ADC sample FIRST, then derive both the pack voltage and
    // the raw-mV readout from that same cached sample — otherwise the two
    // numbers shown side by side come from different, noisy conversions.
    uint32_t batRawMv = readBatteryRawMilliVolts();
    float batV = readBatteryVoltage();
    uint32_t soilRawMv = analogReadMilliVolts(PIN_SOIL_MOIST);

    // Update thread-safe cache for Core 0 Web Server
    updateTelemetryCache(d, batV, batRawMv, soilRawMv);

    Serial.println("======================================================");
    Serial.printf(" [DIAGNOSTIC] Node %d Telemetry | Up: %lu s\n", NODE_ID, millis() / 1000);
    Serial.println("======================================================");
    Serial.printf(" Battery Voltage : %.2f V  (ADC raw: %u mV)\n", batV, batRawMv);
    Serial.printf(" MOSFET Switch   : %s (GPIO%d)\n", mosfetState ? "ON (12V_SW active)" : "OFF", PIN_SENSOR_PWR);
    Serial.printf(" BME280 Readings : %.1f °C  |  %.1f %%  |  %.1f hPa\n", d.temperature, d.humidity, d.pressure);
    Serial.printf(" Rain Gauge Tips : %u tips (%.2f mm)\n", d.rain_tips, d.rain_tips * RAIN_TIP_MM);

    if (d.wind_speed >= 0.0f) {
      Serial.printf(" RS485 Wind Speed: %.1f m/s (Slave ID %d OK)\n", d.wind_speed, MODBUS_ANEMOMETER);
    } else {
      Serial.printf(" RS485 Wind Speed: TIMEOUT / NO RESPONSE (Slave ID %d)\n", MODBUS_ANEMOMETER);
    }

    if (d.wind_dir <= 360) {
      Serial.printf(" RS485 Wind Dir  : %u ° (Slave ID %d OK)\n", d.wind_dir, MODBUS_WIND_VANE);
    } else {
      Serial.printf(" RS485 Wind Dir  : TIMEOUT / NO RESPONSE (Slave ID %d)\n", MODBUS_WIND_VANE);
    }

    Serial.printf(" Soil Moisture   : %u %%  (ADC raw: %u mV)\n", d.soil_moisture, soilRawMv);
    Serial.println("------------------------------------------------------");
    Serial.printf(" JSON Payload    : %s\n", packetToJson(d).c_str());
    Serial.println("======================================================\n");

    ledTXOk(); // Green flash to indicate successful cycle
  }
#endif
}
