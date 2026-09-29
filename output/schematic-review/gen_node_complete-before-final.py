"""Generate the COMPLETE, FULLY-WIRED weather station node schematic.

Power (Mini560 + AMS1117 + IRF4905 switch + divider) + ESP32-S3 HW678
+ LoRa + MAX485 + all sensors — every net drawn with real wires.

Uses kicad-sch-api pin-to-pin wiring (add_wire_between_pins).

Usage: /tmp/kicad-mcp-venv/bin/python gen_node_complete.py
"""
import sys
sys.path.insert(0, '/tmp/kicad-mcp-venv/lib/python3.11/site-packages')
import kicad_sch_api as ksa
from kicad_sch_api.library.cache import get_symbol_cache
from kicad_sch_api.core.pin_utils import get_component_pin_info

# Register Jim's custom Mini560 symbol library
get_symbol_cache().add_library_path(
    "/home/jimcan/dev/projects/weather-station/hardware/power-pcb/weather-power.kicad_sym"
)
get_symbol_cache().add_library_path(
    "/home/jimcan/dev/projects/weather-station/hardware/node-pcb/ESP32-S3-N16R8.kicad_sym"
)

sch = ksa.create_schematic("Weather Station Node — Complete (Wired)")
sch.set_paper_size("A3")
sch.set_title_block({
    "title": "Weather Station Node — Complete",
    "date": "2026-08-20",
    "rev": "v1.0 — fully wired (Mini560 + AMS1117)",
})

# A3 KiCad sheet coordinates are positive from the top-left. Keep the logical
# layout centered by translating the original local coordinates onto the page.
SHIFT_X = 209.55  # 165 × 1.27 mm
SHIFT_Y = 148.59  # 117 × 1.27 mm

def P(x, y):
    return (x + SHIFT_X, y + SHIFT_Y)

# ══════════════════════════════════════════════════════════════════
# PLACE COMPONENTS (A3, 1.27mm grid, +Y = DOWN)
# ══════════════════════════════════════════════════════════════════

# --- INPUT & PROTECTION (far left) ---
sch.components.add("Connector:Barrel_Jack", "J1", "DC_IN_12V", position=P(-190.5, -127.0))
sch.components.add("Device:Fuse", "F1", "PTC_5A", position=P(-190.5, -101.6))
sch.components.add("Device:D_Schottky", "D1", "1N5822", position=P(-190.5, -88.9))
sch.components.add("Device:C_Polarized", "C1", "100uF/35V", position=P(-190.5, -76.2))

# --- BUCK + LDO ---
sch.components.add("weather-power:Mini560", "U1", "Mini560 (12V->5V)", position=P(-114.3, -127.0))
sch.components.add("Regulator_Linear:AMS1117-3.3", "U2", "AMS1117-3.3", position=P(-114.3, -82.55))
sch.components.add("Device:C", "C2", "100nF", position=P(-139.7, -69.85))
sch.components.add("Device:C", "C3", "10uF", position=P(-88.9, -69.85))
sch.components.add("power:PWR_FLAG", "#FLG01", "PWR_FLAG", position=P(-76.2, -82.55))
sch.components.add("power:PWR_FLAG", "#FLG02", "PWR_FLAG", position=P(-76.2, -69.85))
sch.components.add("power:PWR_FLAG", "#FLG03", "PWR_FLAG", position=P(-63.5, -127.0))

# --- MOSFET SWITCH + DIVIDER ---
sch.components.add("Transistor_FET:IRF4905", "Q1", "IRF4905 (P-ch)", position=P(-38.1, -127.0))
sch.components.add("Transistor_FET:2N7000", "Q2", "2N7000 (N-ch)", position=P(-38.1, -82.55))
sch.components.add("Device:R", "R1", "10k", position=P(-12.7, -127.0))
sch.components.add("Device:R", "R2", "1k", position=P(-12.7, -101.6))
sch.components.add("Device:R", "R3", "390k", position=P(-12.7, -69.85))
sch.components.add("Device:R", "R4", "100k", position=P(12.7, -69.85))

