# Weather Node — Power Supply Configuration

> **Archived alternative:** This document records earlier LM2596 and dual-Mini560 studies. The canonical final design is `hardware/node-pcb/weather-node-complete.kicad_sch`: Mini560 12V→5V followed by AMS1117-3.3.

**Board:** ESP32-S3 N16R8 (HW678 v0.0.0)  
**Project:** Weather Station Research  
**Date:** June 29, 2026  
**Revision:** v3.0 — LM2596 + AMS1117 architecture (same as vending machine)  
**Related:** `docs/pin-configuration-guide.md`, `hardware/power-pcb/weather-power-v3.kicad_sch`

---

## Architecture: LM2596-5.0 + AMS1117-3.3 (Same as vending machine)

Single LM2596-5.0 buck converter (12-24V→5V) + AMS1117-3.3 LDO (5V→3.3V) cascaded.
Proven design from vending machine v3.0/v4.0 — parts available on Shopee/Lazada.

```
                         ┌──────────────────────┐
                         │    12-24V DC INPUT      │
                         │  (barrel jack or        │
                         │   screw terminal)       │
                         └──────────┬───────────┘
                                    │
               Phase 1             │           Phase 2
          ┌────────────────────────┼──────────────────────┐
          │                        │                      │
          ▼                        ▼                      ▼
   ┌────────────┐          ┌──────────────┐       ┌──────────────┐
   │ 12V 2A     │          │ Solar 30-50W │       │ Solar + Batt │
   │ Adapter    │          │  + CN3791    │       │  (hybrid)    │
   │ (bench)    │          │  + 3S Li-Ion │       │              │
   └────────────┘          └──────────────┘       └──────────────┘
          │                        │                      │
          └────────────────────────┼──────────────────────┘
                                   │
                        ┌──────────┴──────────┐
                        │    INPUT PROTECTION   │
                        │  PTC 5A + SS34 +      │
                        │  100µF/35V + 100nF    │
                        └──────────┬──────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
   ┌───────────────┐     ┌───────────────┐      ┌──────────────────┐
   │ LM2596-5.0    │     │ AMS1117-3.3   │      │ MOSFET Switch    │
   │ 12V → 5V      │     │ 5V → 3.3V     │      │ (GPIO15 → Gate)  │
   │ + SS34 + 68µH │     │ + 100nF+10µF │      │ 12V → 12V_SW     │
   │ + 220µF+10µF│     │               │      │                  │
   └───────┬───────┘     └───────┬───────┘      └────────┬─────────┘
           │                     │                        │
           ▼                     ▼                        ▼
   ┌───────────────┐     ┌───────────────┐      ┌──────────────────┐
   │ 5V BUS         │     │ 3.3V BUS       │      │ 12V_SWITCHED     │
   │                │     │                │      │                  │
   │ MAX485         │     │ ESP32-S3       │      │ RS485 Anemometer │
   │                │     │ LoRa SX1262    │      │ RS485 Wind Vane  │
   └────────────────┘     │ BME280         │      └──────────────────┘
                          │ LTR390         │
                          │ DS18B20        │
                          │ Rain (passive) │
                          │ Soil Moisture  │
                          │ RGB LED(WS2812)│
                          └───────────────┘

           ┌───────────────┐
           │ BATTERY MON.   │
           │ 330k + 100k    │
           │ divider (4.30) │
           │ → BAT_ADC      │
           └───────────────┘
```

> **Why LM2596 + AMS1117 instead of dual Mini560?** Same parts as vending machine — Jim already knows the design, parts are on Shopee/Lazada, no tuning needed (fixed-voltage versions). LM2596 is TO-220 through-hole, easy to solder. Quiescent current (~10mA) is negligible with a 30W solar panel.

---

## Architecture: Two Parallel Mini560 Bucks from 12V Rail

Two independent Mini560 buck converters run in parallel from the 12V rail. No cascading — each buck converts 12V directly to its target voltage.

