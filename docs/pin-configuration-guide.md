# ESP32-S3 Weather Node — Pin Configuration Guide

**Board:** ESP32-S3 N16R8 (HW678 v0.0.0)
**Project:** Weather Station Research
**Date:** June 10, 2026
**Related:** `docs/power-configuration.md` (12V power supply, BOM, perf board layout)

---

## Pin Map Overview

```
                    ESP32-S3 HW678 (N16R8)
                  ┌─────────────────────────┐
                  │  USB-C (USB)  USB-C (COM)│  ← Use USB port for programming
                  │                         │
    I2C SDA ───── │ GPIO1              GPIO48│ ───── RGB LED (WS2812)
    I2C SCL ───── │ GPIO2              GPIO47│
  OneWire ─────── │ GPIO3              GPIO38│ (PSRAM reserved)
      E22 M0 ───── │ GPIO4              GPIO37│ (PSRAM reserved)
      E22 M1 ───── │ GPIO5              GPIO36│ (PSRAM reserved)
     E22 RXD ───── │ GPIO6              GPIO35│ (PSRAM reserved)
     E22 TXD ───── │ GPIO7              GPIO34│ (PSRAM reserved)
     E22 AUX ───── │ GPIO8              GPIO33│ (PSRAM reserved)
                   │ GPIO9              GPIO32│ (PSRAM reserved)
Rain Gauge ────── │ GPIO10             GPIO31│ (PSRAM reserved)
                  │ GPIO11             GPIO30│ (PSRAM reserved)
                  │ GPIO12             GPIO29│ (PSRAM reserved)
Soil Moisture ─── │ GPIO13             GPIO28│ (PSRAM reserved)
 Battery ADC ──── │ GPIO14             GPIO27│ (PSRAM reserved)
  Sensor PWR ──── │ GPIO15             GPIO26│ (PSRAM reserved)
 Unused     ──── │ GPIO16             GPIO21│
  RS485 TX ────── │ GPIO17             GPIO20│ (USB D+)
  RS485 RX ────── │ GPIO18             GPIO19│ (USB D-)
                  │    GND  3.3V  5V         │
                  └─────────────────────────┘
```

> **Note:** GPIO26–37 are reserved by the octal PSRAM (8MB). Do NOT use these pins.
> GPIO19–20 are the native USB D-/D+ pins. Do NOT use.

---

## Sensor Wiring

### 1. LoRa Radio (E22-900T22D UART)

| E22 Pin | ESP32-S3 Pin | Notes |
|---------|---------------|-------|
| M0 | GPIO4 | Operating-mode select 0 |
| M1 | GPIO5 | Operating-mode select 1 |
| RXD | GPIO6 | ESP32 TX → E22 RXD |
| TXD | GPIO7 | E22 TXD → ESP32 RX |
| AUX | GPIO8 | HIGH means module ready |
| VCC | +5V | Add 470µF + 100nF close to module |
| GND | GND | Common ground |
| ANT | SMA connector | 900/915 MHz antenna |

Firmware uses transparent UART mode at 9600 baud (M0=LOW, M1=LOW). Air channel,
air data rate and TX power are stored in the E22 module and must match the gateway.

---

### 2. BME280 (Temperature, Humidity, Pressure)

| BME280 Pin | ESP32-S3 Pin | Notes |
|-----------|-------------|-------|
| VCC | 3.3V | |
| GND | GND | |
| SDA | GPIO1 | I2C data |
| SCL | GPIO2 | I2C clock |
| CSB | 3.3V | Pull high for I2C mode |
| SDO | GND | GND = addr 0x76, VCC = addr 0x77 |

```
BME280                   ESP32-S3
┌────────┐              ┌──────────┐
│ VCC ───────────────── 3.3V      │
│ GND ───────────────── GND       │
│ SDA ───────────────── GPIO1     │
│ SCL ───────────────── GPIO2     │
│ CSB ──── 3.3V (I2C)            │
│ SDO ──── GND (addr 0x76)       │
└────────┘              └──────────┘
```

**I2C Address:** 0x76

---

### 3. LTR390 UV Sensor

| LTR390 Pin | ESP32-S3 Pin | Notes |
|-----------|-------------|-------|
| VCC | 3.3V | |
| GND | GND | |
| SDA | GPIO1 | Shared I2C bus with BME280 |
| SCL | GPIO2 | Shared I2C bus with BME280 |
| INT | — | Optional, not connected |

```
LTR390                   ESP32-S3
┌────────┐              ┌──────────┐
│ VCC ───────────────── 3.3V      │
│ GND ───────────────── GND       │
│ SDA ───────────────── GPIO1     │  ← Shared with BME280
│ SCL ───────────────── GPIO2     │  ← Shared with BME280
│ INT ──── (not connected)        │
└────────┘              └──────────┘
```