# --- OUTPUT TERMINALS ---
sch.components.add("Connector:Screw_Terminal_01x02", "J2", "12V_SW_OUT", position=P(76.2, -127.0))
sch.components.add("Connector:Screw_Terminal_01x02", "J3", "5V_OUT", position=P(76.2, -107.95))
sch.components.add("Connector:Screw_Terminal_01x02", "J4", "3.3V_OUT", position=P(76.2, -95.25))
sch.components.add("Connector:Conn_01x02_Pin", "J5", "GPIO15", position=P(76.2, -82.55))
sch.components.add("Connector:Conn_01x02_Pin", "J6", "BAT_ADC", position=P(76.2, -69.85))

# --- ESP32-S3 N16R8 module (Jim's custom 44-pin symbol) ---
sch.components.add("ESP32-S3-N16R8:ESP32-S3-N16R8", "U5",
                   "ESP32-S3-N16R8", position=P(-12.7, -38.1))

# --- E22 UART LoRa + MAX485 ---
# E22 order: 1=M0 2=M1 3=RXD 4=TXD 5=AUX 6=VCC 7=GND
sch.components.add("Connector:Conn_01x07_Pin", "U3",
                   "E22-900T22D", position=P(-139.7, -12.7))
sch.components.add("Device:C_Polarized", "C4", "470uF/10V", position=P(-139.7, 5.08))
sch.components.add("Device:C", "C5", "100nF", position=P(-114.3, 5.08))
# MAX485E — represented as 8-pin header (symbol's multi-unit extends chain
# doesn't resolve in kicad-sch-api). Pin map: 1=RO 2=RE# 3=DE 4=DI 5=GND 6=A 7=B 8=VCC
sch.components.add("Connector:Conn_01x08_Pin", "U4", "MAX485E (RS485)", position=P(114.3, -25.4))

# --- SENSORS ---
sch.components.add("Connector:Conn_01x04_Pin", "J9", "BME280 (0x76)", position=P(-190.5, 25.4))
sch.components.add("Connector:Conn_01x04_Pin", "J10", "LTR390 (0x53)", position=P(-152.4, 25.4))
sch.components.add("Device:R", "R5", "4.7k", position=P(-190.5, 50.8))
sch.components.add("Device:R", "R6", "4.7k", position=P(-152.4, 50.8))
sch.components.add("Connector:Conn_01x03_Pin", "J11", "DS18B20", position=P(-114.3, 25.4))
sch.components.add("Device:R", "R7", "4.7k", position=P(-114.3, 50.8))
sch.components.add("Connector:Conn_01x02_Pin", "J12", "Rain Gauge", position=P(-63.5, 25.4))
sch.components.add("Connector:Conn_01x03_Pin", "J13", "Soil Moisture", position=P(-38.1, 25.4))
sch.components.add("Connector:Screw_Terminal_01x04", "J14", "Wind (A/B/GND/12V_SW)", position=P(50.8, 25.4))

# ══════════════════════════════════════════════════════════════════
# WIRE EVERYTHING
#
# Pin map (symbol pin numbers):
#   IRF4905: 1=D 2=G 3=S       2N7000: 1=S 2=G 3=D
#   AMS1117: 1=GND 2=VO 3=VI    Mini560: 1=Vin+ 2=Vin- 3=Vout+ 4=Vout-
#   D_Schottky: 1=K 2=A         C_Polarized: 1=+ 2=-
#   MAX485E: 1=RO 2=RE# 3=DE 4=DI 5=GND 6=A 7=B 8=VCC
#   Barrel_Jack: 1=center(+) 2=sleeve(-)
#   Connectors: pin N = Pin_N (sequential)
#   ESP32 U5 custom symbol: GND=1,2,22,44; 3V3 outputs=23,24; 5VIN=43
#     GPIO1=19 GPIO2=18 GPIO3=35 GPIO4=26 GPIO5=27 GPIO6=28 GPIO7=29
#     GPIO8=34 GPIO9=37 GPIO10=38 GPIO13=41 GPIO14=42 GPIO15=30
#     GPIO16=31 GPIO17=32 GPIO18=33
#   E22 U3 (1x7): 1=M0 2=M1 3=RXD 4=TXD 5=AUX 6=VCC 7=GND
# ══════════════════════════════════════════════════════════════════

failures = []
edges = []

def connect(r1, p1, r2, p2):
    """Record a logical connection; clean net labels are emitted after all nets are known."""
    n1 = (r1, str(p1))
    n2 = (r2, str(p2))
    if sch.get_component_pin_position(*n1) is None:
        failures.append((r1, p1, r2, p2))
        return None
    if sch.get_component_pin_position(*n2) is None:
        failures.append((r1, p1, r2, p2))
        return None
    edges.append((n1, n2))
    return True