```
                         ┌──────────────────────┐
                         │    12V DC INPUT        │
                         │  (barrel jack or        │
                         │   screw terminal)       │
                         └──────────┬───────────┘
                                    │
               Phase 1             │           Phase 2
          ┌────────────────────────┼──────────────────────┐
          │                        │                      │
          ▼                        ▼                      ▼
   ┌────────────┐          ┌──────────────┐       ┌──────────────┐
   │ 12V 2A     │          │ Solar 30-50W │       │ Solar + Batt │
   │ Adapter    │          │  + CN3791    │       │  (hybrid)    │
   │ (bench)    │          │  + 3S Li-Ion │       │              │
   └────────────┘          └──────────────┘       └──────────────┘
          │                        │                      │
          └────────────────────────┼──────────────────────┘
                                   │
                        ┌──────────┴──────────┐
                        │    12V COMMON RAIL   │
                        │  (reverse-polarity   │
                        │   Schottky + 100µF)  │
                        └──────────┬──────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
   ┌───────────────┐     ┌───────────────┐      ┌──────────────────┐
   │ Buck #1       │     │ Buck #2       │      │ MOSFET Switch    │
   │ 12V → 5V      │     │ 12V → 3.3V    │      │ (GPIO15 → Gate)  │
   │ Mini560 (5V)  │     │ Mini560 (3.3V)│      │ 12V → 12V_SW     │
   └───────┬───────┘     └───────┬───────┘      └────────┬─────────┘
           │                     │                        │
           ▼                     ▼                        ▼
   ┌───────────────┐     ┌───────────────┐      ┌──────────────────┐
   │ 5V BUS         │     │ 3.3V BUS       │      │ 12V_SWITCHED     │
   │                │     │                │      │ (sensor bus)     │
   │ MAX485         │     │ ESP32-S3       │      │                  │
   │                │     │ LoRa SX1262    │      │ RS485 Anemometer │
   └────────────────┘     │ BME280         │      │ RS485 Wind Vane  │
                          │ LTR390         │      └──────────────────┘
                          │ DS18B20        │
                          │ Rain (passive) │
                          │ Soil Moisture  │
                          │ RGB LED(WS2812)│
                          └───────────────┘
```

> **Why parallel bucks instead of buck→LDO?** Two Mini560 modules are simpler to source (no separate LDO IC + caps to solder), each is jumper-set to a fixed voltage, and the quiescent current of ~200µA total (2 × 100µA) is trivial on a solar-charged 12V battery. The 12V→3.3V direct conversion also runs cooler at ESP32 loads (~30mA) than cascading through 5V first.

---

## Buck Converter #1: 12V → 5V (Mini560, fixed 5V output)

### Module Settings

| Parameter | Value |
|-----------|-------|
| Module | Mini560 DC-DC Buck (MP1584-based) |
| Input | 7–28V DC |
| Output | **5.0V fixed** (solder jumper selected) |
| Max current | 3A continuous |
| Efficiency | ~88–92% at 50–200mA |
| Quiescent (Iq) | ~100µA |
| Size | ~17×11mm |

### Jumper Configuration

The Mini560 has solder pads on the back. Bridge the **5V** pads to set the output. No potentiometer — no tuning needed.

```
Mini560 back side:
┌──────────────┐
│ ○  ○  ○  ○  │  3.3V  5V  9V  12V  pads
│              │
│  ══          │  Bridge the 5V pads with solder blob
│              │
└──────────────┘
```

### Capacitors (Add for Stability)

```
12V IN ──┬── 100µF/25V electrolytic ── GND
         │
         └── Mini560 Vin+
               Mini560 Vin- ── GND
               Mini560 Vout+ ──┬── 100µF/16V electrolytic ── GND
                              │
                              └── 3.3V BUS → DIYMORE RS485 VCC
```

---

## Buck Converter #2: 12V → 3.3V (Mini560, fixed 3.3V output)

### Module Settings

| Parameter | Value |
|-----------|-------|
| Module | Mini560 DC-DC Buck (MP1584-based) |
| Input | 7–28V DC |
| Output | **3.3V fixed** (solder jumper selected) |
| Max current | 3A continuous |
| Efficiency | ~85–90% at 30–100mA |
| Quiescent (Iq) | ~100µA |
| Size | ~17×11mm |

