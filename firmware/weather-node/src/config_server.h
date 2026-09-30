/**
 * config_server.h — Embedded Web Server, REST API & mDNS Configuration
 *
 * Runs Dual-Mode WiFi:
 *   - AP: "WeatherNode-1" (default IP: 192.168.4.1)
 *   - STA: Connects to home/office WiFi router
 *   - mDNS: http://weather.local (also accessible as http://weather.local on local network)
 *   - DNS Server: Captive portal port 53 mapping any request to 192.168.4.1
 */

#ifndef CONFIG_SERVER_H
#define CONFIG_SERVER_H

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <Preferences.h>
#include "packet.h"

// Network & Hostname settings
#define CONFIG_AP_SSID    "WeatherNode-1"
#define CONFIG_MDNS_HOST  "weather"        // http://weather.local

extern Preferences prefs;
extern WebServer server;
extern bool configMode;

// Runtime configuration (loaded from NVS)
struct RuntimeConfig {
  int   node_id;
  int   sleep_interval_s;
  float rain_tip_mm;
  bool  has_bme280, has_ltr390, has_rain_gauge;
  bool  has_anemometer, has_wind_vane, has_soil_moist;
  int   modbus_anemometer, modbus_wind_vane;
  char  sta_ssid[33];
  char  sta_pass[65];
};
extern RuntimeConfig rtConfig;

/** Start LittleFS, Dual WiFi (AP+STA), mDNS, DNS Server, and Core 0 Web Server Task */
void configPortalStart();

/** Handle incoming HTTP requests in loop() if not using FreeRTOS task */
bool configPortalLoop();

/** Update cached telemetry from sensor readings */
void updateTelemetryCache(const SensorData& data, float batV, uint32_t batRawMv, uint32_t soilRawMv);

/** Load saved configuration from NVS */
void configLoad();

/** Save current config to NVS */
void configSave();

#endif // CONFIG_SERVER_H