def mark_nc(ref, pin):
    """Place a KiCad no-connect marker directly on an intentionally unused pin."""
    pos = sch.get_component_pin_position(ref, str(pin))
    if pos is None:
        failures.append((ref, pin, "NC", "missing pin"))
        return
    sch._no_connects.add((pos.x, pos.y))

# --- POWER INPUT CHAIN ---
connect("J1", 1, "F1", 1)          # center+ -> fuse
connect("F1", 2, "D1", 2)          # fuse -> diode anode
connect("D1", 1, "C1", 1)          # diode cathode -> cap + (12V_BUS)
connect("C1", 2, "J1", 2)          # cap - -> GND (J1 sleeve)
#   NOTE: J1.2 (sleeve) and C1.2 (-) and everything else on GND get wired below.

# --- Mini560 BUCK ---
connect("U1", 1, "D1", 1)          # Vin+ -> 12V_BUS
connect("U1", 2, "C1", 2)          # Vin- -> GND
connect("U1", 3, "U2", 3)          # Vout+ -> 5V_BUS (also AMS1117 VI)
connect("U1", 4, "C1", 2)          # Vout- -> GND

# --- AMS1117 LDO ---
connect("U2", 2, "C3", 1)          # VO -> 3.3V_BUS (cap +)
connect("C3", 2, "C1", 2)          # cap - -> GND
connect("C2", 1, "U2", 3)          # input cap + -> 5V_BUS (VI)
connect("C2", 2, "C1", 2)          # input cap - -> GND
connect("U2", 1, "C1", 2)          # GND -> GND
connect("#FLG01", 1, "U1", 3)      # Tell ERC the regulated 5V rail is driven
connect("#FLG02", 1, "C1", 2)      # Tell ERC the common GND rail is driven
connect("#FLG03", 1, "D1", 1)      # Tell ERC the protected +12V rail is driven

# --- MOSFET SWITCH ---
connect("Q1", 3, "D1", 1)          # S -> 12V_BUS
connect("Q1", 2, "R1", 2)          # G -> pull-up R1 (gate node)
connect("R1", 1, "D1", 1)          # R1 -> 12V_BUS
connect("Q2", 3, "Q1", 2)          # Q2 drain -> gate node
connect("Q2", 2, "R2", 2)          # Q2 gate -> R2
connect("R2", 1, "U5", 30)         # R2 -> GPIO15 (ESP32)
connect("Q2", 1, "C1", 2)          # Q2 source -> GND
connect("Q1", 1, "J2", 1)          # Q1 drain -> 12V_SW_OUT

# --- BATTERY DIVIDER ---
connect("R3", 1, "D1", 1)          # R3 -> 12V_BUS
connect("R3", 2, "R4", 1)          # divider node
connect("R4", 2, "C1", 2)          # R4 -> GND
connect("R3", 2, "J6", 1)          # BAT_ADC -> output terminal
connect("U5", 42, "R3", 2)         # GPIO14 -> BAT_ADC divider node

# --- OUTPUT TERMINALS (GND side) ---
connect("J2", 2, "C1", 2)          # 12V_SW GND
connect("J3", 1, "U1", 3)          # 5V_OUT -> 5V_BUS
connect("J3", 2, "C1", 2)          # 5V GND
connect("J4", 1, "U2", 2)          # 3.3V_OUT -> 3.3V_BUS
connect("J4", 2, "C1", 2)          # 3.3V GND
connect("J5", 1, "U5", 30)         # GPIO15 terminal
connect("J5", 2, "C1", 2)          # GND
connect("J6", 2, "C1", 2)          # BAT_ADC GND

# --- ESP32 POWER ---
# Feed only 5VIN. Do NOT parallel U5's onboard 3V3 regulator outputs (23/24)
# with the external AMS1117 rail used by the sensors and LoRa.
connect("U5", 43, "U1", 3)         # 5VIN -> 5V_BUS
connect("U5", 1, "C1", 2)          # GND
connect("U5", 2, "C1", 2)          # GND
connect("U5", 22, "C1", 2)         # GND
connect("U5", 44, "C1", 2)         # GND