**I2C Address:** 0x53

---

### 4. Rain Gauge (Tipping Bucket)

| Rain Gauge Wire | ESP32-S3 Pin | Notes |
|----------------|-------------|-------|
| Wire 1 | GND | |
| Wire 2 | GPIO10 | Interrupt input (internal pull-up) |

```
Rain Gauge               ESP32-S3
┌──────────┐            ┌──────────┐
│ Wire 1 ─────────────── GND       │
│ Wire 2 ─────────────── GPIO10    │  ← Internal pull-up enabled
└──────────┘            └──────────┘
```

**Calibration:** 0.2794 mm per tip

---

### 5. RS485 Wind Sensors (Anemometer + Wind Vane)

Both sensors share the same RS485 bus (Modbus RTU).

### DIYMORE isolated automatic-direction RS485 module

The selected module has TTL pins **VCC, TXD, RXD, GND** (top to bottom in the supplied image), and **A+, B−, earth** screw terminals. U4 uses logical terminal numbers, not a verified PCB footprint.

| Module terminal | Connection |
|---|---|
| VCC | 3.3V BUS from AMS1117-3.3 |
| TXD | GPIO18 / UART1 RX — provisional: assumes module output |
| RXD | GPIO17 / UART1 TX — provisional: assumes module input |
| GND | ESP32/common GND (TTL side) |
| A+ | Both wind sensors' A bus |
| B− | Both wind sensors' B bus |
| Earth | Reserved/unconnected in this design; separate from TTL GND |

**Verify UART directions before wiring:** the product image labels TXD/RXD but does not specify input/output. The schematic provisionally uses crossed UART wiring. If the board labels refer to the host UART instead, connect GPIO17 TX to module TXD input and GPIO18 RX to module RXD output. Confirm with the seller's pin-direction diagram or datasheet; do not infer direction solely from the names.

- Supply the TTL side at **3.3V**, consistent with the pictured 3.3V/5V marking. Confirm its output signal is 3.3V-compatible before connecting ESP32 RX.
- Automatic direction control: **no DE/RE wire; GPIO16 is unused**. R8/R9 from the old 5V receive divider are removed. C7 remains 100nF across TTL VCC/GND.
- R10 is **120Ω, DNP by default**. Fit only when this is a bus endpoint and the module does not already provide enabled termination; avoid duplicate parallel termination.
- Do not bridge the pictured earth/protection terminal to TTL GND. Its grounding arrangement needs the module documentation. Sensor supply return remains the existing common GND; this design does not claim complete system galvanic isolation.
- Wind sensors retain **12V_SW** power via GPIO15/MOSFET. Never feed their 12V into module VCC.

**Modbus Parameters:**
- Baud: 9600 (default, check sensor datasheet)
- Data bits: 8
- Stop bits: 1
- Parity: None

**Modbus Slave IDs:**
- Anemometer (wind speed): ID 1
- Wind Vane (direction): ID 2

---

### 6. Soil Moisture Sensor (Capacitive v1.2)

| Soil Sensor Pin | ESP32-S3 Pin | Notes |
|----------------|-------------|-------|
| VCC | Sensor PWR (GPIO15) | Switched via MOSFET — only powered during reading |
| GND | GND | |
| AOUT | GPIO13 | Analog input (ADC2) |

```
Soil Moisture Sensor      ESP32-S3
┌────────────────┐       ┌──────────┐
│ VCC ────────────────── GPIO15    │  ← MOSFET-switched power
│ GND ────────────────── GND       │
│ AOUT ───────────────── GPIO13    │  ← Analog (0-3.3V)
└────────────────┘       └──────────┘
```

> **Important:** Power the sensor via a MOSFET controlled by GPIO15,
> NOT directly from 3.3V. This prevents electrolysis corrosion and
> saves battery power during deep sleep.

**MOSFET circuit:**
```
   GPIO15 ──[10k]──┬── G (IRLZ44N or similar)
                    │
   3.3V ─────────── D
                    │
                    S ──── Sensor VCC
                    │
                   GND
```

---

### 7. Battery Voltage Monitor (12V System)

| Voltage Divider | ESP32-S3 Pin | Notes |
|----------------|-------------|-------|
| Battery (+) → 330k → ADC | GPIO14 | Top resistor (updated for 12V) |
| ADC → 100k → GND | | Bottom resistor |
| ADC read point | GPIO14 | V_adc = V_batt × (100/(100+330)) |

