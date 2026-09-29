# Weather Station — Session Progress Log

> **Canonical hardware decision (2026-09-03):** The final weather-node design is `hardware/node-pcb/weather-node-complete.kicad_sch`, using one Mini560 for 12V→5V and an AMS1117-3.3 for 5V→3.3V. LM2596 and dual-Mini560 entries below are retained as historical alternatives.

## 2026-06-29 to 2026-07-08: Power Supply Design & Shopping

### ✅ Completed

1. **Power Supply Architecture v3.0 — LM2596 + AMS1117**
   - Same design as vending machine for parts availability
   - Schematic generated at `hardware/power-pcb/weather-power-v3.kicad_sch`
   - 24 components, KiCad 9.0 format, net labels as wiring reference
   - See `docs/power-configuration.md` for full architecture

2. **Prototype Decision**
   - Phase 1 (now): Mini560 ×2 on perf board for prototyping
   - Phase 2 (final): Custom PCB with LM2596-5.0 + AMS1117-3.3

3. **Solar + Battery Design**
   - 50W 18V Solar Panel with 10A PWM Controller
   - 4S LiFePO4 32650 cells (6500mAh ×8 for dual pack)
   - 2× 4S 15A BMS + 2× Active Balancer
   - See `docs/power-bom-solar-lifepo4.md` for complete BOM

4. **LiFePO4 Voltage Divider Updated**
   - R3 changed from 330k → **390k** (for 14.6V full charge)
   - Ratio: 4.90 (390k + 100k divider)
   - Firmware: `#define BAT_DIVIDER 4.90`

5. **MOSFET Switch — P-channel parts resolved**
   - IRF4905PBF (replacement for rare IRF9540N) — ₱150
   - 2N7000 N-ch MOSFET for level shifting — ₱120
   - Circuit: GPIO15 HIGH → 2N7000 ON → IRF4905 gate LOW → 12V flows to wind sensors

6. **Complete Shopping Cart — ₱9,860**
   - Battery: 8× 32650, 2× BMS, 2× balancer, hardware
   - Solar: 50W panel + 10A controller, PV cable
   - Power: Mini560 5V+3.3V, MOSFETs, 1N5822, PTC 5A, 1000µF/35V cap
   - Connectors: Terminal blocks, XT60, M12+M16 glands, waterproof 5P
   - Sensors: DS18B20 ×5, OLED 1.3", SD module
   - Enclosure: M3 inserts, screws, 5-core 20AWG cable

7. **Existing Parts (already owned)**
   - BME280, LTR390, ESP32-S3 HW678
   - LoRa module + antenna (SX1278/SX1262)
   - RS485 Wind Sensors (anemometer + wind vane)
   - MAX485 module, soil moisture, rain gauge
   - Resistors (all values)

### 📐 Architecture Decisions

- **2-Box Split Design**: Power box (battery, buck converters) separate from Stevenson screen (ESP32, sensors). Prevents Mini560/ESP32 heat from affecting BME280 temperature accuracy.
- **3D Printed Enclosure**: Jim + partner will design and print.
- **Inter-box cable**: 12V + 5V + GND (3 wires) via waterproof 5P connector.
- **LoRa antenna**: OK to stay inside PLA Stevenson screen (no metal blocking).

### ⚠️ Pending / Not Yet Purchased

- SMA bulkhead pigtail (₱50-100) — only needed if metal enclosure for ESP box
- Waterproof enclosure (3D print instead)
- Cable glands for ground sensors

### 📂 Key Files

| File | Description |
|------|-------------|
| `hardware/power-pcb/weather-power-v3.kicad_sch` | Power schematic v3.0 (LM2596) |
| `hardware/power-pcb/weather-power-pcb.kicad_sch` | Old power schematic v2.0 (Mini560) |
| `hardware/power-pcb/weather-power-pcb.kicad_pcb` | Old PCB layout v2.0 |
| `hardware/power-pcb/README.md` | Updated for v3.0 |
| `docs/power-configuration.md` | Updated to v3.0 LM2596 architecture |
| `docs/power-bom-solar-lifepo4.md` | Solar + LiFePO4 BOM |
| `docs/power-bom-shopee-complete.md` | Complete Shopee BOM with search keywords |

## 2026-09-29: Four-wire automatic RS485 module

- Updated canonical complete KiCad schematic and generator to DIYMORE isolated auto-direction module, using the supplied photo's VCC/TXD/RXD/GND and A+/B−/earth terminals.
- TTL supply 3.3V; removed MAX485 DE/RE and R8/R9 divider; GPIO16 unused; C7=100nF; R10=120Ω DNP pending onboard termination check.
- UART crossing remains explicitly provisional until exact module input/output directions are confirmed. Earth is left unconnected, separate from TTL GND.
- Updated sensor, pin and power guides. Firmware was not changed; existing GPIO16 control is obsolete for this module.
- Native schematic syntax/connectivity checked locally. KiCad CLI and kicad-sch-api are unavailable; ERC, generator execution and full-sheet re-export remain unverified.
- Existing full-sheet PDF/SVG/PNG previews predate this change. Use the native schematic and rs485-module-wiring.svg for the updated circuit.