# --- ESP32 -> E22-900T22D (UART LoRa) ---
connect("U5", 26, "U3", 1)         # GPIO4 -> M0
connect("U5", 27, "U3", 2)         # GPIO5 -> M1
connect("U5", 28, "U3", 3)         # GPIO6 (ESP TX) -> E22 RXD
connect("U5", 29, "U3", 4)         # GPIO7 (ESP RX) <- E22 TXD
connect("U5", 34, "U3", 5)         # GPIO8 <- AUX
connect("U3", 6, "U1", 3)          # E22 VCC -> +5V
connect("U3", 7, "C1", 2)          # E22 GND -> GND
connect("C4", 1, "U1", 3)          # E22 bulk capacitor -> +5V
connect("C4", 2, "C1", 2)          # E22 bulk capacitor -> GND
connect("C5", 1, "U1", 3)          # E22 decoupling capacitor -> +5V
connect("C5", 2, "C1", 2)          # E22 decoupling capacitor -> GND

# --- ESP32 -> MAX485 ---
connect("U5", 32, "U4", 4)         # GPIO17 TX -> DI
connect("U5", 33, "U4", 1)         # GPIO18 RX -> RO
connect("U5", 31, "U4", 2)         # GPIO16 -> RE#
connect("U5", 31, "U4", 3)         # GPIO16 -> DE (tied to RE#)
connect("U4", 5, "C1", 2)          # GND
connect("U4", 8, "U1", 3)          # VCC -> 5V
connect("U4", 6, "J14", 1)         # A -> wind A
connect("U4", 7, "J14", 2)         # B -> wind B

# --- I2C SENSORS (SDA/SCL net) ---
connect("U5", 19, "J9", 3)         # GPIO1 SDA -> BME280 SDA
connect("U5", 18, "J9", 4)         # GPIO2 SCL -> BME280 SCL
connect("J9", 3, "J10", 3)         # BME SDA -> LTR SDA
connect("J9", 4, "J10", 4)         # BME SCL -> LTR SCL
connect("J9", 1, "U2", 2)          # BME VCC -> 3.3V
connect("J9", 2, "C1", 2)          # BME GND
connect("J10", 1, "U2", 2)         # LTR VCC -> 3.3V
connect("J10", 2, "C1", 2)         # LTR GND
connect("R5", 1, "U2", 2)          # R5 pull-up -> 3.3V
connect("R5", 2, "J9", 3)          # R5 -> SDA
connect("R6", 1, "U2", 2)          # R6 pull-up -> 3.3V
connect("R6", 2, "J9", 4)          # R6 -> SCL

# --- OneWire (DS18B20) ---
connect("U5", 35, "J11", 2)        # GPIO3 -> DQ
connect("J11", 1, "U2", 2)         # VCC -> 3.3V
connect("J11", 3, "C1", 2)         # GND
connect("R7", 1, "U2", 2)          # R7 -> 3.3V
connect("R7", 2, "J11", 2)         # R7 -> DQ

# --- Rain Gauge ---
connect("U5", 38, "J12", 1)        # GPIO10 -> rain signal
connect("J12", 2, "C1", 2)         # GND

# --- Soil Moisture ---
connect("U5", 41, "J13", 2)        # GPIO13 -> AOUT
connect("J13", 1, "U2", 2)         # VCC -> 3.3V
connect("J13", 3, "C1", 2)         # GND

# --- Wind terminal power ---
connect("J14", 3, "C1", 2)         # GND
connect("J14", 4, "Q1", 1)         # 12V_SW

# --- INTENTIONALLY UNUSED / RESERVED PINS ---
# ESP32 custom-symbol pins intentionally unused in this weather node.
# Includes USB/UART/JTAG/spares, PSRAM-reserved GPIO35-37, RST, and the two
# onboard-regulator 3V3 outputs (23/24), which must not be paralleled with U2.
for pin in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
            20, 21, 23, 24, 25, 36, 37, 39, 40):
    mark_nc("U5", pin)

# Convert the recorded graph into named KiCad nets. Each pin gets the same local
# label as the other members of its connected component, avoiding spaghetti wires.
parent = {}

def find(node):
    parent.setdefault(node, node)
    if parent[node] != node:
        parent[node] = find(parent[node])
    return parent[node]

def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra

for a, b in edges:
    union(a, b)