### Jumper Configuration

Bridge the **3.3V** pads:

```
Mini560 back side:
┌──────────────┐
│ ○  ○  ○  ○  │  3.3V  5V  9V  12V  pads
│              │
│ ══           │  Bridge the 3.3V pads with solder blob
│              │
└──────────────┘
```

### Capacitors

```
12V IN ──┬── 100µF/25V electrolytic ── GND
         │
         └── Mini560 Vin+
               Mini560 Vin- ── GND
               Mini560 Vout+ ──┬── 100µF/16V electrolytic ── GND
                              │
                              └── 3.3V BUS → ESP32 + LoRa + BME280 + LTR390 + DS18B20 + Soil
```

> ⚠️ Double-check the 3.3V jumper before power-up. A misconfigured module set to 12V will kill the ESP32 instantly. Measure Vout with multimeter before connecting anything.

---

## MOSFET Switch: GPIO15 → 12V Sensor Bus

*(Unchanged from v1.0)*

The ESP32 GPIO15 outputs 3.3V, but we need to switch a 12V rail. A two-transistor level shifter does this:

```
12V ────────┬─────────────── IRF9540 Source (P-channel MOSFET)
            │
            └──[10kΩ]──┬── IRF9540 Gate
                       │
                       ├── 2N7000 Drain (N-channel MOSFET)
                       │
                       │   2N7000 Source ── GND
                       │
GPIO15 ────[1kΩ]───────┼── 2N7000 Gate
                       │
                      GND

IRF9540 Drain ──► 12V_SWITCHED (wind sensors)
```

### How It Works

| GPIO15 | 2N7000 | IRF9540 Gate | IRF9540 | 12V_SW |
|--------|--------|-------------|---------|--------|
| LOW (0V) | OFF | Pulled to 12V via 10kΩ | OFF | 0V |
| HIGH (3.3V) | ON | ~0V (pulled to GND) | ON | 12V |

### Parts

| Part | Package | Price |
|------|---------|-------|
| IRF9540 | TO-220 | ₱30 |
| 2N7000 | TO-92 | ₱10 |
| 10kΩ resistor | 1/4W | ₱1 |
| 1kΩ resistor | 1/4W | ₱1 |

---

## Perf Board Layout (7×9 cm)

```
┌──────────────────────────────────────────────────────────┐
│                  POWER PERF BOARD                         │
│                   (7×9 cm, top view)                      │
│                                                           │
│  ┌─────────────┐                                          │
│  │ 12V INPUT    │    ┌────────────────┐  ┌────────────┐  │
│  │ Barrel Jack  │    │ Mini560 #1     │  │ Mini560 #2 │  │
│  │              │    │ 12V → 5V       │  │ 12V→3.3V   │  │
│  │ (+) ────────┬────│─ Vin+          │  │            │  │
│  │ (-) ────┐   │    │  Vin- ───┐     │  │            │  │
│  └─────────│───│────│─ Vout+    │     │  │            │  │
│            │   │    │  Vout- ───│──┐  │  │            │  │
│            │   │    └───────────│──│──│──│─ Vin+      │  │
│            │   │               │  │  │  │  Vin- ───┐ │  │
│  12V BUS   ▼   ▼               │  │  │  │  Vout+   │ │  │
│  ───────────────────           │  │  │  │  Vout- ──│─│──│── 3.3V OUT
│  │  +  │  │  -  │              │  │  │  └──────────│─│──│── GND
│  │     │  │     │              │  │  │             │ │  │
│  │ 12V │  │ GND │              │  │  │             │ │  │
│  │ BUS │  │ BUS │              │  │  │             │ │  │
│  └──┬──┘  └──┬──┘              │  │  │             │ │  │
│     │        │                 │  │  │             │ │  │
│     │        └────── GND ──────┴──┴──┴─────────────┘ │  │
│     │                                                  │  │
│     ├──► Wind Sensors (12V) via MOSFET SW              │  │
│     ├──► Mini560 #1 Vin+                                │  │
│     └──► Mini560 #2 Vin+                                │  │
│                                                         │  │
│  ┌───────────────────────────────────────────────┐     │  │
│  │            OUTPUT TERMINALS                     │     │  │
│  │                                                │     │  │
│  │  [12V_SW] [GND]  [5V] [GND]  [3.3V] [GND]    │     │  │
│  │                           [GPIO15] [BAT_ADC]  │     │  │
│  └───────────────────────────────────────────────┘     │  │
│                                                         │  │
│  ┌────────────────────────┐                             │  │
│  │ MOSFET SW              │                             │  │
│  │ IRF9540 + 2N7000       │                             │  │
│  │ 10kΩ + 1kΩ             │                             │  │
│  └────────────────────────┘                             │  │
└──────────────────────────────────────────────────────────┘
```

