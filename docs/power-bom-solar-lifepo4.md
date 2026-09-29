# Weather Station — Power Supply BOM (Solar + LiFePO4)

**Date:** June 29, 2026  
**Architecture:** Solar Panel → LiFePO4 Charge Controller → 4S LiFePO4 Battery → Power PCB (LM2596 + AMS1117)  
**Total System Voltage:** 12.8V nominal (4S LiFePO4), 14.6V full charge

---

## ⚡ Power Architecture

```
Solar Panel (30-50W, 18Vmp)
    │
    ▼
Charge Controller (CN3791, LiFePO4 profile)
    │
    ├──► 4S LiFePO4 Battery (12.8V / 6-12Ah)
    │       │
    │       ▼
    └──► Power PCB ──┬── LM2596-5.0 ──► +5V (MAX485)
                     │       └── AMS1117-3.3 ──► +3.3V (ESP32 + LoRa + sensors)
                     │
                     ├── MOSFET switch ──► 12V_SW (wind sensors)
                     │
                     └── 390k+100k divider ──► BAT_ADC (ESP32 monitoring)
```

---

## 📦 BOM: Solar + Battery Section

| # | Item | Spec | Qty | Est. Price (₱) | Shopee/Lazada Keywords |
|---|------|------|-----|----------------|------------------------|
| 1 | **Solar Panel** | 30-50W, 18Vmp, monocrystalline | 1 | 800–1,500 | "30W 18V solar panel monocrystalline" |
| 2 | **Solar Charge Controller** | CN3791 module, 4S LiFePO4 configurable, 4A max | 1 | 150–300 | "CN3791 solar charger module 4S" |
| 3 | **LiFePO4 Battery Cells** | 32700 3.2V 6000mAh LiFePO4 | 4 | 200–350 each | "32700 LiFePO4 6000mAh" |
| 4 | **4S LiFePO4 BMS** | 4S 12.8V 30A with balance | 1 | 150–250 | "4S LiFePO4 BMS 12.8V 30A balance" |
| 5 | **Battery Holder** | 32700 4S holder / DIY spot-weld | 1 | 100–250 | "32700 battery holder 4S" |
| 6 | **DC Barrel Jack** | 5.5×2.1mm panel mount (for solar input) | 1 | 30–50 | "DC barrel jack panel mount 5.5 2.1" |
| 7 | **Inline Fuse Holder** | ATC/ATO fuse holder, 12AWG wire | 2 | 40–80 each | "ATC fuse holder inline 12AWG" |
| 8 | **ATC Fuse 10A** | Between solar panel and charge controller | 1 | 15–25 | "ATC fuse 10A blade" |
| 9 | **ATC Fuse 5A** | Between battery and power PCB | 1 | 15–25 | "ATC fuse 5A blade" |
| 10 | **Schottky Diode** | 1N5822 (3A/40V) — anti-backfeed from battery to panel at night | 1 | 15–25 | "1N5822 diode 3A 40V" |
| 11 | **XT60 Connector Pair** | Battery to PCB connection | 1 pair | 40–60 | "XT60 connector pair" |
| 12 | **Silicon Wire** | 14AWG red+black, 1m each | 2m | 80–120 | "14AWG silicone wire red black" |
| 13 | **Heat Shrink Tubing** | Assorted sizes | 1 set | 50–100 | "heat shrink tubing assorted" |
| | | | **Subtotal** | **₱2,000–3,800** | |

### ☀️ Solar Panel Sizing

| Panel | Power | Daily Energy (4.5 sun hrs) | Node Daily Consumption | Net Surplus |
|-------|-------|---------------------------|----------------------|-------------|
| **30W** | 30W | 135 Wh/day | ~10.4 Wh/day (0.43W avg × 24h) | **+124.6 Wh** ✅ |
| 50W | 50W | 225 Wh/day | ~10.4 Wh/day | **+214.6 Wh** ✅ |

30W panel is already **13× more** than needed. 50W gives more cloudy-day buffer.
Node total consumption: ~300mA @ 12V avg × 24h = 86.4 Wh/day worst case, still net positive.

### 🔋 LiFePO4 Battery Sizing

