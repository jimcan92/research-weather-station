"""Generate a standalone ESP32-S3 <-> E22-900T22D LoRa UART schematic.

This is intentionally separate from weather-node-complete.kicad_sch.

E22 header order supplied by Jim:
  1=M0, 2=M1, 3=RXD, 4=TXD, 5=AUX, 6=VCC, 7=GND

GPIO assignment:
  M0  -> GPIO4
  M1  -> GPIO5
  RXD -> GPIO6 (ESP TX to E22 RXD)
  TXD -> GPIO7 (E22 TXD to ESP RX)
  AUX -> GPIO8

Usage: /tmp/kicad-mcp-venv/bin/python gen_lora_e22.py
"""
import sys
sys.path.insert(0, "/tmp/kicad-mcp-venv/lib/python3.11/site-packages")

import kicad_sch_api as ksa
from kicad_sch_api.library.cache import get_symbol_cache

CUSTOM_ESP_LIB = (
    "/home/jimcan/dev/projects/weather-station/hardware/"
    "node-pcb/ESP32-S3-N16R8.kicad_sym"
)
get_symbol_cache().add_library_path(CUSTOM_ESP_LIB)

sch = ksa.create_schematic("ESP32-S3 to E22-900T22D LoRa")
sch.set_paper_size("A4")
sch.set_title_block({
    "title": "ESP32-S3 to E22-900T22D LoRa",
    "date": "2026-08-25",
    "rev": "v1.0 — UART LoRa module",
})

# Components — positive A4 coordinates (origin is top-left).
sch.components.add(
    "ESP32-S3-N16R8:ESP32-S3-N16R8", "U1", "ESP32-S3-N16R8",
    position=(105.41, 50.80),
)
sch.components.add(
    "Connector:Conn_01x07_Pin", "U2", "E22-900T22D",
    position=(218.44, 78.74),
)
sch.components.add(
    "Connector:Screw_Terminal_01x02", "J1", "5V_IN",
    position=(35.56, 35.56),
)
sch.components.add("Device:C_Polarized", "C1", "470uF/10V", position=(190.50, 116.84))
sch.components.add("Device:C", "C2", "100nF", position=(218.44, 116.84))
sch.components.add("power:PWR_FLAG", "#FLG01", "PWR_FLAG", position=(63.50, 35.56))
sch.components.add("power:PWR_FLAG", "#FLG02", "PWR_FLAG", position=(63.50, 50.80))

failures = []

def pin_exists(ref, pin):
    return sch.get_component_pin_position(ref, str(pin)) is not None

def add_net(name, nodes):
    for ref, pin in nodes:
        if not pin_exists(ref, pin):
            failures.append((name, ref, pin))
            continue

        # Keep labels outside Jim's custom ESP32 symbol. A short wire stub
        # clears the body/pin-number area before the label begins.
        if ref == "U1" and 25 <= int(pin) <= 42:  # right-side GPIO/RST pins
            pos = sch.get_component_pin_position(ref, str(pin))
            end = (pos.x + 10.16, pos.y)
            sch.add_wire((pos.x, pos.y), end)
            sch.add_label(name, position=end, rotation=0)
        elif ref == "U1" and 3 <= int(pin) <= 19:  # left-side GPIO pins
            pos = sch.get_component_pin_position(ref, str(pin))
            end = (pos.x - 10.16, pos.y)
            sch.add_wire((pos.x, pos.y), end)
            sch.add_label(name, position=end, rotation=180)
        else:
            sch.add_label(name, pin=(ref, str(pin)))

def mark_nc(ref, pin):
    pos = sch.get_component_pin_position(ref, str(pin))
    if pos is None:
        failures.append(("NC", ref, pin))
        return
    sch._no_connects.add((pos.x, pos.y))

# Power. E22 VCC uses the 5V rail; UART I/O remains 3.3V logic.
add_net("+5V", [
    ("J1", 1), ("#FLG01", 1), ("U1", 43), ("U2", 6), ("C1", 1), ("C2", 1),
])
add_net("GND", [
    ("J1", 2), ("#FLG02", 1),
    ("U1", 1), ("U1", 2), ("U1", 22), ("U1", 44),
    ("U2", 7), ("C1", 2), ("C2", 2),
])

# E22 UART/mode signals. Pin order is exactly Jim's supplied order.
add_net("E22_M0", [("U2", 1), ("U1", 26)])       # GPIO4
add_net("E22_M1", [("U2", 2), ("U1", 27)])       # GPIO5
add_net("E22_RXD", [("U2", 3), ("U1", 28)])      # GPIO6 = ESP TX
add_net("E22_TXD", [("U2", 4), ("U1", 29)])      # GPIO7 = ESP RX
add_net("E22_AUX", [("U2", 5), ("U1", 34)])      # GPIO8

# Everything else on the ESP32 symbol is intentionally unused in this standalone sheet.
used_u1 = {1, 2, 22, 26, 27, 28, 29, 34, 43, 44}
for pin in range(1, 45):
    if pin not in used_u1:
        mark_nc("U1", pin)

# Section labels and clear pin-map notes.
sch.add_text("[ POWER INPUT ]", position=(35.56, 20.32))
sch.add_text("[ ESP32-S3 N16R8 ]", position=(105.41, 25.40))
sch.add_text("[ E22-900T22D UART LoRa ]", position=(218.44, 50.80))

notes = [
    "E22 PIN ORDER: 1=M0, 2=M1, 3=RXD, 4=TXD, 5=AUX, 6=VCC, 7=GND",
    "GPIO4 -> M0 | GPIO5 -> M1 | GPIO6 (ESP TX) -> RXD",
    "GPIO7 (ESP RX) <- TXD | GPIO8 <- AUX",
    "VCC = +5V; UART logic is 3.3V. C1 470uF + C2 100nF near E22 VCC/GND.",
    "M0/M1 select operating mode; AUX reports module busy/ready state.",
]
y = 134.62
for note in notes:
    sch.add_text(note, position=(148.59, y))
    y += 6.35

OUTPUT = "/home/jimcan/dev/projects/weather-station/hardware/lora-e22/lora-e22-900t22d.kicad_sch"
sch.save(OUTPUT)

# Repair kicad-sch-api 0.5.6 title-block serialization.
with open(OUTPUT, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace(
    "\t(title_block\n"
    "\t\t(title {'title': 'ESP32-S3 to E22-900T22D LoRa', 'date': '2026-08-25', "
    "'rev': 'v1.0 — UART LoRa module'})\n"
    "\t)",
    "\t(title_block\n"
    "\t\t(title \"ESP32-S3 to E22-900T22D LoRa\")\n"
    "\t\t(date \"2026-08-25\")\n"
    "\t\t(rev \"v1.0 — UART LoRa module\")\n"
    "\t\t(company \"CTU Moalboal — Research\")\n"
    "\t)",
)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Generated: {OUTPUT}")
print(f"Components: {len(list(sch.components.all()))}")
print(f"Failed pins: {len(failures)}")
for failure in failures:
    print("FAIL:", failure)
