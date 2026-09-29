#!/usr/bin/env python3
"""
Weather Station Node Carrier PCB — kicad-sch-api version.
All components placed, NO wiring. Jim handles connections in KiCad GUI.

Usage: /tmp/kicad-mcp-venv/bin/python gen_node_sch.py
"""

import sys
sys.path.insert(0, "/tmp/kicad-mcp-venv/lib/python3.14/site-packages")

import kicad_sch_api as ksa

# ═══════════════════════════════════════════════════════════════════
# A3 page, 1.27mm (50mil) grid
# +Y = DOWN on page. Center = (0, 0).
# ═══════════════════════════════════════════════════════════════════

sch = ksa.create_schematic("Weather Station — ESP32-S3 Node Carrier PCB")
sch.set_paper_size("A3")
sch.set_title_block({
    "title": "Weather Station — ESP32-S3 Node Carrier PCB",
    "date": "2026-06-14",
    "rev": "v1.0-draft",
    "company": "Jimboy Cantila — coe-research",
})

G = 1.27  # grid spacing in mm
def Gx(n):
    """Convert grid units to mm, aligned to 1.27mm grid."""
    return round(n * G, 2)

# ═══════════════════════════════════════════════════════════════════
# SECTION: Power Input + MOSFET Switch + Battery Divider
# ═══════════════════════════════════════════════════════════════════

# 12V Input
sch.add_text("=== POWER SECTION ===", position=(Gx(-32), Gx(-22)))
sch.components.add("Connector:Screw_Terminal_01x02", "J1", "12V_IN",
                   position=(Gx(-32), Gx(-18)))

# 5V Input
sch.components.add("Connector:Screw_Terminal_01x02", "J2", "5V_IN",
                   position=(Gx(-32), Gx(-14)))

# 3.3V Input
sch.components.add("Connector:Screw_Terminal_01x02", "J3", "3.3V_IN",
                   position=(Gx(-32), Gx(-10)))

# P-ch MOSFET (12V switch)
sch.components.add("Transistor_FET:IRF9540N", "Q1", "IRF9540N",
                   position=(Gx(-24), Gx(-18)))

# N-ch MOSFET (level shifter)
sch.components.add("Transistor_FET:2N7000", "Q2", "2N7000",
                   position=(Gx(-24), Gx(-12)))

# 10k pull-up (Q1 gate to 12V)
sch.components.add("Device:R", "R1", "10k",
                   position=(Gx(-18), Gx(-18)), rotation=90)

# 1k gate resistor (GPIO15 to Q2 gate)
sch.components.add("Device:R", "R2", "1k",
                   position=(Gx(-18), Gx(-12)), rotation=90)

# Battery voltage divider
sch.components.add("Device:R", "R3", "330k",
                   position=(Gx(-12), Gx(-18)))
sch.components.add("Device:R", "R4", "100k",
                   position=(Gx(-12), Gx(-12)))

# Net labels for power rails
sch.add_global_label("+12V", position=(Gx(-35), Gx(-18)))
sch.add_global_label("+5V", position=(Gx(-35), Gx(-14)))
sch.add_global_label("+3.3V", position=(Gx(-35), Gx(-10)))
sch.add_global_label("GND", position=(Gx(-32), Gx(-6)))
sch.add_global_label("GND", position=(Gx(-24), Gx(-4)))
sch.add_global_label("GND", position=(Gx(-12), Gx(-4)))

# Signal labels
sch.add_label("GPIO15", position=(Gx(-20), Gx(-16)))
sch.add_label("BAT_ADC", position=(Gx(-14), Gx(-20)))
sch.add_label("12V_SW", position=(Gx(-26), Gx(-20)))

# ═══════════════════════════════════════════════════════════════════
# SECTION: MCU — ESP32-S3 HW678 DevKitC-1 Headers
# ═══════════════════════════════════════════════════════════════════

sch.add_text("=== MCU — ESP32-S3 HW678 N16R8 ===", position=(Gx(-4), Gx(-22)))

# J1 — Left header (pins 1-22, 2 rows × 11)
sch.components.add("Connector_Generic:Conn_02x11_Odd_Even", "J4",
                   "ESP32-S3 J1 (Left)",
                   position=(Gx(-6), Gx(-12)),
                   footprint="Connector_PinHeader_2.54mm:PinHeader_2x11_P2.54mm_Vertical")