| Capacity | Cells | Runtime (no sun) | Weight | Est. Cost |
|----------|-------|------------------|--------|-----------|
| **6Ah** | 4× 32700 6000mAh | ~20 hours | ~580g | ₱800–1,400 |
| 12Ah | 4× 32700 6000mAh ×2 parallel | ~40 hours | ~1.2kg | ₱1,600–2,800 |

6Ah is enough — with 30W solar, battery recharges fully in <2 hours of sun.

### ⚙️ CN3791 Configuration for LiFePO4 (4S)

The CN3791 module needs resistor configuration for LiFePO4 voltage:

| Parameter | LiFePO4 Value | Resistor Formula |
|-----------|--------------|------------------|
| Float voltage | **14.6V** (3.65V/cell × 4) | R_fb = (V_bat / 2.416 - 1) × R_ref |
| MPPT voltage | **18V** (panel Vmp) | Set by input divider |
| Charge current | 2A max (safe for 32700) | R_sense = 0.12 / I_charge |
| Termination | C/10 (600mA for 6Ah) | Automatic |

**Important:** Some CN3791 modules come pre-set for Li-Ion (12.6V). Check/modify the feedback resistors. If hassle, use an **XY-L30A** or **XH-M604** charge controller instead — direct voltage setting via potentiometer, no resistor math.

### 🪫 LiFePO4 Voltage Divider for BAT_ADC

| Component | Old (Li-Ion 3S) | New (LiFePO4 4S) |
|-----------|----------------|-------------------|
| R3 (top) | 330k | **390k** |
| R4 (bottom) | 100k | 100k |
| Ratio | 4.30 | **4.90** |
| ADC at 14.6V | — | 2.98V ✅ |
| ADC at 12.8V | — | 2.61V |
| ADC at 10.0V (empty) | — | 2.04V |

```cpp
// Updated for LiFePO4 4S
#define BAT_R1  390.0   // kΩ (top resistor — UPDATED from 330k)
#define BAT_R2  100.0   // kΩ (bottom resistor)
#define BAT_DIVIDER ((BAT_R1 + BAT_R2) / BAT_R2)  // = 4.90
```

---

## 📦 BOM: Power PCB Section (already designed)

| # | Ref | Value | Qty | Unit Price (₱) | Shopee/Lazada Keywords |
|---|-----|-------|-----|---------------|------------------------|
| 14 | J1 | DC Barrel Jack (PCB mount) | 1 | 15–25 | "DC barrel jack PCB 5.5 2.1" |
| 15 | F1 | PTC 5A resettable fuse | 1 | 15–30 | "PTC fuse 5A resettable" |
| 16 | D1, D2 | SS34 Schottky 3A/40V SMD | 2 | 5–10 each | "SS34 SMD diode" |
| 17 | C1 | 100µF/35V electrolytic | 1 | 10–20 | "100uF 35V electrolytic capacitor" |
| 18 | C2, C5 | 100nF ceramic | 2 | 3–5 each | "100nF ceramic capacitor" |
| 19 | **U1** | **LM2596-5.0 fixed** TO-220-5 | 1 | 60–100 | "LM2596-5.0 fixed TO-220" |
| 20 | C3 | 220µF/16V electrolytic | 1 | 10–20 | "220uF 16V electrolytic capacitor" |
| 21 | C4, C6 | 10µF ceramic/electrolytic | 2 | 5–10 each | "10uF 16V capacitor" |
| 22 | L1 | 68µH inductor (3A rated) | 1 | 30–60 | "68uH inductor 3A toroidal" |
| 23 | **U2** | **AMS1117-3.3** SOT-223 | 1 | 15–30 | "AMS1117-3.3 SOT-223" |
| 24 | Q1 | IRF9540N P-ch MOSFET TO-220 | 1 | 30–60 | "IRF9540N TO-220 MOSFET" |
| 25 | Q2 | 2N7000 N-ch MOSFET TO-92 | 1 | 10–20 | "2N7000 TO-92 MOSFET" |
| 26 | R1 | 10kΩ 1/4W resistor | 1 | 2–5 | "10k ohm resistor 1/4W" |
| 27 | R2 | 1kΩ 1/4W resistor | 1 | 2–5 | "1k ohm resistor 1/4W" |
| 28 | R3 | **390kΩ** 1/4W resistor (LiFePO4) | 1 | 2–5 | "390k ohm resistor 1/4W" |
| 29 | R4 | 100kΩ 1/4W resistor | 1 | 2–5 | "100k ohm resistor 1/4W" |
| 30 | J2–J4 | Screw terminal 2P 5.08mm | 3 | 10–15 each | "screw terminal 2P 5.08mm PCB" |
| 31 | J5–J6 | Pin header 2P 2.54mm male | 2 | 3–5 each | "pin header 2P 2.54mm male" |
| 32 | PCB | Custom PCB (JLCPCB 5pcs) | 5 | ~400 | "JLCPCB 2-layer 60×50mm" |
| | | | **Subtotal** | **~₱780–1,200** | |

