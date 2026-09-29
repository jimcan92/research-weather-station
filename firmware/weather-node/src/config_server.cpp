/**
 * config_server.cpp — WiFi Configuration Portal implementation
 */

#include "config_server.h"
#include "config.h"

// ── NVS Keys ──────────────────────────────────────────────────────
static const char* NVS_NS = "weather";

// ── Runtime config instance ───────────────────────────────────────
RuntimeConfig rtConfig;

// ── Globals ───────────────────────────────────────────────────────
Preferences prefs;
WebServer   server(80);
bool        configMode = false;

static bool alwaysPortal = false;  // Auto-close after timeout

// ── HTML Page ─────────────────────────────────────────────────────
static const char HTML_HEAD[] = R"raw(
<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Weather Node Config</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:#1a1a2e;color:#e0e0e0;padding:16px;max-width:480px;margin:auto}
h1{color:#00d4ff;font-size:1.3em;margin-bottom:16px;text-align:center}
h2{color:#00d4ff;font-size:1.1em;margin:20px 0 10px;border-bottom:1px solid #333;padding-bottom:5px}
label{display:block;font-size:0.9em;margin:12px 0 4px;color:#aaa}
input,select{width:100%;padding:10px;background:#16213e;border:1px solid #333;color:#fff;border-radius:6px;font-size:1em}
input:focus,select:focus{border-color:#00d4ff;outline:none}
.row{display:flex;gap:8px}
.row>div{flex:1}
.toggle{display:flex;align-items:center;justify-content:space-between;padding:8px 0}
.toggle input{width:48px;height:26px;accent-color:#00d4ff}
button{width:100%;padding:14px;background:#00d4ff;color:#000;border:none;border-radius:8px;font-size:1.1em;font-weight:bold;margin:20px 0;cursor:pointer}
button:hover{background:#00b8e6}
.info{text-align:center;color:#666;font-size:0.8em;margin-top:10px}
.saved{background:#0f3460;padding:10px;border-radius:6px;text-align:center;color:#00ff88;margin:10px 0}
</style></head><body>
<h1>⚙️ Weather Node Config</h1>
)raw";

static const char HTML_FOOT[] = R"raw(
<br><div class="info">ESP32-S3 N16R8 | Weather Station v1.0</div>
</body></html>
)raw";

// ── NVS Helpers ────────────────────────────────────────────────────
void configLoad() {
  prefs.begin(NVS_NS, false);

  rtConfig.node_id          = prefs.getInt("node_id", NODE_ID);
  rtConfig.sleep_interval_s = prefs.getInt("sleep_s", SLEEP_INTERVAL_S);
  rtConfig.rain_tip_mm      = prefs.getFloat("rain_tip", RAIN_TIP_MM);
  rtConfig.has_bme280       = prefs.getBool("bme280", HAS_BME280);
  rtConfig.has_ltr390       = prefs.getBool("ltr390", HAS_LTR390);
  rtConfig.has_rain_gauge   = prefs.getBool("rain", HAS_RAIN_GAUGE);
  rtConfig.has_anemometer   = prefs.getBool("anemo", HAS_ANEMOMETER);
  rtConfig.has_wind_vane    = prefs.getBool("vane", HAS_WIND_VANE);
  rtConfig.has_soil_moist   = prefs.getBool("soil", HAS_SOIL_MOIST);
  rtConfig.modbus_anemometer = prefs.getInt("mb_anemo", MODBUS_ANEMOMETER);
  rtConfig.modbus_wind_vane  = prefs.getInt("mb_vane", MODBUS_WIND_VANE);

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

  prefs.end();

  Serial.println("[Config] Saved to NVS");
}

// ── Web Handlers ────────────────────────────────────────────────────

static String makePage(String content) {
  return String(HTML_HEAD) + content + HTML_FOOT;
}

static void handleRoot() {
  String html = R"raw(
<form method="POST" action="/save">

<h2>📡 E22-900T22D LoRa</h2>
<div class="info" style="text-align:left;line-height:1.6">
UART 9600 baud · transparent mode<br>
M0=GPIO4 · M1=GPIO5 · RXD=GPIO6 · TXD=GPIO7 · AUX=GPIO8<br>
Air channel/rate/power are stored in the E22 module and must match the gateway.
</div>

<h2>⏱️ Sleep</h2>
<label>Sleep Interval (seconds)</label>
<input type="number" name="sleep_s" value=")raw" + String(rtConfig.sleep_interval_s) + R"raw(" min="5" max="3600">
<label>Node ID (1-255)</label>
<input type="number" name="node_id" value=")raw" + String(rtConfig.node_id) + R"raw(" min="1" max="255">

<h2>🌧️ Rain Gauge</h2>
<label>mm per tip</label>
<input type="number" name="rain_tip" value=")raw" + String(rtConfig.rain_tip_mm, 4) + R"raw(" step="0.0001" min="0.01" max="5">

<h2>🔌 Sensors Enabled</h2>
<div class="toggle"><span>BME280 (Temp/Hum/Press)</span>
  <input type="checkbox" name="bme280")raw" + String(rtConfig.has_bme280 ? " checked" : "") + R"raw(></div>
<div class="toggle"><span>LTR390 (UV/Ambient)</span>
  <input type="checkbox" name="ltr390")raw" + String(rtConfig.has_ltr390 ? " checked" : "") + R"raw(></div>
<div class="toggle"><span>Rain Gauge</span>
  <input type="checkbox" name="rain")raw" + String(rtConfig.has_rain_gauge ? " checked" : "") + R"raw(></div>
<div class="toggle"><span>Anemometer (Wind Speed)</span>
  <input type="checkbox" name="anemo")raw" + String(rtConfig.has_anemometer ? " checked" : "") + R"raw(></div>
<div class="toggle"><span>Wind Vane (Direction)</span>
  <input type="checkbox" name="vane")raw" + String(rtConfig.has_wind_vane ? " checked" : "") + R"raw(></div>
<div class="toggle"><span>Soil Moisture</span>
  <input type="checkbox" name="soil")raw" + String(rtConfig.has_soil_moist ? " checked" : "") + R"raw(></div>

<h2>🔢 Modbus Addresses</h2>
<div class="row">
<div><label>Anemometer ID</label><input type="number" name="mb_anemo" value=")raw" + String(rtConfig.modbus_anemometer) + R"raw(" min="1" max="247"></div>
<div><label>Wind Vane ID</label><input type="number" name="mb_vane" value=")raw" + String(rtConfig.modbus_wind_vane) + R"raw(" min="1" max="247"></div>
</div>

<button type="submit">💾 Save & Reboot</button>
</form>
<form method="GET" action="/close" style="margin-top:-10px">
<button type="submit" style="background:#444;color:#fff">🚪 Close Portal (go to production)</button>
</form>
)raw";

  server.send(200, "text/html", makePage(html));
}

static void handleSave() {
  // Read form values
  if (server.hasArg("sleep_s"))     rtConfig.sleep_interval_s = server.arg("sleep_s").toInt();
  if (server.hasArg("node_id"))     rtConfig.node_id     = server.arg("node_id").toInt();
  if (server.hasArg("rain_tip"))    rtConfig.rain_tip_mm = server.arg("rain_tip").toFloat();

  rtConfig.has_bme280     = server.hasArg("bme280");
  rtConfig.has_ltr390     = server.hasArg("ltr390");
  rtConfig.has_rain_gauge = server.hasArg("rain");
  rtConfig.has_anemometer = server.hasArg("anemo");
  rtConfig.has_wind_vane  = server.hasArg("vane");
  rtConfig.has_soil_moist = server.hasArg("soil");

  if (server.hasArg("mb_anemo")) rtConfig.modbus_anemometer = server.arg("mb_anemo").toInt();
  if (server.hasArg("mb_vane"))  rtConfig.modbus_wind_vane  = server.arg("mb_vane").toInt();

  configSave();

  String html = R"raw(
<div class="saved">✅ Settings saved! Rebooting...</div>
<p style="text-align:center;color:#aaa">Reconnect to WeatherNode-1 WiFi after reboot.</p>
<script>setTimeout(function(){fetch('/reboot')},2000)</script>
)raw";
  server.send(200, "text/html", makePage(html));
}

static void handleReboot() {
  server.send(200, "text/plain", "OK");
  delay(500);
  ESP.restart();
}

static void handleClose() {
  server.send(200, "text/html", makePage(
    "<div class='saved'>🚪 Portal closed. LED off.</div>"
    "<p style='text-align:center;color:#aaa'>ESP32 now in idle mode.</p>"
  ));
  delay(1000);
  server.stop();
  WiFi.softAPdisconnect(true);
  configMode = false;
}

// ── Portal Start / Loop ────────────────────────────────────────────

void configPortalStart() {
  configLoad();

  // Start AP
  WiFi.mode(WIFI_AP);
  WiFi.softAP(CONFIG_AP_SSID);

  Serial.println();
  Serial.println("══════════════════════════════════════");
  Serial.println("  ⚙️  CONFIG PORTAL ACTIVE");
  Serial.println("══════════════════════════════════════");
  Serial.printf("  WiFi: %s\n", CONFIG_AP_SSID);
  Serial.println("  Open: http://192.168.4.1");
  Serial.println("  Timeout: 5 minutes");
  Serial.println("══════════════════════════════════════");

  // Web server routes
  server.on("/", handleRoot);
  server.on("/save", HTTP_POST, handleSave);
  server.on("/reboot", handleReboot);
  server.on("/close", handleClose);
  server.begin();

  configMode = true;
}

bool configPortalLoop() {
  if (!configMode) return false;

  server.handleClient();

  // Auto-close after timeout (only if not alwaysPortal)
  static unsigned long startTime = millis();
  if (!alwaysPortal && millis() - startTime > CONFIG_AP_TIMEOUT) {
    Serial.println("[Config] Portal timeout — closing");
    server.stop();
    WiFi.softAPdisconnect(true);
    configMode = false;
    return false;
  }

  return true;
}