# J3 — Right header (pins 1-22, 2 rows × 11)
sch.components.add("Connector_Generic:Conn_02x11_Odd_Even", "J5",
                   "ESP32-S3 J3 (Right)",
                   position=(Gx(6), Gx(-12)),
                   footprint="Connector_PinHeader_2.54mm:PinHeader_2x11_P2.54mm_Vertical")

# Net labels for key MCU pins (reference for Jim)
sch.add_label("LoRa_NSS/GPIO4", position=(Gx(-10), Gx(-2)))
sch.add_label("LoRa_SCK/GPIO5", position=(Gx(-10), Gx(-3)))
sch.add_label("LoRa_MOSI/GPIO6", position=(Gx(-10), Gx(-4)))
sch.add_label("LoRa_MISO/GPIO7", position=(Gx(-10), Gx(-5)))
sch.add_label("LoRa_RST/GPIO8", position=(Gx(-10), Gx(-6)))
sch.add_label("LoRa_DIO0/GPIO9", position=(Gx(-10), Gx(-7)))
sch.add_label("I2C_SDA/GPIO1", position=(Gx(10), Gx(-2)))
sch.add_label("I2C_SCL/GPIO2", position=(Gx(10), Gx(-3)))
sch.add_label("OneWire/GPIO3", position=(Gx(-10), Gx(-9)))
sch.add_label("RAIN/GPIO10", position=(Gx(-10), Gx(-10)))
sch.add_label("SOIL/GPIO13", position=(Gx(-10), Gx(-11)))
sch.add_label("BAT_ADC/GPIO14", position=(Gx(-10), Gx(-12)))
sch.add_label("PWR_MOSFET/GPIO15", position=(Gx(-10), Gx(-13)))
sch.add_label("RS485_DE/GPIO16", position=(Gx(10), Gx(-5)))
sch.add_label("RS485_TX/GPIO17", position=(Gx(10), Gx(-6)))
sch.add_label("RS485_RX/GPIO18", position=(Gx(10), Gx(-7)))
sch.add_label("RGB_LED/GPIO48", position=(Gx(10), Gx(-9)))

# ═══════════════════════════════════════════════════════════════════
# SECTION: LoRa — SX1278 Module (915 MHz)
# ═══════════════════════════════════════════════════════════════════

sch.add_text("=== LoRa — SX1278 915 MHz ===", position=(Gx(22), Gx(-22)))

sch.components.add("Connector_Generic:Conn_02x07_Odd_Even", "U1",
                   "SX1278 LoRa",
                   position=(Gx(24), Gx(-14)),
                   footprint="")

sch.add_label("NSS", position=(Gx(20), Gx(-6)))
sch.add_label("SCK", position=(Gx(20), Gx(-7)))
sch.add_label("MOSI", position=(Gx(20), Gx(-8)))
sch.add_label("MISO", position=(Gx(20), Gx(-9)))
sch.add_label("RST", position=(Gx(20), Gx(-10)))
sch.add_label("DIO0", position=(Gx(20), Gx(-11)))

# ═══════════════════════════════════════════════════════════════════
# SECTION: I2C Sensors — BME280 + LTR390
# ═══════════════════════════════════════════════════════════════════

sch.add_text("=== I2C Sensors ===", position=(Gx(-30), Gx(2)))

# BME280 breakout (4 pins: VCC, GND, SDA, SCL)
sch.components.add("Connector:Conn_01x04_Pin", "U2",
                   "BME280 (0x76)",
                   position=(Gx(-28), Gx(6)))

# LTR390 breakout (4 pins: VCC, GND, SDA, SCL)
sch.components.add("Connector:Conn_01x04_Pin", "U3",
                   "LTR390 (0x53)",
                   position=(Gx(-28), Gx(12)))

# I2C pull-up resistors (4.7k each for SDA and SCL)
sch.components.add("Device:R", "R5", "4.7k",
                   position=(Gx(-22), Gx(6)), rotation=90)
sch.components.add("Device:R", "R6", "4.7k",
                   position=(Gx(-22), Gx(10)), rotation=90)