groups = {}
for node in parent:
    groups.setdefault(find(node), set()).add(node)

anchor_names = {
    ("J1", "1"): "DC_IN_12V",
    ("F1", "2"): "FUSED_12V",
    ("C1", "2"): "GND",
    ("D1", "1"): "+12V",
    ("U1", "3"): "+5V",
    ("U2", "2"): "+3V3",
    ("Q1", "1"): "12V_SW",
    ("R3", "2"): "BAT_ADC",
    ("Q1", "2"): "MOSFET_GATE",
    ("Q2", "2"): "MOSFET_CTRL",
    ("U5", "30"): "GPIO15",
    ("U5", "26"): "E22_M0",
    ("U5", "27"): "E22_M1",
    ("U5", "28"): "E22_RXD",
    ("U5", "29"): "E22_TXD",
    ("U5", "31"): "RS485_DE_RE",
    ("U5", "32"): "RS485_TX",
    ("U5", "33"): "RS485_RX",
    ("U5", "34"): "E22_AUX",
    ("U5", "35"): "ONEWIRE",

    ("U5", "38"): "RAIN_SIG",
    ("U5", "41"): "SOIL_ADC",
    ("U5", "19"): "I2C_SDA",
    ("U5", "18"): "I2C_SCL",
    ("U4", "6"): "RS485_A",
    ("U4", "7"): "RS485_B",
}

power_nets = {"GND", "+3V3", "+5V", "+12V"}
power_ref = 1

def add_power_symbol(name, ref, pin):
    """Connect a pin to a KiCad power symbol using an outward-facing stub."""
    global power_ref
    component = sch.components.get(ref)
    pin_info = get_component_pin_info(component, pin) if component else None
    if pin_info is None:
        failures.append((ref, pin, "POWER", name))
        return
    pos, rotation = pin_info
    # Follow the pin outward so power stubs do not cross nearby signal stubs.
    if ref == "U4":
        side_stub = 30.48
    elif ref in {"J9", "J10", "J11", "J13"}:
        side_stub = 20.32
    else:
        side_stub = 10.16
    if rotation == 0:
        end = (pos.x - side_stub, pos.y)
    elif rotation == 180:
        end = (pos.x + side_stub, pos.y)
    elif rotation == 90:
        end = (pos.x, pos.y + 5.08)
    else:
        end = (pos.x, pos.y - 5.08)
    sch.add_wire((pos.x, pos.y), end)
    sch.components.add(
        f"power:{name}", f"#PWR{power_ref:02d}", name, position=end
    )
    power_ref += 1

def add_signal_label(name, ref, pin):
    """Move a local net label outward according to the pin's facing direction."""
    component = sch.components.get(ref)
    pin_info = get_component_pin_info(component, pin) if component else None
    if pin_info is None:
        failures.append((ref, pin, "LABEL", name))
        return
    pos, rotation = pin_info
    if rotation == 0:       # left-side pin, outward is left
        end = (pos.x - 10.16, pos.y)
        label_rotation = 180
    elif rotation == 180:   # right-side pin, outward is right
        end = (pos.x + 10.16, pos.y)
        label_rotation = 0
    elif rotation == 90:    # bottom pin, outward is down
        end = (pos.x, pos.y + 7.62)
        label_rotation = 270
    else:                   # top pin (270°), outward is up
        end = (pos.x, pos.y - 7.62)
        label_rotation = 90
    sch.add_wire((pos.x, pos.y), end)
    sch.add_label(name, position=end, rotation=label_rotation)

