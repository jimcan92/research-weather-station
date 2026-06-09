# Sensor Wiring Reference

## ESP32-WROOM-32 Pin Assignments

```
                   ┌──────────────┐
                   │   ESP32-DEV  │
                   │              │
    LoRa NSS  ←─── │ GPIO5        │
    LoRa SCK  ←─── │ GPIO18       │
    LoRa MOSI ←─── │ GPIO23       │
    LoRa MISO ───→ │ GPIO19       │
    LoRa RST  ←─── │ GPIO14       │
    LoRa DIO0 ───→ │ GPIO26       │
                   │              │
    I2C SDA   ←──→ │ GPIO21  ────→ BME280 SDA
    I2C SCL   ←─── │ GPIO22  ────→ BME280 SCL
                   │              │
    OneWire   ←──→ │ GPIO4   ────→ DS18B20 DQ (4.7kΩ pull-up to 3.3V)
                   │              │
    Rain      ───→ │ GPIO34  ────→ Rain Gauge (NO, internal pull-up)
    Wind Spd  ───→ │ GPIO35  ────→ Anemometer (NO, internal pull-up)
    Wind Dir  ───→ │ GPIO36  ────→ Wind Vane signal (ADC)
    Soil      ───→ │ GPIO39  ────→ Soil moisture AOUT (ADC)
    Battery   ───→ │ GPIO33  ────→ Voltage divider center tap
                   │              │
    PWR Gate  ←─── │ GPIO32  ────→ MOSFET gate (sensor power switch)
                   │              │
                    ── 3.3V ──────→ Sensor VCC bus (via MOSFET)
                    ── GND ───────→ Common ground
                   └──────────────┘
```

## Individual Sensor Wiring

### BME280 (Temperature, Humidity, Pressure)

```
BME280    → ESP32
VIN       → 3.3V (on MOSFET-switched bus)
GND       → GND
SCL       → GPIO22 (I2C)
SDA       → GPIO21 (I2C)
```

- I2C address: 0x76 (SDO to GND) or 0x77 (SDO to VCC)
- Library: Adafruit BME280

### DS18B20 (Precision Temperature)

```
DS18B20   → ESP32
VDD (red) → 3.3V (switched bus)
DQ  (yellow) → GPIO4
GND (black) → GND
4.7kΩ resistor between DQ and VDD
```

- Library: DallasTemperature + OneWire
- Multiple sensors can share one pin (each has unique 64-bit ROM ID)

### Rain Gauge (Tipping Bucket)

```
Rain Gauge → ESP32
Wire 1     → GND
Wire 2     → GPIO34 (internal pull-up enabled)
```

- Reed switch: normally open, closes on tip
- Each tip = calibrated volume (typically 0.2-0.3 mm)
- Calibrate by pouring measured water and counting tips

### Anemometer (Wind Speed)

```
Anemometer → ESP32
Wire 1     → GND
Wire 2     → GPIO35 (internal pull-up enabled)
```

- Reed switch: one pulse per rotation
- Convert: wind_speed (m/s) = pulse_frequency × calibration_factor
- Typical factor: 2.4 m/s per Hz (calibrate per sensor)

### Wind Vane (Direction)

```
Wind Vane  → ESP32
VCC        → 3.3V (switched bus)
Signal     → GPIO36 (ADC1)
GND        → GND
```

- Internal resistor network gives different voltage per direction
- Read ADC, map to compass direction (0-360°)
- Calibrate by measuring voltage at each cardinal point

### Soil Moisture (Capacitive v1.2)

```
Sensor     → ESP32
VCC        → GPIO32 (MOSFET-switched — power ONLY during reading!)
GND        → GND
AOUT       → GPIO39 (ADC1, 12-bit)
```

- Capacitive sensors (v1.2) — do NOT use resistive probes
- Power only during reading to prevent electrolysis corrosion
- Typical range: ~1.2V (dry) to ~2.8V (wet)

### Battery Voltage Divider

```
Battery (+) ──[100kΩ]──┬──[220kΩ]── GND
                        │
                    GPIO33 (ADC)
```

- V_adc = V_battery × (R2 / (R1+R2)) = V_battery × (220/320) ≈ 0.6875 × V_battery
- At 4.2V: ADC reads ~2.89V → safe for ESP32 (3.3V max)
- Formula: V_battery = ADC_voltage × (R1+R2)/R2 = ADC_voltage × 320/220

## Power System

```
Solar Panel (5-10W, 18V)
  │
  ▼
CN3791 Charge Controller
  │
  ▼
Li-Ion Battery (3.7V, 3000mAh)
  │
  ▼
HT7333-A LDO (3.3V, 250mA, <5µA quiescent)
  │
  ├── ESP32 (always powered, deep sleep ~10µA)
  ├── LoRa Module (sleep ~1µA)
  └── MOSFET Gate (GPIO32) → Sensor bus (ON only during reading)
```

**Current Budget (per read cycle):**

| Phase | Duration | Current | Energy |
|-------|----------|---------|--------|
| Wake + Init | 0.5s | 80 mA | 40 mAs |
| Sensor read | 0.3s | 40 mA | 12 mAs |
| LoRa TX | 1.0s | 120 mA | 120 mAs |
| **Total active** | **1.8s** | | **172 mAs** |
| Deep sleep | 118.2s | 16 µA | 1.9 mAs |
| **Total per 2min cycle** | **120s** | | **~174 mAs** |

With 3000 mAh battery: ~7 days without charging, indefinite with solar.