```
Battery (+) 12.6V max
    │
  [330kΩ]     ← R1 (top — was 100k for 3.7V system)
    │
    ├──── GPIO14 (ADC2)   ← Max = 12.6 × 100/430 = 2.93V (safe)
    │
  [100kΩ]     ← R2 (bottom — was 220k for 3.7V system)
    │
   GND
```

**Formula:** `V_battery = V_adc × (330 + 100) / 100 = V_adc × 4.30`

> ⚠️ Updated for 12V system. Old values (100k/220k) were for 3.7V Li-Ion and will give wrong readings on a 12V battery. See `docs/power-configuration.md` for details.

---

### 8. RGB Status LED (WS2812)

| WS2812 Pin | ESP32-S3 Pin | Notes |
|-----------|-------------|-------|
| VCC | 5V or 3.3V | Onboard — no external wiring needed |
| GND | GND | Onboard |
| DIN | GPIO48 | Data in |

```
The RGB LED is onboard the HW678 board — no external wiring needed.
Connected to GPIO48. Uses Adafruit NeoPixel library (NEO_GRB + NEO_KHZ800).

Status Colors:
  Blue pulse    → Booting
  Dim blue      → TEST_MODE idle
  Yellow        → Reading sensors
  Green flash   → TX success
  Red blink     → Error
  Off           → Deep sleep
```

---

## Power Pin Summary

Power is supplied by a 12V rail. See `docs/power-configuration.md` for the complete power supply design.

| Pin | Function | Voltage |
|-----|----------|---------|
| GPIO15 | 12V sensor bus MOSFET gate — HIGH = wind sensors powered | 3.3V signal → switches 12V |
| 3.3V BUS | ESP32, LoRa, BME280, LTR390, DS18B20, Soil | 3.3V (from HT7333-A LDO) |
| 3.3V BUS | DIYMORE auto RS485 | 3.3V (AMS1117) |
| 12V_SW | Anemometer + Wind Vane | 12V (MOSFET-switched via GPIO15) |

> GPIO15 drives a two-transistor level shifter (2N7000 + IRF9540) that switches the 12V rail to the wind sensors. All low-voltage sensors are always-on and manage their own sleep states.

---

## I2C Bus Map

```
        3.3V
         │
    ┌────┴────┐
    │  BME280  │  Address: 0x76
    │  SDA SCL │
    └────┬────┘
         │
    ┌────┼────┐
    │  LTR390  │  Address: 0x53
    │  SDA SCL │
    └────┬────┘
         │
    GPIO1 ──── SDA
    GPIO2 ──── SCL
```

Both sensors share GPIO1 (SDA) and GPIO2 (SCL) with no address conflict.

---

## Quick Reference

| GPIO | Function | Type | Notes |
|------|----------|------|-------|
| 1 | I2C SDA | I2C | BME280 + LTR390 |
| 2 | I2C SCL | I2C | BME280 + LTR390 |
| 3 | OneWire | Digital | DS18B20 (4.7k pull-up to 3.3V) |
| 4 | LoRa NSS | SPI CS | SX1276 |
| 5 | LoRa SCK | SPI CLK | SX1276 |
| 6 | LoRa MOSI | SPI | SX1276 |
| 7 | LoRa MISO | SPI | SX1276 |
| 8 | LoRa RST | Digital OUT | SX1276 reset |
| 9 | LoRa DIO0 | Digital IN | SX1276 interrupt |
| 10 | Rain Gauge | Interrupt | Internal pull-up |
| 13 | Soil Moisture | ADC2 | Capacitive analog |
| 14 | Battery | ADC2 | Voltage divider 100k/220k |
| 15 | Sensor PWR | Digital OUT | MOSFET gate |
| 16 | Unused | — | Automatic RS485 direction |
| 17 | RS485 TX | UART1 TX | Wind sensors |
| 18 | RS485 RX | UART1 RX | Wind sensors |
| 48 | RGB LED | WS2812 | Onboard status LED |

---

## Firmware Commands

```bash
# Enter project directory
cd ~/dev/projects/weather-station/firmware/weather-node

# Build
sg dialout -c "pio run -e s3"

# Flash + monitor
sg dialout -c "pio run -e s3 -t upload"

# Read serial output
python3 -c "
import serial
s = serial.Serial('/dev/ttyACM0', 115200, timeout=10)
while True: print(s.readline().decode(errors='replace').rstrip())
"
```

## Switch to Production Mode

Edit `src/config.h`:

```c
#define TEST_MODE       false   // was true
#define SLEEP_INTERVAL_S  120   // was 5

#define HAS_BME280      true
#define HAS_LTR390      true
#define HAS_RAIN_GAUGE  true
#define HAS_ANEMOMETER  true
#define HAS_WIND_VANE   true
#define HAS_SOIL_MOIST  true
```