for index, nodes in enumerate(groups.values(), 1):
    name = next((anchor_names[n] for n in anchor_names if n in nodes), f"NET_{index:02d}")
    u5_ground_nodes = []
    for ref, pin in sorted(nodes):
        if name == "GND" and ref == "U5":
            u5_ground_nodes.append((ref, pin))
            continue
        if name in power_nets:
            add_power_symbol(name, ref, pin)
        else:
            add_signal_label(name, ref, pin)

    # U5 has four adjacent bottom GND pins. Join them to one small bus and one
    # GND symbol instead of drawing four overlapping GND symbols/text labels.
    if u5_ground_nodes:
        ground_points = sorted(
            [sch.get_component_pin_position(ref, pin) for ref, pin in u5_ground_nodes],
            key=lambda point: point.x,
        )
        bus_y = max(point.y for point in ground_points) + 5.08
        bus_points = []
        for point in ground_points:
            end = (point.x, bus_y)
            sch.add_wire((point.x, point.y), end)
            bus_points.append(end)
        for start, end in zip(bus_points, bus_points[1:]):
            sch.add_wire(start, end)
        symbol_pos = bus_points[len(bus_points) // 2]
        sch.components.add(
            "power:GND", f"#PWR{power_ref:02d}", "GND", position=symbol_pos
        )
        power_ref += 1

# ══════════════════════════════════════════════════════════════════
# SECTION HEADERS
# ══════════════════════════════════════════════════════════════════
sch.add_text("[ INPUT & PROTECTION ]", position=P(-190.5, -139.7))
sch.add_text("[ 5V BUCK + 3.3V LDO ]", position=P(-114.3, -139.7))
sch.add_text("[ MOSFET SWITCH + DIVIDER ]", position=P(-38.1, -139.7))
sch.add_text("[ OUTPUT ]", position=P(76.2, -139.7))
sch.add_text("[ ESP32-S3 N16R8 ]", position=P(-38.1, -50.8))
sch.add_text("[ E22 UART LoRa ]", position=P(-139.7, -38.1))
sch.add_text("[ RS485 ]", position=P(114.3, -38.1))
sch.add_text("[ SENSORS ]", position=P(-190.5, 12.7))

# ══════════════════════════════════════════════════════════════════
# NOTES
# ══════════════════════════════════════════════════════════════════
notes = [
    "NOTES:",
    "1. U1 Mini560 = custom symbol (weather-power:Mini560) - Vin+/Vin-/Vout+/Vout-.",
    "2. IRF4905 + 2N7000 MOSFET switch -> 12V_SW. GPIO15 HIGH = ON. R1=10k keeps OFF.",
    "3. Divider R3=390k + R4=100k -> BAT_ADC (GPIO14), ratio 4.90 (4S LiFePO4).",
    "4. I2C: BME280 (0x76) + LTR390 (0x53) share SDA(GPIO1)/SCL(GPIO2). R5/R6 = 4.7k.",
    "5. OneWire DS18B20 on GPIO3 (R7=4.7k). Rain=GPIO10, Soil=GPIO13.",
    "6. RS485 wind (shared A/B): MAX485E DI=GPIO17, RO=GPIO18, DE+RE=GPIO16.",
    "   Wind sensor power via 12V_SW (NOT through ESP32).",
    "7. E22-900T22D: M0=GPIO4 M1=GPIO5 RXD=GPIO6 TXD=GPIO7 AUX=GPIO8; VCC=5V; C4=470uF C5=100nF.",
    "8. U5 uses Jim's custom ESP32-S3-N16R8 44-pin symbol (two physical 1x22 headers).",
    "9. Final PCB: swap Mini560 -> LM2596-5.0.",
]
yn = 76.2
for n in notes:
    sch.add_text(n, position=P(-25.4, yn))
    yn += 5.08

OUTPUT = "/home/jimcan/dev/projects/weather-station/hardware/node-pcb/weather-node-complete.kicad_sch"
sch.save(OUTPUT)

# kicad-sch-api 0.5.6 serializes title-block dicts incorrectly.
# Repair only this known malformed block after saving.
with open(OUTPUT, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace(
    "\t(title_block\n"
    "\t\t(title {'title': 'Weather Station Node — Complete', 'date': '2026-08-20', "
    "'rev': 'v1.0 — fully wired (Mini560 + AMS1117)'})\n"
    "\t)",
    "\t(title_block\n"
    "\t\t(title \"Weather Station Node — Complete\")\n"
    "\t\t(date \"2026-08-20\")\n"
    "\t\t(rev \"v1.0 — fully wired (Mini560 + AMS1117)\")\n"
    "\t\t(company \"CTU Moalboal — Research\")\n"
    "\t)",
)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(content)

comps = list(sch.components.all())
nwires = len(list(sch.wires.all())) if hasattr(sch.wires, "all") else "?"
print(f"Generated: {OUTPUT}")
print(f"Components: {len(comps)}")
print(f"Wires: {nwires}")
print(f"Failed connections: {len(failures)}")
for f in failures:
    print(f"  FAIL: {f[0]}.{f[1]} -> {f[2]}.{f[3]}")
