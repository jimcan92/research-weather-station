/**
 * sensors.cpp — Sensor reading and hardware diagnostics implementation
 *
 * All sensors are powered via a MOSFET gate (PIN_SENSOR_PWR / GPIO15)
 * to eliminate quiescent current drain during deep sleep.
 */

#include "sensors.h"
#include <Wire.h>

// ── Sensor libraries ───────────────────────────────────────────────
#if HAS_BME280
#include <Adafruit_BME280.h>
#include <Adafruit_BMP280.h>
static Adafruit_BME280 bme;
static Adafruit_BMP280 bmp;
static bool hasBmeWorking = false;
static bool hasBmpWorking = false;
static uint8_t bmeAddress = 0;
#endif

#if HAS_DS18B20
#include <OneWire.h>
#include <DallasTemperature.h>
static OneWire oneWire(PIN_ONEWIRE);
static DallasTemperature ds18b20(&oneWire);
static int dsDeviceCount = 0;
#endif

// ── Rain gauge (pulse counter via interrupt) ───────────────────────
#if HAS_RAIN_GAUGE
static volatile uint16_t rainTips = 0;

void IRAM_ATTR rainISR() {
  rainTips++;
}
#endif

// ── RS485 Wind Sensors (Modbus RTU over UART1) ─────────────────────
#if HAS_ANEMOMETER || HAS_WIND_VANE
#include <ModbusMaster.h>
static HardwareSerial rs485Serial(1);
static ModbusMaster mbAnemo;
static ModbusMaster mbVane;
static bool rs485Initialized = false;
#endif

// ── Power Management ───────────────────────────────────────────────
static bool mosfetActive = false;

void sensorsPowerOn() {
  digitalWrite(PIN_SENSOR_PWR, HIGH);
  mosfetActive = true;
  delay(50); // 50ms stabilization for 12V_SW and 3.3V sensors
}

void sensorsPowerOff() {
  digitalWrite(PIN_SENSOR_PWR, LOW);
  mosfetActive = false;
}

bool getMosfetState() {
  return mosfetActive;
}

void setMosfetState(bool on) {
  if (on) sensorsPowerOn();
  else sensorsPowerOff();
}

// ── I2C Bus Scanner ────────────────────────────────────────────────
// The I2C pins are owned by the Wire peripheral. Never call pinMode() on them
// after Wire.begin(): that detaches them from the peripheral and the bus stops
// ACKing until reboot. Attach the bus once here, then only ever scan.
static bool i2cStarted = false;

void sensorsScanI2C() {
  Serial.println("[I2C] Scanning bus (SDA=GPIO1, SCL=GPIO2)...");

  if (!i2cStarted) {
    pinMode(PIN_I2C_SDA, INPUT_PULLUP);
    pinMode(PIN_I2C_SCL, INPUT_PULLUP);
    delay(10);
    if (digitalRead(PIN_I2C_SDA) == LOW || digitalRead(PIN_I2C_SCL) == LOW) {
      Serial.println("  -> WARNING: I2C bus is stuck LOW! (SDA or SCL grounded or 3.3V bus unpowered).");
      Serial.println("  -> Check 12V power supply to terminal and ensure SDA/SCL are not swapped.");
      return;
    }

    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.setTimeOut(50);
    i2cStarted = true;
  }

  uint8_t count = 0;
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    uint8_t err = Wire.endTransmission();
    if (err == 0) {
      Serial.printf("  -> Found I2C device at 0x%02X", addr);
      if (addr == 0x76 || addr == 0x77) {
        Serial.print(" (BME280 / BMP280)");
#if HAS_BME280
        if (!hasBmeWorking && !hasBmpWorking) {
          if (bme.begin(addr, &Wire)) {
            hasBmeWorking = true;
            bmeAddress = addr;
            Serial.print(" -> Initialized OK!");
          } else if (bmp.begin(addr)) {
            hasBmpWorking = true;
            bmeAddress = addr;
            Serial.print(" -> Initialized BMP280 OK!");
          }
        }
#endif
      } else if (addr == 0x53) {
        Serial.print(" (LTR390)");
      }
      Serial.println();
      count++;
    }
  }
  if (count == 0) {
    Serial.println("  -> No I2C devices found! Check wiring and 3.3V power.");
  }
}

