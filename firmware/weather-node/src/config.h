/**
 * config.h — Node-specific configuration
 *
 * Edit this per deployed node. Every node gets a unique NODE_ID.
 * GPIO pin assignments should match your physical wiring.
 */

#ifndef CONFIG_H
#define CONFIG_H

// ── Node Identity ──────────────────────────────────────────────────
#define NODE_ID          1         // UNIQUE per node (1–255)
#define NODE_NAME        "Node 1"
#define FIRMWARE_VERSION "1.0.0"

// ── Sleep ──────────────────────────────────────────────────────────
#define SLEEP_INTERVAL_S 120       // Deep sleep duration (seconds)
#define SLEEP_INTERVAL_US (SLEEP_INTERVAL_S * 1000000ULL)

// ── LoRa Radio (SX1276/SX1278) ─────────────────────────────────────
#define LORA_FREQ        915.0     // MHz — Philippines ISM band
#define LORA_BW          125.0     // kHz bandwidth
#define LORA_SF          9         // Spreading factor (7–12)
#define LORA_CR          7         // Coding rate (5–8)
#define LORA_POWER       17        // dBm output (2–17)
#define LORA_PREAMBLE    8         // Preamble length
#define LORA_SYNC_WORD   0x12      // RADIOLIB_SX127X_SYNC_WORD

// ── GPIO Pin Assignments ───────────────────────────────────────────
// LoRa SPI
#define PIN_LORA_NSS     5
#define PIN_LORA_SCK     18
#define PIN_LORA_MOSI    23
#define PIN_LORA_MISO    19
#define PIN_LORA_RST     14
#define PIN_LORA_DIO0    26

// I2C bus (BME280, etc.)
#define PIN_I2C_SDA      21
#define PIN_I2C_SCL      22

// OneWire (DS18B20)
#define PIN_ONEWIRE      4

// Rain gauge (pulse counter)
#define PIN_RAIN         34       // ADC1 — safe in deep sleep

// Anemometer (pulse counter)
#define PIN_WIND_SPEED   35       // ADC1

// Wind direction (analog potentiometer)
#define PIN_WIND_DIR     36       // ADC1 (VP)

// Soil moisture (analog)
#define PIN_SOIL_MOIST   39       // ADC1 (VN)

// Battery voltage divider
#define PIN_BATTERY      33       // ADC1

// Sensor power MOSFET gate
#define PIN_SENSOR_PWR   32

// ── Battery Divider ─────────────────────────────────────────────────
#define BAT_R1           100.0    // kΩ (top resistor)
#define BAT_R2           220.0    // kΩ (bottom resistor)
// ratio = (R1 + R2) / R2
#define BAT_DIVIDER      ((BAT_R1 + BAT_R2) / BAT_R2)

// ── Calibration ─────────────────────────────────────────────────────
#define RAIN_TIP_MM      0.2794   // mm per bucket tip
#define WIND_FACTOR      2.4      // m/s per Hz (pulses/sec)

// ── Sensor Toggle ───────────────────────────────────────────────────
// Disable sensors you don't have to skip their init + read
#define HAS_BME280       true
#define HAS_DS18B20      true
#define HAS_RAIN_GAUGE   true
#define HAS_ANEMOMETER   true
#define HAS_WIND_VANE    true
#define HAS_SOIL_MOIST   true
#define HAS_UV_SOLAR     false    // Future expansion

#endif // CONFIG_H