### Perf Board Wiring Checklist

- [ ] Barrel jack soldered at edge (12V IN)
- [ ] Schottky diode (1N5819) in series with 12V+ for reverse-polarity protection
- [ ] 100µF/25V electrolytic across 12V input (polarity: stripe = negative)
- [ ] Thick power bus traces for 12V and GND (use solder bridges or solid wire)
- [ ] Mini560 #1 (5V) mounted — **verify jumper is on 5V pads**
- [ ] 100µF/16V electrolytic across Mini560 #1 output
- [ ] Mini560 #2 (3.3V) mounted — **verify jumper is on 3.3V pads**
- [ ] 100µF/16V electrolytic across Mini560 #2 output
- [ ] MOSFET level-shifter circuit in one corner
- [ ] Screw terminal block for each output: 12V_SW, 5V, 3.3V
- [ ] GPIO15 header pin for MOSFET gate signal
- [ ] BAT_ADC header pin for battery voltage divider tap
- [ ] All GNDs tied to common ground bus
- [ ] Heat shrink tubing on exposed 12V connections

### Wire Gauge Guide

| Connection | Recommended Wire |
|------------|-----------------|
| 12V input / bus | 22–20 AWG solid core |
| 3.3V / 5V signal | 24–26 AWG |
| Sensor power runs | 24 AWG |
| High-current paths (>500mA) | 20 AWG |

---

## Voltage Divider: 12V Battery Monitoring

The divider is sized for a 12V battery (3S Li-Ion: 9.0V–12.6V, or 12V SLA: 10.5V–13.8V).

```
Battery (+) 12.6V max
    │
  [330kΩ]     ← R1 (top resistor)
    │
    ├──── GPIO14 (ADC2)   ← Max = 12.6 × 100/(100+330) = 2.93V (safe)
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
| Max ADC voltage | 2.93V (at 12.6V battery) |
| Min ADC voltage | 2.09V (at 9.0V battery) |

**Formula:** `V_battery = V_adc × (330 + 100) / 100 = V_adc × 4.30`

### Firmware Config

In `config.h`:

```c
#define BAT_R1  330.0   // kΩ (top resistor)
#define BAT_R2  100.0   // kΩ (bottom resistor)
```

---

> **2026-09-29 update:** The older MAX485 drawings/current estimates above are historical. The current U4 module uses 3.3V; see the wiring below. Module current and rail budget require its datasheet.

## RS485 Wind Sensor Power

### Wind Sensor Supply (12V Direct)

The RS485 anemometer and wind vane need 12-24V DC. They connect to the **12V_SWITCHED** output (controlled by GPIO15 via MOSFET).

```
12V_SW ──┬── Anemometer V+ (red/brown)
         │
         └── Wind Vane V+ (red/brown)

GND ─────┬── Anemometer GND (black)
         │
         └── Wind Vane GND (black)
