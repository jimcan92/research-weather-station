/**
 * sensors.cpp — Sensor reading implementation
 *
 * All sensors are powered via a MOSFET gate (PIN_SENSOR_PWR)
 * to eliminate quiescent current drain during deep sleep.
 */

#include "sensors.h"

// ── Sensor libraries ───────────────────────────────────────────────
#if HAS_BME280
#include <Adafruit_BME280.h>
Adafruit_BME280 bme;
#endif

#if HAS_DS18B20
#include <OneWire.h>
#include <DallasTemperature.h>
OneWire oneWire(PIN_ONEWIRE);
DallasTemperature ds18b20(&oneWire);
#endif

// ── Rain gauge (pulse counter via interrupt) ───────────────────────
#if HAS_RAIN_GAUGE
static volatile uint16_t rainTips = 0;

void IRAM_ATTR rainISR() {
  rainTips++;
}
#endif

// ── Anemometer (pulse counter via interrupt) ───────────────────────
#if HAS_ANEMOMETER
static volatile uint16_t windPulses = 0;
static volatile uint32_t windStartMillis = 0;

void IRAM_ATTR windISR() {
  if (windPulses == 0) {
    windStartMillis = millis();
  }
  windPulses++;
}
#endif

// ── Public API ─────────────────────────────────────────────────────

void sensorsInit() {
#if HAS_BME280
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  if (!bme.begin(0x76)) {
    Serial.println("BME280 not found at 0x76, trying 0x77...");
    if (!bme.begin(0x77)) {
      Serial.println("BME280 not found!");
    }
  } else {
    Serial.println("BME280 ready");
  }
#endif

#if HAS_DS18B20
  ds18b20.begin();
  Serial.print("DS18B20 devices: ");
  Serial.println(ds18b20.getDeviceCount());
#endif

#if HAS_RAIN_GAUGE
  pinMode(PIN_RAIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_RAIN), rainISR, FALLING);
  rainTips = 0;
  Serial.println("Rain gauge ready");
#endif

#if HAS_ANEMOMETER
  pinMode(PIN_WIND_SPEED, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_WIND_SPEED), windISR, FALLING);
  windPulses = 0;
  windStartMillis = 0;
  Serial.println("Anemometer ready");
#endif

  // MOSFET gate: start LOW (sensors off)
  pinMode(PIN_SENSOR_PWR, OUTPUT);
  digitalWrite(PIN_SENSOR_PWR, LOW);
}

void sensorsPowerOn() {
  digitalWrite(PIN_SENSOR_PWR, HIGH);
  delay(50);  // Let voltage stabilize
}

void sensorsPowerOff() {
  digitalWrite(PIN_SENSOR_PWR, LOW);
}

SensorData sensorsRead(uint16_t nodeId) {
  SensorData data = {0};
  data.node_id = nodeId;

  sensorsPowerOn();

#if HAS_BME280
  data.temperature = bme.readTemperature();
  data.humidity    = bme.readHumidity();
  data.pressure    = bme.readPressure() / 100.0F;  // Pa → hPa
  Serial.printf("BME280: %.1f°C, %.1f%%, %.1f hPa\n",
    data.temperature, data.humidity, data.pressure);
#endif

#if HAS_DS18B20
  ds18b20.requestTemperatures();
  float dsTemp = ds18b20.getTempCByIndex(0);
  if (dsTemp > -127.0) {
    // Use DS18B20 as primary temp if available (more accurate)
    data.temperature = dsTemp;
    Serial.printf("DS18B20: %.2f°C\n", dsTemp);
  }
#endif

  // Battery voltage
  int batRaw = analogRead(PIN_BATTERY);
  float batV = (batRaw / 4095.0) * 3.3 * BAT_DIVIDER;
  data.battery_v = batV;
  Serial.printf("Battery: %.2f V (raw=%d)\n", batV, batRaw);

#if HAS_RAIN_GAUGE
  data.rain_tips = rainTips;
  rainTips = 0;  // Reset counter
#endif

#if HAS_ANEMOMETER
  uint32_t elapsed = millis() - windStartMillis;
  if (elapsed > 0 && windPulses > 0) {
    float freq = (float)windPulses / (elapsed / 1000.0F);
    data.wind_speed = freq * WIND_FACTOR;
  }
  windPulses = 0;
  windStartMillis = 0;

#if HAS_WIND_VANE
  int dirRaw = analogRead(PIN_WIND_DIR);
  data.wind_dir = (uint16_t)((dirRaw / 4095.0F) * 360.0F);
  Serial.printf("Wind: %.1f m/s, %d° (raw=%d)\n",
    data.wind_speed, data.wind_dir, dirRaw);
#endif
#endif

#if HAS_SOIL_MOIST
  int soilRaw = analogRead(PIN_SOIL_MOIST);
  // Capacitive v1.2: ~1.2V dry → ~2.8V wet
  data.soil_moisture = (uint8_t)constrain(map(soilRaw, 1200, 2800, 0, 100), 0, 100);
  Serial.printf("Soil: %d%% (raw=%d)\n", data.soil_moisture, soilRaw);
#endif

  sensorsPowerOff();
  return data;
}

uint16_t getRainTips() {
#if HAS_RAIN_GAUGE
  uint16_t val = rainTips;
  rainTips = 0;
  return val;
#else
  return 0;
#endif
}

uint16_t getWindPulses() {
#if HAS_ANEMOMETER
  uint16_t val = windPulses;
  windPulses = 0;
  return val;
#else
  return 0;
#endif
}