---

## 📦 BOM: Enclosure & Misc

| # | Item | Spec | Qty | Est. Price (₱) | Keywords |
|---|------|------|-----|----------------|---------|
| 33 | Waterproof Enclosure | ABS junction box, min 200×150×100mm | 1 | 250–500 | "ABS waterproof junction box outdoor" |
| 34 | Cable Glands | PG9 or PG11, 3-6mm cable | 4 | 15–25 each | "PG9 cable gland waterproof" |
| 35 | DIN Rail Mount | Optional, for clean install | 1 | 50–100 | "DIN rail mount bracket" |
| 36 | Nylon Standoffs | M3 hex, assorted heights | 1 set | 30–60 | "M3 nylon standoff kit" |
| 37 | M3 Screws + Nuts | Stainless, assorted | 1 set | 50–100 | "M3 screw nut stainless kit" |
| 38 | Zip Ties | 100mm, UV-resistant black | 1 pack | 30–50 | "UV zip tie 100mm black" |
| 39 | Silicone Sealant | Neutral cure (for cable glands) | 1 tube | 80–150 | "silicone sealant neutral cure" |
| | | | **Subtotal** | **₱600–1,200** | |

---

## 💰 Total Cost Summary

| Section | Low Est. | High Est. |
|---------|---------|-----------|
| Solar + Battery | ₱2,000 | ₱3,800 |
| Power PCB | ₱780 | ₱1,200 |
| Enclosure + Misc | ₱600 | ₱1,200 |
| **TOTAL** | **₱3,380** | **₱6,200** |

Kung naa na kay uban parts (wires, connectors, solder), mas cheaper pa.

---

## 🔄 Alternative: Ready-Made Solar Charge Controller

Kung hassle ang CN3791 configuration, pwede ni:

| Controller | Price (₱) | Notes |
|-----------|-----------|-------|
| **XY-L30A** | 250–400 | Adjustable voltage relay controller, 30A, NOT solar-optimized |
| **XH-M604** | 200–350 | Battery charge control module, voltage set via pot |
| **PWM 10A LiFePO4** | 400–700 | Dedicated solar PWM, pre-set for LiFePO4 4S |
| **MPPT 10A** (EPEver clone) | 800–1,500 | True MPPT, better efficiency, LCD display |

Recommended: **PWM 10A LiFePO4 controller** — plug and play, no configuration, ₱400–700.

---

## ⚠️ Reminders

1. **Diode between solar panel and CN3791**: 1N5822 Schottky prevents battery from back-feeding into the panel at night (some CN3791 modules have this built-in — check)
2. **BMS is REQUIRED**: LiFePO4 cells MUST have a balance BMS — overcharge = fire risk, over-discharge = permanent cell damage
3. **32700 cells**: Spot-weld or use a 4S holder. Do NOT solder directly to cell terminals — heat damages LiFePO4 cells
4. **Fuse BEFORE and AFTER charge controller**: 10A panel-side, 5A battery-side
5. **Enclosure ventilation**: Charge controller and LM2596 generate heat. Add small vent holes or a breather vent
6. **Update R3 to 390k**: LiFePO4 14.6V full charge > Li-Ion 12.6V. Old 330k divider would saturate ESP32 ADC
