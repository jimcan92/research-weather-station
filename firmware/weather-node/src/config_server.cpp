/**
 * config_server.cpp — LittleFS SvelteKit Web Server, REST API, DNS & FreeRTOS Core 0 Task
 */

#include "config_server.h"
#include "config.h"
#include "sensors.h"
#include <LittleFS.h>
#include <ESPmDNS.h>
#include <DNSServer.h>
#include <ArduinoJson.h>
#include <Wire.h>

// ── NVS Keys ──────────────────────────────────────────────────────
static const char* NVS_NS = "weather";

// ── Runtime config instance ───────────────────────────────────────
RuntimeConfig rtConfig;

// ── Globals ───────────────────────────────────────────────────────
Preferences prefs;
WebServer   server(80);
DNSServer   dnsServer;
bool        configMode = false;
static bool littleFsMounted = false;
static TaskHandle_t webServerTaskHandle = NULL;

// ── Thread-Safe Telemetry Cache ───────────────────────────────────
struct TelemetryCache {
  SensorData    data;
  float         battery_v;
  uint32_t      battery_raw_mv;
  uint32_t      soil_raw_mv;
  float         ds18b20_temp;
  unsigned long last_update;
};

static TelemetryCache cachedTelem = {0};
static portMUX_TYPE telemMux = portMUX_INITIALIZER_UNLOCKED;

void updateTelemetryCache(const SensorData& data, float batV, uint32_t batRawMv, uint32_t soilRawMv) {
  portENTER_CRITICAL(&telemMux);
  cachedTelem.data           = data;
  cachedTelem.battery_v      = batV;
  cachedTelem.battery_raw_mv = batRawMv;
  cachedTelem.soil_raw_mv    = soilRawMv;
  cachedTelem.ds18b20_temp   = data.temperature;
  cachedTelem.last_update    = millis();
  portEXIT_CRITICAL(&telemMux);
}

// ── NVS Helpers ────────────────────────────────────────────────────
void configLoad() {
  prefs.begin(NVS_NS, false);

  rtConfig.node_id           = prefs.getInt("node_id", NODE_ID);
  rtConfig.sleep_interval_s  = prefs.getInt("sleep_s", SLEEP_INTERVAL_S);
  rtConfig.rain_tip_mm       = prefs.getFloat("rain_tip", RAIN_TIP_MM);
  rtConfig.has_bme280        = prefs.getBool("bme280", HAS_BME280);
  rtConfig.has_ltr390        = prefs.getBool("ltr390", HAS_LTR390);
  rtConfig.has_rain_gauge    = prefs.getBool("rain", HAS_RAIN_GAUGE);
  rtConfig.has_anemometer    = prefs.getBool("anemo", HAS_ANEMOMETER);
  rtConfig.has_wind_vane     = prefs.getBool("vane", HAS_WIND_VANE);
  rtConfig.has_soil_moist    = prefs.getBool("soil", HAS_SOIL_MOIST);
  rtConfig.modbus_anemometer = prefs.getInt("mb_anemo", MODBUS_ANEMOMETER);
  rtConfig.modbus_wind_vane  = prefs.getInt("mb_vane", MODBUS_WIND_VANE);

  String ssid = prefs.getString("sta_ssid", "");
  String pass = prefs.getString("sta_pass", "");
  strncpy(rtConfig.sta_ssid, ssid.c_str(), sizeof(rtConfig.sta_ssid) - 1);
  strncpy(rtConfig.sta_pass, pass.c_str(), sizeof(rtConfig.sta_pass) - 1);

  prefs.end();
  Serial.println("[Config] Loaded from NVS");
}

void configSave() {
  prefs.begin(NVS_NS, false);

  prefs.putInt("node_id", rtConfig.node_id);
  prefs.putInt("sleep_s", rtConfig.sleep_interval_s);
  prefs.putFloat("rain_tip", rtConfig.rain_tip_mm);
  prefs.putBool("bme280", rtConfig.has_bme280);
  prefs.putBool("ltr390", rtConfig.has_ltr390);
  prefs.putBool("rain", rtConfig.has_rain_gauge);
  prefs.putBool("anemo", rtConfig.has_anemometer);
  prefs.putBool("vane", rtConfig.has_wind_vane);
  prefs.putBool("soil", rtConfig.has_soil_moist);
  prefs.putInt("mb_anemo", rtConfig.modbus_anemometer);
  prefs.putInt("mb_vane", rtConfig.modbus_wind_vane);
  prefs.putString("sta_ssid", rtConfig.sta_ssid);
  prefs.putString("sta_pass", rtConfig.sta_pass);

  prefs.end();
  Serial.println("[Config] Saved to NVS");
}