sch.add_label("I2C_SDA", position=(Gx(-31), Gx(6)))
sch.add_label("I2C_SCL", position=(Gx(-31), Gx(10)))
sch.add_label("+3.3V", position=(Gx(-31), Gx(4)))

# ═══════════════════════════════════════════════════════════════════
# SECTION: OneWire — DS18B20
# ═══════════════════════════════════════════════════════════════════

sch.add_text("=== OneWire ===", position=(Gx(-30), Gx(16)))

sch.components.add("Connector:Conn_01x03_Pin", "J6",
                   "DS18B20",
                   position=(Gx(-28), Gx(20)),
                   footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")

sch.components.add("Device:R", "R7", "4.7k",
                   position=(Gx(-22), Gx(20)), rotation=90)

sch.add_label("OneWire", position=(Gx(-31), Gx(20)))

# ═══════════════════════════════════════════════════════════════════
# SECTION: Digital / Analog Sensors — Rain Gauge + Soil Moisture
# ═══════════════════════════════════════════════════════════════════

sch.add_text("=== Digital / Analog ===", position=(Gx(-8), Gx(2)))

sch.components.add("Connector:Conn_01x02_Pin", "J7",
                   "Rain Gauge",
                   position=(Gx(-6), Gx(6)),
                   footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")

sch.components.add("Connector:Conn_01x03_Pin", "J8",
                   "Soil Moisture",
                   position=(Gx(-6), Gx(12)),
                   footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")

sch.add_label("RAIN_INT", position=(Gx(-9), Gx(6)))
sch.add_label("SOIL_ADC", position=(Gx(-9), Gx(12)))

# ═══════════════════════════════════════════════════════════════════
# SECTION: RS485 — MAX485 + Wind Sensor Terminal
# ═══════════════════════════════════════════════════════════════════

sch.add_text("=== RS485 — Wind Sensors ===", position=(Gx(14), Gx(2)))

sch.components.add("Interface_UART:MAX485E", "U4",
                   "MAX485",
                   position=(Gx(16), Gx(8)),
                   footprint="Package_DIP:DIP-8_W7.62mm")

sch.components.add("Connector:Screw_Terminal_01x04", "J9",
                   "Wind Sensor (RS485)",
                   position=(Gx(22), Gx(8)))

sch.add_label("RS485_DE", position=(Gx(13), Gx(6)))
sch.add_label("RS485_TX", position=(Gx(13), Gx(8)))
sch.add_label("RS485_RX", position=(Gx(13), Gx(10)))
sch.add_label("RS485_A", position=(Gx(20), Gx(6)))
sch.add_label("RS485_B", position=(Gx(20), Gx(8)))

# ═══════════════════════════════════════════════════════════════════
# SECTION: Notes
# ═══════════════════════════════════════════════════════════════════

sch.add_text("NOTES:", position=(Gx(-32), Gx(26)))
sch.add_text("1. I2C bus: BME280 (0x76) + LTR390 (0x53) share SDA/SCL pins — no address conflict",
             position=(Gx(-32), Gx(27)))
sch.add_text("2. RS485: Anemometer (ID1) + Wind Vane (ID2) share same A/B bus",
             position=(Gx(-32), Gx(28)))
sch.add_text("3. Pull-ups required: SDA/SCL (4.7k to 3.3V), DS18B20 DQ (4.7k to 3.3V)",
             position=(Gx(-32), Gx(29)))
sch.add_text("4. ESP32-S3 HW678 N16R8 — 16MB Flash, 8MB Octal PSRAM. GPIO35-37 reserved.",
             position=(Gx(-32), Gx(30)))
sch.add_text("5. Q1+Q2 form 12V level-shifted switch (GPIO15 3.3V drives IRF9540N gate via 2N7000).",
             position=(Gx(-32), Gx(31)))
sch.add_text("6. Battery ADC divider: 330k + 100k (ratio 4.30). 12.6V full → 2.93V at ADC pin.",
             position=(Gx(-32), Gx(32)))

# ═══════════════════════════════════════════════════════════════════
# Save
# ═══════════════════════════════════════════════════════════════════

import os
out_dir = os.path.expanduser("~/dev/projects/weather-station/hardware/node-pcb")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "weather-node.kicad_sch")
sch.save(out_path)
print(f"OK — {out_path}")
print(f"   Paper: A3 | Components: 25 placed | No wiring")