// ── Battery ADC Calibration ────────────────────────────────────────
// Two stages of conditioning, because LiFePO4's discharge curve is so flat that
// a few mV of ADC jitter becomes several % of apparent state of charge:
//
//   1. Oversample BAT_ADC_SAMPLES times, drop the extreme samples, average.
//      Kills the ADC's own noise.
//   2. Smooth the result with an EMA across read cycles. What survives step 1
//      is mostly REAL variation — WiFi current bursts sagging the pack through
//      the PTC fuse — which only a slower filter can remove.
//
// A large step (battery reconnected, load removed) snaps the filter instead of
// being slewed, so the reading never lags behind a genuinely new value.
//
// The averaged sample is cached for BAT_ADC_CACHE_MS so every caller in one read
// cycle (sensorsRead, the telemetry cache, the raw-mV readout) reports the SAME
// sample instead of three unrelated ones.
static uint32_t      batteryMvCache     = 0;
static unsigned long batteryMvCacheAt   = 0;
static float         batteryVoltsFilter = 0.0f;   // EMA of pack volts
static bool          batteryFilterValid = false;

// Take one oversampled conversion and advance the EMA exactly once.
static void batterySampleAndFilter() {
  uint32_t sum = 0;
  uint32_t lo  = UINT32_MAX;
  uint32_t hi  = 0;

  for (int i = 0; i < BAT_ADC_SAMPLES; i++) {
    uint32_t mv = analogReadMilliVolts(PIN_BATTERY);
    sum += mv;
    if (mv < lo) lo = mv;
    if (mv > hi) hi = mv;
    delayMicroseconds(200);
  }

  sum -= lo;  // discard the single lowest and
  sum -= hi;  // single highest sample as outliers

  batteryMvCache   = sum / (BAT_ADC_SAMPLES - 2);
  batteryMvCacheAt = millis();

  const float volts = (batteryMvCache * BAT_DIVIDER) / 1000.0f;

  float delta = volts - batteryVoltsFilter;
  if (delta < 0.0f) delta = -delta;

  if (!batteryFilterValid || delta > BAT_ADC_EMA_SNAP_V) {
    batteryVoltsFilter = volts;   // first reading, or a genuine step change
    batteryFilterValid = true;
  } else {
    batteryVoltsFilter += BAT_ADC_EMA_ALPHA * (volts - batteryVoltsFilter);
  }
}

uint32_t readBatteryRawMilliVolts() {
  unsigned long now = millis();
  if (batteryMvCacheAt == 0 || (now - batteryMvCacheAt) >= BAT_ADC_CACHE_MS) {
    batterySampleAndFilter();
  }
  return batteryMvCache;   // always the raw (unsmoothed) averaged sample
}

float readBatteryVoltage() {
  // Uses the ESP32 calibrated millivolts (eFuse ADC curve), averaged then smoothed.
  readBatteryRawMilliVolts();   // ensures one fresh sample + EMA step this cycle
  return batteryVoltsFilter;
}

// ── Soil Moisture ──────────────────────────────────────────────────
uint8_t readSoilMoisture() {
#if HAS_SOIL_MOIST
  uint32_t mv = analogReadMilliVolts(PIN_SOIL_MOIST);
  // Typical capacitive v1.2: ~2600mV dry air -> ~1200mV submerged in water
  if (mv >= 2600) return 0;
  if (mv <= 1200) return 100;
  return (uint8_t)map(mv, 2600, 1200, 0, 100);
#else
  return 0;
#endif
}

