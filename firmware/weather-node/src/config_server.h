/**
 * config_server.h — WiFi Configuration Portal
 *
 * Creates a WiFi access point (AP) at boot. Connect your phone to
 * "WeatherNode-1" WiFi, then open http://192.168.4.1 to edit settings.
 * Changes are saved to NVS and applied on reboot.
 */

#ifndef CONFIG_SERVER_H
#define CONFIG_SERVER_H

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>

// AP settings
#define CONFIG_AP_SSID    "WeatherNode-1"
#define CONFIG_AP_TIMEOUT 300000   // 5 min — auto-close after this if no client

extern Preferences prefs;
extern WebServer server;
extern bool configMode;

// Runtime configuration (loaded from NVS)
struct RuntimeConfig {
  int  node_id;
  int  sleep_interval_s;
  float rain_tip_mm;
  bool has_bme280, has_ltr390, has_rain_gauge;
  bool has_anemometer, has_wind_vane, has_soil_moist;
  int  modbus_anemometer, modbus_wind_vane;
};
extern RuntimeConfig rtConfig;

/**
 * Start the configuration portal (WiFi AP + web server).
 * Blocks for up to CONFIG_AP_TIMEOUT ms or until user clicks "Save & Reboot".
 */
void configPortalStart();

/**
 * Handle web client requests (call in loop).
 * Returns true if portal is still active.
 */
bool configPortalLoop();

/**
 * Load saved configuration from NVS into the global config variables.
 * Call at boot, before using any config values.
 */
void configLoad();

/**
 * Save current config to NVS.
 */
void configSave();

#endif
