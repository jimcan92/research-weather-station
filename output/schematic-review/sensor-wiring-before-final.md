# Sensor Wiring Reference

**Board:** ESP32-S3 N16R8 (HW678 v0.0.0)  
**Project:** Weather Station Research  
**Date:** June 14, 2026  
**Revision:** v2.0 — Updated for 12V system, dual Mini560 power architecture  

> See `docs/power-configuration.md` for complete power supply design.  
> See `docs/pin-configuration-guide.md` for GPIO assignments.

---

## Power Rails Summary

```
12V Battery/Solar
    │
    ├── Mini560 #1 (12V→5V) ──► 5V BUS ──► MAX485 + E22-900T22D
    │
    ├── Mini560 #2 (12V→3.3V) ──► 3.3V BUS ──► ESP32-S3, BME280, LTR390, DS18B20, Soil
    │
    └── MOSFET Switch (GPIO15) ──► 12V_SW ──► RS485 Anemometer + Wind Vane
```

---

## Individual Sensor Wiring

### BME280 (Temperature, Humidity, Pressure)

```
BME280    → ESP32-S3
VIN       → 3.3V BUS
GND       → GND
SCL       → GPIO1 (I2C)
SDA       → GPIO2 (I2C)
```

- I2C address: 0x76 (SDO to GND) or 0x77 (SDO to VCC)
- Library: Adafruit BME280

### LTR390 (UV / Ambient Light)

```
LTR390    → ESP32-S3
VIN       → 3.3V BUS
GND       → GND
SCL       → GPIO1 (I2C, shared with BME280)
SDA       → GPIO2 (I2C, shared with BME280)
INT       → (optional, not used)
```

- I2C address: 0x53
- Library: Adafruit LTR390

### DS18B20 (Precision Temperature)

```
DS18B20   → ESP32-S3
VDD (red) → 3.3V BUS
DQ  (yellow) → GPIO3 (OneWire)
GND (black) → GND
4.7kΩ resistor between DQ and VDD
```

- Library: DallasTemperature + OneWire
- Multiple sensors can share one pin (each has unique 64-bit ROM ID)

### Rain Gauge (Tipping Bucket)

```
Rain Gauge → ESP32-S3
Wire 1     → GND
Wire 2     → GPIO10 (internal pull-up enabled)
```

- Reed switch: normally open, closes on tip
- Each tip = calibrated volume (typically 0.2-0.3mm)

### Soil Moisture (Capacitive / Resistive)

```
Sensor     → ESP32-S3
VCC        → 3.3V BUS (or GPIO13 for switched power)
GND        → GND
AOUT       → GPIO14 (ADC) — but GPIO14 used for battery ADC
```

> **Note:** Soil moisture ADC conflicts with battery monitoring on GPIO14. Use GPIO13 to switch sensor VCC and read via a different ADC pin, or remap battery ADC to another pin.

---

## RS485 Wind Sensors

### MAX485 Transceiver (on main board)

```
MAX485    → ESP32-S3
VCC       → 5V BUS
GND       → GND
RO (RX)   → GPIO18 (UART1 RX)
DI (TX)   → GPIO17 (UART1 TX)
RE + DE   → GPIO16 (tied together, HIGH=TX, LOW=RX)
A         → RS485 A line (to both sensors)
B         → RS485 B line (to both sensors)
```

### Anemometer + Wind Vane (field wiring)

```
12V_SW ──┬── Anemometer V+ (red/brown)
         └── Wind Vane V+ (red/brown)

GND ─────┬── Anemometer GND (black)
         └── Wind Vane GND (black)

RS485 A ─┬── Anemometer A (yellow or green)
         └── Wind Vane A (yellow or green)

RS485 B ─┬── Anemometer B (blue or white)
         └── Wind Vane B (blue or white)
```

- Both sensors share the same RS485 bus
- Each has a unique Modbus address — query individually
- Powered via 12V_SW (GPIO15 controls MOSFET) — only ON during reading

---

## Battery Voltage Divider (12V System)

```
Battery (+) 12.6V max
    │
  [330kΩ]     ← R1 (top resistor)
    │
    ├──── GPIO14 (ADC2)   ← V_adc = V_bat × 100/(330+100)
    │
  [100kΩ]     ← R2 (bottom resistor)
    │
   GND
```

| Parameter | Value |
|-----------|-------|
| R1 (top) | 330kΩ |
| R2 (bottom) | 100kΩ |
| Divider ratio | 0.2326 |
| Max ADC voltage | 2.93V (at 12.6V) |
| Firmware formula | `V_battery = V_adc × 4.30` |

---

## Power System (Dual Mini560)

```
Solar Panel (30-50W, 18Vmp)
    │
    ▼
CN3791 Charge Controller
    │
    ▼
3S Li-Ion Battery (11.1V nominal, 9.0–12.6V range)
    │
    ▼
12V COMMON RAIL (reverse-polarity Schottky + 100µF bulk cap)
    │
    ├── Mini560 #1 (12V→5V fixed) ──► 5V BUS ──► MAX485 + E22-900T22D
    │
    ├── Mini560 #2 (12V→3.3V fixed) ──► 3.3V BUS ──► ESP32 + Sensors
    │
    └── MOSFET Switch (GPIO15 → IRF9540) ──► 12V_SW ──► Wind Sensors
```

| Rail | Source | Voltage | Load |
|------|--------|---------|------|
| 12V_SW | 12V via MOSFET | 12V | RS485 anemometer + wind vane |
| 5V BUS | Mini560 #1 | 5.0V fixed | MAX485 + E22-900T22D |
| 3.3V BUS | Mini560 #2 | 3.3V fixed | ESP32-S3, BME280, LTR390, DS18B20, Soil |

---

## Current Budget (per 2-minute read cycle)

| Phase | Duration | Current @ 12V | Energy |
|-------|----------|---------------|--------|
| Wake + Init | 0.5s | 80 mA | 40 mAs |
| Sensor read (3.3V bus) | 0.3s | 40 mA | 12 mAs |
| Wind sensors (12V_SW) | 1.0s | 50 mA | 50 mAs |
| E22 LoRa TX (up to 22dBm) | 1.0s | Measure actual | TBD |
| **Total active (5-min cycle)** | **2.8s** | — | **222 mAs** |
| Deep sleep (296.2s) | 297.2s | 0.6 mA | 178 mAs |
| **Total per 5-min cycle** | **300s** | — | **~400 mAs** |

**Daily energy:** 288 cycles × 400 mAs = 115,200 mAs = **32 mAh @ 12V = 0.38 Wh**

**Battery life (3S 3500mAh, no solar):** ~109 days  
**With 30W solar (135 Wh/day in PH sun):** Indefinite / always full