// ── REST API Endpoints ─────────────────────────────────────────────

static void handleApiTelemetry() {
  TelemetryCache c;
  portENTER_CRITICAL(&telemMux);
  c = cachedTelem;
  portEXIT_CRITICAL(&telemMux);

  JsonDocument doc;
  doc["node_id"]        = rtConfig.node_id;
  doc["uptime_s"]       = millis() / 1000;
  doc["battery_v"]      = c.battery_v;
  doc["battery_raw_mv"] = c.battery_raw_mv;
  doc["bme_temp"]       = c.data.temperature;
  doc["bme_hum"]        = c.data.humidity;
  doc["bme_press"]      = c.data.pressure;
  doc["ds18b20_temp"]   = c.ds18b20_temp;
  doc["wind_speed"]     = c.data.wind_speed;
  doc["wind_dir"]       = c.data.wind_dir;
  doc["rain_tips"]      = c.data.rain_tips;
  doc["rain_mm"]        = c.data.rain_tips * rtConfig.rain_tip_mm;
  doc["soil_moist"]     = c.data.soil_moisture;
  doc["soil_raw_mv"]    = c.soil_raw_mv;
  doc["mosfet_on"]      = getMosfetState();
  doc["ap_ip"]          = WiFi.softAPIP().toString();
  doc["sta_ip"]         = (WiFi.status() == WL_CONNECTED) ? WiFi.localIP().toString() : "";
  doc["mdns"]           = "http://" + String(CONFIG_MDNS_HOST) + ".local";

  String output;
  serializeJson(doc, output);
  server.send(200, "application/json", output);
}

static void handleApiMosfet() {
  bool newState = !getMosfetState();
  setMosfetState(newState);

  JsonDocument doc;
  doc["mosfet_on"] = newState;
  String output;
  serializeJson(doc, output);
  server.send(200, "application/json", output);
}

static void handleApiScanI2c() {
  // sensorsScanI2C() owns I2C pin setup. Do NOT call pinMode() on the I2C pins
  // here: it detaches them from the Wire peripheral and breaks the bus until reboot.
  sensorsScanI2C();

  JsonDocument doc;
  JsonArray arr = doc["devices"].to<JsonArray>();

  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      char buf[32];
      if (addr == 0x76 || addr == 0x77) {
        snprintf(buf, sizeof(buf), "0x%02X (BME280/BMP280)", addr);
      } else if (addr == 0x53) {
        snprintf(buf, sizeof(buf), "0x%02X (LTR390)", addr);
      } else {
        snprintf(buf, sizeof(buf), "0x%02X", addr);
      }
      arr.add(buf);
    }
  }

  String output;
  serializeJson(doc, output);
  server.send(200, "application/json", output);
}

static void handleApiRainReset() {
  getRainTips(); // Reset volatile counter
  server.send(200, "application/json", "{\"success\":true}");
}

static void handleApiWifi() {
  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"error\":\"Missing body\"}");
    return;
  }

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, server.arg("plain"));
  if (err) {
    server.send(400, "application/json", "{\"error\":\"Invalid JSON\"}");
    return;
  }

  const char* s = doc["ssid"];
  const char* p = doc["password"];
  if (s) strncpy(rtConfig.sta_ssid, s, sizeof(rtConfig.sta_ssid) - 1);
  if (p) strncpy(rtConfig.sta_pass, p, sizeof(rtConfig.sta_pass) - 1);
  configSave();

  if (strlen(rtConfig.sta_ssid) > 0) {
    Serial.printf("[WiFi] Connecting to %s...\n", rtConfig.sta_ssid);
    WiFi.begin(rtConfig.sta_ssid, rtConfig.sta_pass);
  }

  server.send(200, "application/json", "{\"success\":true}");
}

