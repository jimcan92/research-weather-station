/**
 * config.h — Node-specific configuration (ESP32-S3 N16R8)
 *
 * Edit this per deployed node. Every node gets a unique NODE_ID.
 * GPIO pin assignments should match your physical wiring.
 *
 * ESP32-S3 N16R8 constraints:
 *   - Octal PSRAM uses GPIO26-37 (unavailable)
 *   - Native USB uses GPIO19 (D-) / GPIO20 (D+)
 *   - Safe GPIOs: 1-18, 21, 38-48
 *   - ADC1: GPIO1-10
 *   - ADC2: GPIO11-20
 */

#ifndef CONFIG_H
#define CONFIG_H

// ── Node Identity ──────────────────────────────────────────────────
#define NODE_ID          1         // UNIQUE per node (1–255)
#define NODE_NAME        "Node 1"
#define FIRMWARE_VERSION "1.1.0-e22"

// ── Sleep ──────────────────────────────────────────────────────────
#define SLEEP_INTERVAL_S 5        // Deep sleep duration (seconds) — TEST MODE
#define SLEEP_INTERVAL_US (SLEEP_INTERVAL_S * 1000000ULL)
#define TEST_MODE         true     // Skip deep sleep + LoRa for testing

// ── LoRa Radio (Ebyte E22-900T22D, UART transparent mode) ──────────
// Air frequency/channel, air data rate and TX power are stored inside the
// E22 module. Both ends must be configured identically before deployment.
#define E22_UART_BAUD       9600
#define E22_AUX_TIMEOUT_MS  3000
#define E22_MODE_SETTLE_MS  50

// ── GPIO Pin Assignments (ESP32-S3 safe pins) ──────────────────────
// E22-900T22D UART LoRa
#define PIN_E22_M0       4
#define PIN_E22_M1       5
#define PIN_E22_RXD      6   // ESP32 TX -> E22 RXD
#define PIN_E22_TXD      7   // E22 TXD -> ESP32 RX
#define PIN_E22_AUX      8   // HIGH = module ready

// I2C bus (shared: BME280 @ 0x76/0x77, LTR390 @ 0x53)
#define PIN_I2C_SDA      1
#define PIN_I2C_SCL      2

// OneWire (DS18B20)
#define PIN_ONEWIRE      3

// Rain gauge — tipping bucket (interrupt pulse counter)
#define PIN_RAIN         10

// RS485 bus (Anemometer + Wind Vane — Modbus RTU)
// DIYMORE auto-direction module: no DE/RE pin needed
#define PIN_RS485_RX     18       // ESP32-S3 UART1 RX (from RS485 module TXD)
#define PIN_RS485_TX     17       // ESP32-S3 UART1 TX (to RS485 module RXD)

// RS485 Modbus slave IDs
#define MODBUS_ANEMOMETER 1       // Wind speed sensor
#define MODBUS_WIND_VANE  2       // Wind direction sensor

// Soil moisture (capacitive, analog)
#define PIN_SOIL_MOIST   13

// Battery voltage divider — ADC2
#define PIN_BATTERY      14

// Sensor power MOSFET gate (switches 12V_SW and sensor power rails)
#define PIN_SENSOR_PWR   15

// Status RGB LED (WS2812/SK6812 — onboard)
#define PIN_RGB_LED      48       // Common on ESP32-S3-DevKitC
#define NUM_RGB_LEDS     1        // Single onboard LED

// ── Spare pins ─────────────────────────────────────────────────────
// GPIO11, GPIO12, GPIO16, GPIO21, GPIO38-47

// ── Battery Divider (12V System) ────────────────────────────────────
// Actual PCB: R1 = 47kΩ (top), R2 = 10kΩ (bottom)
// V_adc = V_batt × R2/(R1+R2) = V_batt × 10/(47+10) = V_batt × 0.1754
// Divider ratio = (47 + 10) / 10 = 5.70
//
// Sense tap: 12V rail AFTER the PTC fuse but BEFORE the 1N5822 Schottky.
// Tapping after the diode adds its ~0.33 V forward drop, which on LiFePO4's
// flat discharge curve is worth roughly 20 percentage points of state of charge.
#define BAT_R1           47.0     // kΩ (top resistor)
#define BAT_R2           10.0     // kΩ (bottom resistor)
#define BAT_DIVIDER      ((BAT_R1 + BAT_R2) / BAT_R2)

// The ESP32 ADC jitters by a few mV, and 12 mV at the pack is already 1% of
// state of charge on LiFePO4. Oversample and average to settle it.
#define BAT_ADC_SAMPLES  32       // reads averaged per measurement
#define BAT_ADC_CACHE_MS 500      // reuse one averaged sample within a read cycle

// Residual variation after averaging is real load sag (WiFi bursts through the
// PTC fuse), so smooth it across cycles too.
#define BAT_ADC_EMA_ALPHA  0.25f  // 0 = frozen, 1 = no smoothing
#define BAT_ADC_EMA_SNAP_V 0.5f   // step larger than this snaps instead of slewing

// ── Calibration ─────────────────────────────────────────────────────
#define RAIN_TIP_MM      0.2794   // mm per bucket tip

// ── Sensor Toggle ───────────────────────────────────────────────────
#define HAS_BME280       true     // I2C 0x76/0x77 — temp, humidity, pressure
#define HAS_DS18B20      true     // OneWire — accurate temp
#define HAS_LTR390       false    // I2C 0x53 — UV index, ambient light
#define HAS_RAIN_GAUGE   true     // Tipping bucket, interrupt counter
#define HAS_ANEMOMETER   true     // RS485 Modbus — wind speed (m/s)
#define HAS_WIND_VANE    true     // RS485 Modbus — wind direction (°)
#define HAS_SOIL_MOIST   true     // Capacitive analog

#endif // CONFIG_H
