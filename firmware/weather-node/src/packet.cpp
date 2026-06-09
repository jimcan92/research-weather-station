/**
 * packet.cpp — LoRa packet serialization
 */

#include "packet.h"
#include <ArduinoJson.h>

#if PACKET_JSON

String packetToJson(const SensorData& data) {
  // Use ArduinoJson v7 syntax
  JsonDocument doc;

  doc["n"]  = data.node_id;
  doc["t"]  = roundf(data.temperature * 10) / 10.0;  // 1 decimal
  doc["h"]  = roundf(data.humidity * 10) / 10.0;
  doc["p"]  = roundf(data.pressure * 10) / 10.0;
  doc["b"]  = roundf(data.battery_v * 100) / 100.0;  // 2 decimals
  doc["r"]  = data.rain_tips;
  doc["ws"] = roundf(data.wind_speed * 10) / 10.0;
  doc["wd"] = data.wind_dir;
  doc["sm"] = data.soil_moisture;

  // Future fields — omit if not used to save bytes
  // doc["uv"] = data.uv_index;
  // doc["sr"] = data.solar_rad;

  String output;
  serializeJson(doc, output);
  return output;
}

#else

// ── Binary mode (compact, ~20 bytes) ───────────────────────────────

static uint16_t crc16_ccitt(const uint8_t* data, size_t len) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < len; i++) {
    crc ^= (uint16_t)data[i] << 8;
    for (uint8_t bit = 0; bit < 8; bit++) {
      if (crc & 0x8000)
        crc = (crc << 1) ^ 0x1021;
      else
        crc <<= 1;
    }
  }
  return crc;
}

size_t packetToBinary(const SensorData& data, uint8_t* buf, size_t buf_len) {
  if (buf_len < 20) return 0;

  buf[0]  = data.node_id & 0xFF;
  buf[1]  = (data.node_id >> 8) & 0xFF;
  buf[2]  = 0;  // packet type: full reading

  int16_t temp_x10 = (int16_t)(data.temperature * 10);
  buf[3]  = temp_x10 & 0xFF;
  buf[4]  = (temp_x10 >> 8) & 0xFF;

  uint16_t hum_x10 = (uint16_t)(data.humidity * 10);
  buf[5]  = hum_x10 & 0xFF;
  buf[6]  = (hum_x10 >> 8) & 0xFF;

  uint16_t pres_off = (uint16_t)(data.pressure - 800.0);
  buf[7]  = pres_off & 0xFF;
  buf[8]  = (pres_off >> 8) & 0xFF;

  uint16_t bat_x100 = (uint16_t)(data.battery_v * 100);
  buf[9]  = bat_x100 & 0xFF;
  buf[10] = (bat_x100 >> 8) & 0xFF;

  buf[11] = data.rain_tips & 0xFF;
  buf[12] = (data.rain_tips >> 8) & 0xFF;

  uint16_t ws_x10 = (uint16_t)(data.wind_speed * 10);
  buf[13] = ws_x10 & 0xFF;
  buf[14] = (ws_x10 >> 8) & 0xFF;

  buf[15] = data.wind_dir & 0xFF;
  buf[16] = (data.wind_dir >> 8) & 0xFF;

  buf[17] = data.soil_moisture;

  uint16_t crc = crc16_ccitt(buf, 18);
  buf[18] = crc & 0xFF;
  buf[19] = (crc >> 8) & 0xFF;

  return 20;
}

#endif // PACKET_JSON