```

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
---

## Sensor Power Table

| Sensor | Supply Voltage | Rail | Switched? | Notes |
|--------|---------------|------|-----------|-------|
| ESP32-S3 | 3.3V | 3.3V BUS | No | Always powered or deep sleep |
| E22-900T22D | 5V | 5V BUS | No | Mode 3 sleep via M0=HIGH, M1=HIGH |
| BME280 | 3.3V | 3.3V BUS | No | ~0.5mA active, 0.1µA sleep |
| LTR390 | 3.3V | 3.3V BUS | No | ~0.3mA active |
| DS18B20 | 3.3V | 3.3V BUS | No | ~1mA active |
| Rain Gauge | — | — | No | Passive reed switch |
| Soil Moisture | 3.3V | 3.3V BUS | No | Read via ADC |
| RGB LED (WS2812) | 3.3V | 3.3V BUS | No | Built into dev board |
| DIYMORE auto RS485 | 3.3V | 3.3V BUS | No | Confirm module current from datasheet |
| RS485 Anemometer | 12V | 12V_SW | **Yes (GPIO15)** | ~20-50mA active |
| RS485 Wind Vane | 12V | 12V_SW | **Yes (GPIO15)** | ~20-50mA active |

> Low-voltage sensors (3.3V bus) stay always-on and manage their own sleep states. The MOSFET switch controls only the 12V wind sensor rail.

---

## Current Budget (12V System)

### Sleep State

| Component | Current @ 12V | Notes |
|-----------|--------------|-------|
| Mini560 #1 (5V) quiescent | ~100µA | Always-on |
| Mini560 #2 (3.3V) quiescent | ~100µA | Always-on |
| ESP32 deep sleep | ~10µA @ 3.3V ≈ 3µA @ 12V | After buck |
| E22 mode 3 | Verify with ammeter | Module/batch dependent; M0=M1=HIGH |
| BME280 sleep | ~0.1µA @ 3.3V | |
| MAX485 idle | ~1mA @ 5V ≈ 0.4mA @ 12V | After buck |
| Wind sensors | 0mA | MOSFET OFF (GPIO15 LOW) |
| **Total Sleep** | **~0.6mA @ 12V** | |

### Active State (~2 seconds per cycle)

| Component | Current @ 12V |
|-----------|--------------|
| ESP32 (80MHz, WiFi off) | ~27mA |
| LoRa TX burst (17dBm) | ~40mA |
| Sensors (BME280+LTR390+DS18B20+Soil) | ~5mA |
| MAX485 active | ~0.5mA |
| Wind sensors (12V direct) | 50mA |
| Buck conversion losses (~10%) | ~12mA |
| **Total Active** | **~135mA @ 12V** |

### Daily Energy (5-min sleep interval, 288 cycles/day)

| Phase | Calculation | Energy |
|-------|------------|--------|
| Sleep: 0.6mA × 23.92h | | 14.4 mAh |
| Active: 135mA × (288 × 2s / 3600) | = 135mA × 0.16h | 21.6 mAh |
| **Daily Total** | | **36.0 mAh @ 12V** |
| **Daily Wh** | 36.0mAh × 12V | **0.43 Wh** |

### Battery Runtime

| Battery | Capacity @ 12V | Runtime (no solar) |
|---------|---------------|-------------------|
| 3S 18650 3000mAh | 3000mAh | ~83 days |
| 3S 18650 3500mAh | 3500mAh | ~97 days |
| 12V 7Ah SLA | 3500mAh usable (50% DoD) | ~97 days |
| 12V 9Ah SLA | 4500mAh usable | ~125 days |

> With a 30W solar panel in Philippines sun (~4.5 peak sun hours = 135Wh/day), the system is net-positive by a huge margin. The 0.43Wh/day draw is less than 0.5% of daily solar harvest.

---

## Complete Bill of Materials (BOM)

### Phase 1 — Bench Testing (paliton karon)

| # | Item | Spec | Qty | Unit Price | Total |
|---|------|------|-----|-----------|-------|
| 1 | 12V DC Adapter | 12V 2A, 5.5×2.1mm barrel plug | 1 | ₱200 | ₱200 |
| 2 | DC Barrel Jack | 5.5×2.1mm female, panel mount, screw terminals | 1 | ₱40 | ₱40 |
| 3 | Schottky Diode | 1N5819, 1A 40V (reverse-polarity protection) | 1 | ₱5 | ₱5 |
| 4 | **Mini560 Buck Module** | 5V fixed output (jumper-selectable) | 1 | ₱85 | ₱85 |
| 5 | **Mini560 Buck Module** | 3.3V fixed output (jumper-selectable) | 1 | ₱85 | ₱85 |
| 6 | IRF9540 | P-channel MOSFET, TO-220 | 1 | ₱30 | ₱30 |
| 7 | 2N7000 | N-channel MOSFET, TO-92 | 1 | ₱12 | ₱12 |
| 8 | Resistor 10kΩ | 1/4W carbon film | 2 | ₱1 | ₱2 |
| 9 | Resistor 1kΩ | 1/4W carbon film | 1 | ₱1 | ₱1 |
| 10 | Resistor 330kΩ | 1/4W carbon film (battery divider R1) | 1 | ₱1 | ₱1 |
| 11 | Resistor 100kΩ | 1/4W carbon film (battery divider R2) | 1 | ₱1 | ₱1 |
| 12 | Resistor 4.7kΩ | 1/4W carbon film (DS18B20 pull-up) | 1 | ₱1 | ₱1 |
| 13 | Capacitor 100µF/25V | Electrolytic (input bulk) | 1 | ₱10 | ₱10 |
| 14 | Capacitor 100µF/16V | Electrolytic (output bulk, one per buck) | 2 | ₱8 | ₱16 |
| 15 | **Perf Board** | 7×9 cm, single-sided, 2.54mm pitch | 1 | ₱55 | ₱55 |
| 16 | Screw Terminal Block | 2-pin, 5mm pitch | 4 | ₱15 | ₱60 |
| 17 | Pin Headers | Male 1×40, 2.54mm | 1 strip | ₱20 | ₱20 |
| 18 | Jumper Wires | Male-to-male, 20cm, 40pcs | 1 set | ₱60 | ₱60 |
| 19 | Solid Core Wire | 22 AWG, red+black, 2m each | 1 set | ₱50 | ₱50 |
| 20 | Heat Shrink Tubing | Assorted, 2mm–6mm | 1 set | ₱40 | ₱40 |
| 21 | Dupont Connectors | Male + female crimp pins + housings | 1 set | ₱50 | ₱50 |
| | | | | **Phase 1 Total** | **₱825** |

### Phase 2 — Solar + Battery (paliton unya)

| # | Item | Spec | Qty | Unit Price | Total |
|---|------|------|-----|-----------|-------|
| 22 | Solar Panel | 30–50W, 18Vmp, monocrystalline | 1 | ₱1,200 | ₱1,200 |
| 23 | Li-Ion Cells | 18650, 3500mAh, protected (Samsung/Panasonic) | 3 | ₱250 | ₱750 |
| 24 | 3S BMS Board | 12.6V, 25A, balance charging | 1 | ₱180 | ₱180 |
| 25 | CN3791 Module | Solar charge controller, 1S–4S configurable | 1 | ₱350 | ₱350 |
| 26 | IP65 Enclosure | ABS waterproof box, 200×150×100mm | 1 | ₱450 | ₱450 |
| 27 | Cable Glands | PG7 or PG9, waterproof | 4 | ₱25 | ₱100 |
| 28 | Mounting Bracket | L-bracket + U-bolts for solar panel | 1 set | ₱200 | ₱200 |
| 29 | XT60 Connectors | Male+female pair (battery disconnect) | 2 pairs | ₱40 | ₱80 |
| 30 | Fuse Holder + Fuse | 2A, inline blade type | 1 | ₱60 | ₱60 |
| | | | | **Phase 2 Total** | **₱3,370** |

### Grand Total

| Phase | Total |
|-------|-------|
| Phase 1 — Bench Testing | ₱825 |
| Phase 2 — Solar + Battery | ₱3,370 |
| **GRAND TOTAL (complete single-node power)** | **₱4,195** |

> **Note:** Prices are estimated from Shopee/Lazada Philippines as of June 2026. ±20% depending on seller and shipping. The BOM is ₱55 more than v1.0 (₱85 extra Mini560 replaces ₱15 HT7333 + 2×₱5 electrolytics — simpler, fewer parts to solder).

---

## Shopee/Lazada Search Terms

| Item | Search Term |
|------|------------|
| Mini560 5V | "mini560 buck 5v module fixed" |
| Mini560 3.3V | "mini560 buck 3.3v module fixed" |
| 1N5819 | "1n5819 schottky diode" |
| IRF9540 | "irf9540 p channel mosfet" |
| 2N7000 | "2n7000 mosfet to-92" |
| Perf board | "perf board 7x9 single sided" |
| Barrel jack | "dc barrel jack panel mount 5.5 2.1 screw terminal" |
| Solar panel | "solar panel 30w 18v monocrystalline" |
| 18650 cells | "18650 3500mah protected samsung panasonic genuine" |
| 3S BMS | "3s bms 12.6v 25a balance" |
| CN3791 | "cn3791 solar charge controller module" |
| IP65 enclosure | "ip65 abs junction box waterproof 200x150x100" |
| Cable gland | "pg7 cable gland waterproof" |
| XT60 | "xt60 connector pair" |

---

## Assembly Order

1. **Solder barrel jack** to perf board edge (2 pins: + and -)
2. **Solder 1N5819 Schottky diode** in series with 12V+ (cathode/stripe toward the circuit). This protects against accidental reverse polarity.
3. **Solder 100µF/25V cap** across 12V input (mind polarity — stripe = negative)
4. **Configure Mini560 #1 for 5V** — bridge the 5V pads with solder
5. **Configure Mini560 #2 for 3.3V** — bridge the 3.3V pads with solder
6. **Mount both Mini560 modules** on perf board — DO NOT connect output to anything yet
7. **Power up with 12V adapter**
8. **Measure Mini560 #1 output** — should read 5.0V ±0.1V. If it's way off, the jumper pads may not be bridged properly.
9. **Measure Mini560 #2 output** — should read 3.3V ±0.05V. ⚠️ If it reads >5V, the jumper is wrong — do NOT connect ESP32.
10. **Solder 100µF/16V cap** across each output (one on 5V, one on 3.3V)
11. **Build MOSFET level-shifter** (IRF9540 + 2N7000 + resistors) in one corner
12. **Verify MOSFET switching**: connect GPIO15 to 3.3V → 12V_SW should read ~12V; connect to GND → 12V_SW should be 0V
13. **Solder output terminal blocks** for each voltage rail
14. **Wire sensors** one at a time, testing each before adding the next
15. **Last step**: connect ESP32-S3 to 3.3V and GND

> ⚠️ **Golden Rule:** Always verify Mini560 output voltages with a multimeter BEFORE connecting the ESP32 or any sensor. A misconfigured jumper (wrong voltage) will destroy downstream electronics instantly. Measure twice, connect once.

---

## Quick Reference: Power Pin Assignments

| Function | GPIO | Voltage | Notes |
|----------|------|---------|-------|
| Sensor PWR MOSFET gate | GPIO15 | 3.3V signal | Switches 12V rail via IRF9540 |
| Battery ADC | GPIO14 | 0–2.93V | 330k/100k divider (12V system) |
| 12V_SW | — | 12V (switched) | Wind sensors V+ |
| 3.3V BUS | — | 3.3V | DIYMORE RS485 VCC |
| 3.3V BUS | — | 3.3V | ESP32, LoRa, BME280, LTR390, DS18B20, Soil |

---

## One-Shot Verification

After assembly, run these checks:

```bash
# 1. Measure all rails (disconnected from ESP32 first)
#    12V in:  ~12.0V (adapter) or 9.0–12.6V (battery)
#    5V out:   5.00V ± 0.1V
#    3.3V out: 3.30V ± 0.05V

# 2. Test MOSFET with a 12V LED or multimeter
#    GPIO15 HIGH → 12V_SW = 12V
#    GPIO15 LOW  → 12V_SW = 0V

# 3. Connect ESP32, flash firmware, open serial monitor
cd ~/dev/projects/weather-station/firmware/weather-node
sg dialout -c "pio run -e s3 -t upload -t monitor"

# 4. In serial output, verify battery reading matches multimeter:
#    Battery: 12.XX V (raw=XXXX)   ← should match adapter/battery voltage
```