// ── FreeRTOS WebServer Task (Core 0: Network & Web) ────────────────
static void webServerTask(void* pvParameters) {
  Serial.printf("[Task] Web Server running on Core %d\n", xPortGetCoreID());
  while (true) {
    if (configMode) {
      dnsServer.processNextRequest();
      server.handleClient();
    }
    vTaskDelay(pdMS_TO_TICKS(5));
  }
}

// ── Web Server Setup ───────────────────────────────────────────────

void configPortalStart() {
  configLoad();

  // 1. Mount LittleFS
  if (!LittleFS.begin(true)) {
    Serial.println("[LittleFS] Mount failed!");
    littleFsMounted = false;
  } else {
    Serial.println("[LittleFS] Mounted successfully");
    littleFsMounted = true;
  }

  // 2. Dual WiFi Mode (AP + STA)
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(CONFIG_AP_SSID);
  Serial.printf("[WiFi] AP Started: SSID='%s' IP=%s\n", CONFIG_AP_SSID, WiFi.softAPIP().toString().c_str());

  if (strlen(rtConfig.sta_ssid) > 0) {
    Serial.printf("[WiFi] STA Connecting to: %s\n", rtConfig.sta_ssid);
    WiFi.begin(rtConfig.sta_ssid, rtConfig.sta_pass);
  }

  // 3. DNS Server for Captive Portal (Port 53)
  dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
  dnsServer.start(53, "*", WiFi.softAPIP());
  Serial.println("[DNS] Captive Portal DNS started on port 53");

  // 4. mDNS (http://weather.local)
  if (MDNS.begin(CONFIG_MDNS_HOST)) {
    MDNS.addService("http", "tcp", 80);
    Serial.println();
    Serial.println("======================================================");
    Serial.printf("  Web Dashboard: http://%s.local\n", CONFIG_MDNS_HOST);
    Serial.printf("  AP Hotspot   : %s  ->  http://192.168.4.1\n", CONFIG_AP_SSID);
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("  Home WiFi IP : http://%s\n", WiFi.localIP().toString().c_str());
    }
    Serial.println("======================================================");
  }

  // 5. REST API Handlers
  server.on("/api/telemetry", HTTP_GET, handleApiTelemetry);
  server.on("/api/mosfet", HTTP_POST, handleApiMosfet);
  server.on("/api/scan-i2c", HTTP_GET, handleApiScanI2c);
  server.on("/api/rain/reset", HTTP_POST, handleApiRainReset);
  server.on("/api/wifi", HTTP_POST, handleApiWifi);

  // 6. Direct WebUI root handler
  server.on("/", HTTP_GET, []() {
    if (littleFsMounted && LittleFS.exists("/index.html")) {
      File f = LittleFS.open("/index.html", "r");
      server.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
      server.streamFile(f, "text/html");
      f.close();
    } else {
      server.send(404, "text/plain", "WebUI index.html not found in LittleFS");
    }
  });

  // 7. Static File Serving from LittleFS
  if (littleFsMounted) {
    server.serveStatic("/_app", LittleFS, "/_app");
    server.serveStatic("/favicon.png", LittleFS, "/favicon.png");
  }

  // 8. Captive portal detection & SPA fallback
  server.onNotFound([]() {
    String host = server.hostHeader();
    // Redirect external requests to 192.168.4.1
    if (!host.isEmpty() && host != "192.168.4.1" && !host.startsWith("weather.local")) {
      server.sendHeader("Location", "http://192.168.4.1/", true);
      server.send(302, "text/plain", "");
      return;
    }
    // Fallback for SPA routing
    if (littleFsMounted && LittleFS.exists("/index.html")) {
      File f = LittleFS.open("/index.html", "r");
      server.streamFile(f, "text/html");
      f.close();
    } else {
      server.send(404, "text/plain", "Not Found");
    }
  });

  server.begin();
  configMode = true;
  Serial.println("[HTTP] Server started on port 80");

  // 9. Launch FreeRTOS Task pinned to Core 0 (Network & Web)
  xTaskCreatePinnedToCore(
    webServerTask,
    "webServerTask",
    8192,
    NULL,
    1,
    &webServerTaskHandle,
    0 // Dedicated to Core 0
  );
  Serial.println("[Core 0] Dedicated Web Server task spawned.");
}

bool configPortalLoop() {
  if (!configMode) return false;
  // If task is running on Core 0, loop doesn't need to do anything,
  // but we keep handleClient() here if called directly.
  return true;
}