// ── RS485 Modbus Helpers ───────────────────────────────────────────
float readRS485WindSpeed() {
#if HAS_ANEMOMETER
  // Standard Modbus RTU wind speed: Slave ID 1, Read Holding Register 0x0000
  uint8_t result = mbAnemo.readHoldingRegisters(0x0000, 1);
  if (result == mbAnemo.ku8MBSuccess) {
    uint16_t raw = mbAnemo.getResponseBuffer(0);
    return raw / 10.0f; // 0.1 m/s resolution
  }
  // Only try register 0x0001 if slave responded with illegal data address
  if (result == mbAnemo.ku8MBIllegalDataAddress) {
    result = mbAnemo.readHoldingRegisters(0x0001, 1);
    if (result == mbAnemo.ku8MBSuccess) {
      uint16_t raw = mbAnemo.getResponseBuffer(0);
      return raw / 10.0f;
    }
  }
  return -1.0f; // Error / Timeout
#else
  return 0.0f;
#endif
}

uint16_t readRS485WindDirection() {
#if HAS_WIND_VANE
  // Standard Modbus RTU wind direction: Slave ID 2, Read Holding Register 0x0000
  uint8_t result = mbVane.readHoldingRegisters(0x0000, 1);
  if (result == mbVane.ku8MBSuccess) {
    return mbVane.getResponseBuffer(0); // 0-360 degrees
  }
  // Only try register 0x0001 if slave responded with illegal data address
  if (result == mbVane.ku8MBIllegalDataAddress) {
    result = mbVane.readHoldingRegisters(0x0001, 1);
    if (result == mbVane.ku8MBSuccess) {
      return mbVane.getResponseBuffer(0);
    }
  }
  return 0xFFFF; // Error / Timeout
#else
  return 0;
#endif
}

// ── Public Initialization ──────────────────────────────────────────
void sensorsInit() {
  // Configure MOSFET gate and power up sensors for detection
  pinMode(PIN_SENSOR_PWR, OUTPUT);
  sensorsPowerOn();

#if HAS_BME280
  // sensorsScanI2C() owns I2C pin setup and calls Wire.begin() exactly once.
  sensorsScanI2C();

  if (!i2cStarted) {
    Serial.println("[I2C] Bus lines are held LOW! (Check 3.3V power). Skipping BME280.");
  } else {
    // Try BME280 at 0x76 then 0x77
    if (bme.begin(0x76, &Wire)) {
      hasBmeWorking = true;
      bmeAddress = 0x76;
      Serial.println("[BME280] Connected at 0x76");
    } else if (bme.begin(0x77, &Wire)) {
      hasBmeWorking = true;
      bmeAddress = 0x77;
      Serial.println("[BME280] Connected at 0x77");
    } else {
      // Fallback: test if board has BMP280 (no humidity sensor)
      if (bmp.begin(0x76)) {
        hasBmpWorking = true;
        bmeAddress = 0x76;
        Serial.println("[BMP280] Connected at 0x76 (No Humidity)");
      } else if (bmp.begin(0x77)) {
        hasBmpWorking = true;
        bmeAddress = 0x77;
        Serial.println("[BMP280] Connected at 0x77 (No Humidity)");
      } else {
        Serial.println("[BME280] ERROR: Sensor not responding on 0x76/0x77");
      }
    }
  }
#endif

#if HAS_DS18B20
  ds18b20.begin();
  ds18b20.setWaitForConversion(false);
  dsDeviceCount = ds18b20.getDeviceCount();
  Serial.printf("[DS18B20] Devices found on GPIO%d: %d\n", PIN_ONEWIRE, dsDeviceCount);
#endif

#if HAS_RAIN_GAUGE
  pinMode(PIN_RAIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_RAIN), rainISR, FALLING);
  rainTips = 0;
  Serial.printf("[Rain] Interrupt attached to GPIO%d\n", PIN_RAIN);
#endif

#if HAS_SOIL_MOIST
  pinMode(PIN_SOIL_MOIST, INPUT);
  analogSetPinAttenuation(PIN_SOIL_MOIST, ADC_11db);
  Serial.printf("[Soil] Analog input configured on GPIO%d\n", PIN_SOIL_MOIST);
