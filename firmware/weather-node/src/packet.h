/**
 * packet.h — LoRa packet structure and serialization
 *
 * Binary format (20 bytes):
 *   [0-1]  Node ID (uint16, little-endian)
 *   [2]    Packet type (0=full reading, 1=heartbeat, 2=alarm)
 *   [3-4]  Temperature × 10 (int16) — °C
 *   [5-6]  Humidity × 10 (uint16) — %
 *   [7-8]  Pressure - 800 (uint16) — hPa offset
 *   [9-10] Battery voltage × 100 (uint16) — V
 *   [11-12] Rain tips since last TX (uint16)
 *   [13-14] Wind speed × 10 (uint16) — m/s
 *   [15-16] Wind direction (uint16) — degrees
 *   [17]    Soil moisture (uint8) — % (0-100)
 *   [18-19] CRC-16/CCITT
 *
 * Alternate: JSON mode for debugging (toggleable via PACKET_JSON).
 */

#ifndef PACKET_H
#define PACKET_H

#include <stdint.h>

// Set to 1 for human-readable JSON packets (larger, easier to debug).
// Set to 0 for compact binary packets (smaller, less air time).
#define PACKET_JSON 1

// ── C++ API ────────────────────────────────────────────────────────
#ifdef __cplusplus

#include <Arduino.h>

struct SensorData {
  uint16_t node_id;
  float    temperature;    // °C
  float    humidity;       // %
  float    pressure;       // hPa
  float    battery_v;      // V
  uint16_t rain_tips;      // tips since last TX
  float    wind_speed;     // m/s
  uint16_t wind_dir;       // degrees (0-360)
  uint8_t  soil_moisture;  // %
  // Reserved for future
  float    uv_index;       // future
  float    solar_rad;      // W/m², future
};

/** Serialize SensorData into a buffer. Returns number of bytes written. */
#if PACKET_JSON
  String packetToJson(const SensorData& data);
#else
  size_t packetToBinary(const SensorData& data, uint8_t* buf, size_t buf_len);
#endif

#endif // __cplusplus
#endif // PACKET_H