#endif

  pinMode(PIN_BATTERY, INPUT);
  analogSetPinAttenuation(PIN_BATTERY, ADC_11db);
  Serial.printf("[Battery] ADC configured on GPIO%d (Divider: 47k/10k = 5.70x)\n", PIN_BATTERY);

#if HAS_ANEMOMETER || HAS_WIND_VANE
  if (!rs485Initialized) {
    rs485Serial.begin(9600, SERIAL_8N1, PIN_RS485_RX, PIN_RS485_TX);
    rs485Serial.setTimeout(50);
    mbAnemo.begin(MODBUS_ANEMOMETER, rs485Serial);
    mbVane.begin(MODBUS_WIND_VANE, rs485Serial);
    rs485Initialized = true;
    Serial.printf("[RS485] UART1 active: RX=GPIO%d, TX=GPIO%d, Baud=9600\n", PIN_RS485_RX, PIN_RS485_TX);
  }
#endif

  Serial.println("[Sensors] Initialization complete");
}

// ── Read All Sensors ───────────────────────────────────────────────
SensorData sensorsRead(uint16_t nodeId) {
  SensorData data = {0};
  data.node_id = nodeId;

  sensorsPowerOn();

#if HAS_BME280
  if (hasBmeWorking) {
    data.temperature = bme.readTemperature();
    data.humidity    = bme.readHumidity();
    data.pressure    = bme.readPressure() / 100.0F; // Pa -> hPa
  } else if (hasBmpWorking) {
    data.temperature = bmp.readTemperature();
    data.humidity    = 0.0f;
    data.pressure    = bmp.readPressure() / 100.0F;
  }
#endif

#if HAS_DS18B20
  if (dsDeviceCount > 0) {
    ds18b20.requestTemperatures();
    float dsTemp = ds18b20.getTempCByIndex(0);
    if (dsTemp > -127.0f && dsTemp < 85.0f) {
      data.temperature = dsTemp; // High precision probe temperature
    }
  }
#endif

  // Battery voltage
  data.battery_v = readBatteryVoltage();

#if HAS_RAIN_GAUGE
  data.rain_tips = rainTips;
  rainTips = 0; // Reset counter after reading
#endif

#if HAS_ANEMOMETER
  float ws = readRS485WindSpeed();
  data.wind_speed = (ws >= 0.0f) ? ws : 0.0f;
#endif

#if HAS_WIND_VANE
  uint16_t wd = readRS485WindDirection();
  data.wind_dir = (wd != 0xFFFF) ? wd : 0;
#endif

#if HAS_SOIL_MOIST
  data.soil_moisture = readSoilMoisture();
#endif

  return data;
}

uint16_t getRainTips() {
#if HAS_RAIN_GAUGE
  return rainTips;
#else
  return 0;
#endif
}

float readBmeTemp() {
#if HAS_BME280
  if (hasBmeWorking) return bme.readTemperature();
  if (hasBmpWorking) return bmp.readTemperature();
#endif
  return 0.0f;
}

float readBmeHum() {
#if HAS_BME280
  if (hasBmeWorking) return bme.readHumidity();
#endif
  return 0.0f;
}

float readBmePress() {
#if HAS_BME280
  if (hasBmeWorking) return bme.readPressure() / 100.0F;
  if (hasBmpWorking) return bmp.readPressure() / 100.0F;
#endif
  return 0.0f;
}

float readDS18B20Temp() {
#if HAS_DS18B20
  if (dsDeviceCount > 0) {
    ds18b20.requestTemperatures();
    float t = ds18b20.getTempCByIndex(0);
    if (t > -127.0f && t < 85.0f) return t;
  }
#endif
  return -127.0f;
}

bool isBmeWorking() {
#if HAS_BME280
  return hasBmeWorking || hasBmpWorking;
#else
  return false;
#endif
}
