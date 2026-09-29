#!/usr/bin/env python3
"""
Generate proper KiCad schematic (.kicad_sch) for weather station power supply.

Components: 19 (J1, D1, C1-C4, U1-U2, Q1-Q2, R1-R4, J2-J6)
Nets: 9 (12V_IN_RAW, 12V, GND, 5V, 3.3V, 12V_SW, GPIO_SIG, GATE, BAT_ADC)

Layout (left to right):
  INPUT SECTION:     J1 → D1 → C1
  BUCK SECTION:      U1 (MP1584) → C2
  LDO SECTION:       U2 (HT7333-A) + C3 + C4
  SWITCH SECTION:    Q1 (IRF9540) + Q2 (2N7000) + R1 + R2
  DIVIDER:           R3 + R4
  OUTPUTS:           J2 (12V_SW), J3 (5V), J4 (3.3V), J5 (GPIO15), J6 (BAT_ADC)
"""

import os, uuid

PROJECT_DIR = os.path.expanduser("~/dev/projects/weather-station/hardware/power-pcb")
PROJECT_NAME = "weather-power-pcb"

def U(): return str(uuid.uuid4())

# Symbol positions in schematic units (mils), 1 inch = 1000 mils
# Standard grid: 50 mils
G = 50  # grid spacing

def pos(x, y):
    """Convert grid units to mils for schematic placement."""
    return f"{x * G} {y * G}"

def at_xy(x, y, rot=0):
    """Return just the coordinate string for at."""
    return f"{pos(x,y)} {rot}"

def at_tag(x, y, rot=0):
    """Return full (at x y rot) tag."""
    return f"(at {pos(x,y)} {rot})"

# ── Build schematic ──────────────────────────────────────────────────
def generate():
    lines = []

    # Header
    lines.append(f'(kicad_sch (version 20231120) (generator "eeschema")')
    lines.append(f'  (uuid {U()})')
    lines.append(f'  (paper "A4")')

    # Title block
    lines.append(f'  (title_block')
    lines.append(f'    (title "Weather Station — Power Supply")')
    lines.append(f'    (date "2026-06-10")')
    lines.append(f'    (rev "v1.0")')
    lines.append(f'  )')

    # ── Custom library symbols ─────────────────────────────────────
    lines.append(f'  (lib_symbols')

    # MP1584 custom symbol (4-pin block: Vin+, Vin-, Vout+, Vout-)
    lines.append(f'    (symbol "weather-power:MP1584"')
    lines.append(f'      (in_bom yes) (on_board yes)')
    lines.append(f'      (property "Reference" "U" (at 0 -5.08 0))')
    lines.append(f'      (property "Value" "MP1584" (at 0 5.08 0))')
    lines.append(f'      (property "Footprint" "" (at 0 0 0))')
    lines.append(f'      (symbol "MP1584_0_1"')
    lines.append(f'        (rectangle (start -7.62 -7.62) (end 7.62 7.62))')
    for i, (name, x, y, rot) in enumerate([
        ("Vin+", -7.62, 3.81, 180), ("Vin-", -7.62, -3.81, 180),
        ("Vout+", 7.62, 3.81, 0), ("Vout-", 7.62, -3.81, 0),
    ]):
        lines.append(f'        (pin passive line (at {x} {y} {rot}) (length 2.54)')
        lines.append(f'          (name "{name}" (effects (font (size 1.27 1.27))))')
        lines.append(f'          (number "{i+1}" (effects (font (size 1.27 1.27)))))')
    lines.append(f'      )')
    lines.append(f'    )')

    # HT7333-A custom symbol (3-pin: Vout, GND, Vin)
    lines.append(f'    (symbol "weather-power:HT7333A"')
    lines.append(f'      (in_bom yes) (on_board yes)')
    lines.append(f'      (property "Reference" "U" (at 0 -5.08 0))')
    lines.append(f'      (property "Value" "HT7333-A" (at 0 5.08 0))')
    lines.append(f'      (property "Footprint" "" (at 0 0 0))')
    lines.append(f'      (symbol "HT7333A_0_1"')
    lines.append(f'        (rectangle (start -5.08 -5.08) (end 5.08 5.08))')
    for i, (name, x, y, rot) in enumerate([
        ("Vout", -5.08, 2.54, 180), ("GND", 0, -5.08, 270),
        ("Vin", 5.08, 2.54, 0),
    ]):
        lines.append(f'        (pin passive line (at {x} {y} {rot}) (length 2.54)')
        lines.append(f'          (name "{name}" (effects (font (size 1.27 1.27))))')
        lines.append(f'          (number "{i+1}" (effects (font (size 1.27 1.27)))))')
    lines.append(f'      )')
    lines.append(f'    )')

    lines.append(f'  )')

    # ── Placed symbols (direct children of kicad_sch, NOT inside symbol_instances!) ─
    # symbol_instances stays empty
    lines.append(f'  (symbol_instances)')

    # --- INPUT SECTION (left column, x=2-6) ---
    # J1 - Barrel Jack (x=2, y=18)
    _add_symbol(lines, "Connector:Barrel_Jack_Switch", "J1", 2, 18, 0)
    # D1 - Schottky diode (x=4, y=18)
    _add_symbol(lines, "Device:D_Schottky", "D1", 4, 18, 0)
    # C1 - 100uF/25V (x=6, y=18)
    _add_symbol(lines, "Device:C_Polarized", "C1", 6, 18, 0)

    # --- BUCK SECTION (center-left, x=8-12) ---
    # U1 - MP1584 (x=10, y=16)
    _add_symbol(lines, "weather-power:MP1584", "U1", 10, 16, 0)
    # C2 - 100uF/16V (x=12, y=16)
    _add_symbol(lines, "Device:C_Polarized", "C2", 12, 16, 0)

    # --- LDO SECTION (center, x=14-18) ---
    # U2 - HT7333-A (x=16, y=16)
    _add_symbol(lines, "weather-power:HT7333A", "U2", 16, 16, 0)
    # C3 - 10uF (x=14, y=12)
    _add_symbol(lines, "Device:C_Polarized", "C3", 14, 12, 0)
    # C4 - 10uF (x=18, y=12)
    _add_symbol(lines, "Device:C_Polarized", "C4", 18, 12, 0)

    # --- SWITCH SECTION (right, x=20-26) ---
    # Q1 - P-ch MOSFET (x=22, y=16)
    _add_symbol(lines, "Device:Q_PMOS_GSD", "Q1", 22, 18, 0)
    # Q2 - N-ch MOSFET (x=22, y=10)
    _add_symbol(lines, "Device:Q_NMOS_GSD", "Q2", 22, 10, 0)
    # R1 - 10k (x=24, y=18)
    _add_symbol(lines, "Device:R", "R1", 24, 18, 90)
    # R2 - 1k (x=24, y=10)
    _add_symbol(lines, "Device:R", "R2", 24, 10, 90)

    # --- DIVIDER (x=26-28, y=6) ---
    # R3 - 330k (x=26, y=6)
    _add_symbol(lines, "Device:R", "R3", 26, 6, 0)
    # R4 - 100k (x=28, y=6)
    _add_symbol(lines, "Device:R", "R4", 28, 6, 0)

    # --- OUTPUT TERMINALS (rightmost, x=28-30) ---
    # J2 - 12V_SW (x=30, y=18)
    _add_symbol(lines, "Connector:Screw_Terminal_01x02", "J2", 30, 18, 0)
    # J3 - 5V_OUT (x=30, y=14)
    _add_symbol(lines, "Connector:Screw_Terminal_01x02", "J3", 30, 14, 0)
    # J4 - 3.3V_OUT (x=30, y=10)
    _add_symbol(lines, "Connector:Screw_Terminal_01x02", "J4", 30, 10, 0)
    # J5 - GPIO15 (x=26, y=12)
    _add_symbol(lines, "Connector:Conn_01x02_Pin", "J5", 26, 12, 0)
    # J6 - BAT_ADC (x=30, y=6)
    _add_symbol(lines, "Connector:Conn_01x02_Pin", "J6", 30, 6, 0)

    # --- POWER PORTS ---
    _add_power_port(lines, "+12V", 2, 20, 0)     # 12V input rail label
    _add_power_port(lines, "+5V", 12, 20, 0)      # 5V rail label
    _add_power_port(lines, "+3.3V", 18, 20, 0)    # 3.3V rail label

    # --- GROUND SYMBOLS ---
    _add_ground(lines, 2, 16)
    _add_ground(lines, 6, 16)
    _add_ground(lines, 12, 14)
    _add_ground(lines, 14, 10)
    _add_ground(lines, 18, 10)
    _add_ground(lines, 22, 8)
    _add_ground(lines, 26, 4)
    _add_ground(lines, 28, 4)

    # Output terminal ground references
    _add_ground(lines, 30, 16)  # J2 GND
    _add_ground(lines, 30, 12)  # J3 GND
    _add_ground(lines, 30, 8)   # J4 GND

    # ── Wires (direct children) ────────────────────────────────────

    # 12V Input path: J1(center) → D1(anode)
    _wire(lines, 2, 18.5, 3, 18.5)  # J1 pin1 to D1 anode
    # D1(cathode) → C1(+) → U1(Vin+) — 12V bus
    _wire(lines, 5, 18.5, 6, 18.5)  # D1 cathode to C1+
    _wire(lines, 6.5, 18.5, 9, 18.5)  # to 12V bus → U1 Vin+
    _wire(lines, 9, 18.5, 9, 16.5)    # down to U1 Vin+
    # 12V bus to R1(12V pull-up) and Q1(Source)
    _wire(lines, 6.5, 18.5, 6.5, 20)  # 12V bus up
    _wire(lines, 6.5, 20, 23, 20)     # across to switch section
    _wire(lines, 23, 20, 23, 18.5)    # down to Q1 Source
    _wire(lines, 23, 20, 23.5, 20)     # to R1 pull-up
    _wire(lines, 23.5, 20, 23.5, 18.5) # down to R1

    # U1(Vout+) → C2(+) → U2(Vin) → J3(5V_OUT)
    _wire(lines, 11, 16.5, 11.5, 16.5)  # U1 Vout+
    _wire(lines, 11.5, 16.5, 12, 16.5)  # to C2+
    _wire(lines, 12.5, 16.5, 14.5, 16.5) # to 5V bus
    _wire(lines, 14.5, 16.5, 14.5, 16)   # down to U2 Vin
    _wire(lines, 12.5, 16.5, 12.5, 20)   # 5V bus up to power port
    _wire(lines, 12.5, 16.5, 29, 16.5)   # 5V bus to J3
    _wire(lines, 29, 16.5, 29, 14.5)     # down to J3
    # C3 across 5V rail to GND
    _wire(lines, 13.5, 16.5, 13.5, 14)   # C3 top
    _wire(lines, 13.5, 13.5, 13.5, 12.5) # C3+

    # U2(Vout) → C4(+) → J4(3.3V_OUT) — 3.3V bus
    _wire(lines, 17, 16, 17, 17)          # U2 Vout up
    _wire(lines, 17, 17, 17.5, 17)        # to 3.3V bus
    _wire(lines, 17.5, 17, 17.5, 20)      # 3.3V bus up to power port
    _wire(lines, 17.5, 17, 29.5, 17)      # 3.3V bus to J4
    _wire(lines, 29.5, 17, 29.5, 12.5)    # down to C4+ 
    _wire(lines, 29.5, 12.5, 29.5, 10.5)  # to J4

    # MOSFET switch circuit
    # Q1 Gate ← 10k → 12V (pull-up via R1)
    _wire(lines, 22, 18, 23, 18)           # Q1 Gate to junction
    # R1 (10k) is vertical at x=24 between y=17.5 (top) and y=18.5 (bottom)
    _wire(lines, 23, 18, 23.5, 18)         # to R1
    # Q1 Gate → Q2 Drain (GATE net)
    _wire(lines, 22, 18, 22, 12)           # Q1 Gate down to Q2 Drain
    # Q2 Gate via R2 from GPIO15
    _wire(lines, 22, 10.5, 22, 10.5)       # Q2 Gate
    _wire(lines, 23, 10.5, 23.5, 10.5)     # to R2
    # R2 to GPIO15 header
    _wire(lines, 23.5, 10, 23.5, 10.5)     # R2 bottom
    # Q1 Drain → J2(12V_SW)
    _wire(lines, 22, 18.5, 29, 18.5)       # Q1 Drain to J2
    _wire(lines, 29, 18.5, 29, 18.5)       # to J2 pin1

    # Battery divider: 12V → R3 → R4 → GND, junction to J6
    _wire(lines, 6.5, 18.5, 6.5, 22)       # 12V down
    _wire(lines, 6.5, 22, 25, 22)          # across to divider section
    _wire(lines, 25, 22, 25, 6.5)          # down to R3 top
    _wire(lines, 25, 6.5, 26, 6.5)         # R3 top
    _wire(lines, 28, 6.5, 29, 6.5)         # R4 bottom → J6
    _wire(lines, 29, 6.5, 29, 6.5)         # to J6 pin1

    # GPIO15 signal to J5
    _wire(lines, 25.5, 12.5, 26, 12.5)     # to J5 pin1

    # GND connections
    _wire(lines, 2, 17, 2, 16)              # J1 GND to GND symbol
    _wire(lines, 6, 17, 6, 16)              # C1 GND to GND
    _wire(lines, 10, 14, 10, 14)            # U1 Vin- 
    _wire(lines, 10, 12, 12, 12)            # U1 Vout-
    _wire(lines, 12, 12, 14, 12)            # to C3 GND side
    _wire(lines, 12, 12, 18, 12)            # to C4 GND
    _wire(lines, 16, 14, 16, 14)            # U2 GND
    _wire(lines, 22, 9, 22, 8)              # Q2 Source to GND
    _wire(lines, 26, 5, 26, 4)              # R3-R4 junction to GND (via R4)
    _wire(lines, 28, 5, 28, 4)              # R4 bottom to GND
    # Output terminals GND
    _wire(lines, 30, 17, 30, 16)            # J2 GND
    _wire(lines, 30, 13, 30, 12)            # J3 GND
    _wire(lines, 30, 9, 30, 8)              # J4 GND
    _wire(lines, 26, 11, 26, 11)            # J5 GND (handled via GND symbol)

    # ── Net labels (direct children) ───────────────────────────────
    _label(lines, "12V_IN", 2.5, 19)
    _label(lines, "12V_BUS", 7, 19.5)
    _label(lines, "5V", 12, 20.5)
    _label(lines, "3.3V", 18, 20.5)
    _label(lines, "12V_SW", 28, 19)
    _label(lines, "GATE", 22.5, 15)
    _label(lines, "GPIO15", 25, 13)
    _label(lines, "BAT_ADC", 29, 7)

    # Footer
    lines.append(f')')

    sch_path = os.path.join(PROJECT_DIR, f"{PROJECT_NAME}.kicad_sch")
    with open(sch_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return sch_path


def _add_symbol(lines, lib_id, ref, gx, gy, rot):
    """Add a symbol instance as direct child of kicad_sch."""
    lines.append(f'  (symbol (lib_id "{lib_id}") (at {at_xy(gx, gy, rot)})')
    lines.append(f'    (uuid {U()})')
    lines.append(f'    (property "Reference" "{ref}" {at_tag(0, -2)})')
    lines.append(f'    (property "Value" "" {at_tag(0, 2)})')
    lines.append(f'    (property "Footprint" "" {at_tag(0, 0)})')
    lines.append(f'    (property "Datasheet" "" {at_tag(0, 0)})')
    lines.append(f'    (pin "1" (uuid {U()}))')
    lines.append(f'    (pin "2" (uuid {U()}))')
    lines.append(f'  )')


def _add_power_port(lines, name, gx, gy, rot):
    """Add a power port symbol as direct child."""
    lines.append(f'  (symbol (lib_id "power:{name}") (at {at_xy(gx, gy, rot)})')
    lines.append(f'    (uuid {U()})')
    lines.append(f'    (property "Reference" "#PWR" {at_tag(0, -2)})')
    lines.append(f'    (property "Value" "{name}" {at_tag(0, 2)})')
    lines.append(f'    (property "Footprint" "" {at_tag(0, 0)})')
    lines.append(f'    (property "Datasheet" "" {at_tag(0, 0)})')
    lines.append(f'    (pin "1" (uuid {U()}))')
    lines.append(f'  )')


def _add_ground(lines, gx, gy):
    """Add a GND symbol as direct child."""
    lines.append(f'  (symbol (lib_id "power:GND") (at {at_xy(gx, gy, 0)})')
    lines.append(f'    (uuid {U()})')
    lines.append(f'    (property "Reference" "#PWR" {at_tag(0, -2)})')
    lines.append(f'    (property "Value" "GND" {at_tag(0, 2)})')
    lines.append(f'    (property "Footprint" "" {at_tag(0, 0)})')
    lines.append(f'    (property "Datasheet" "" {at_tag(0, 0)})')
    lines.append(f'    (pin "1" (uuid {U()}))')
    lines.append(f'  )')


def _label(lines, text, gx, gy):
    """Add a net label as direct child."""
    lines.append(f'  (text "{text}" {at_tag(gx, gy, 0)} '
                 f'(effects (font (size 1.27 1.27))) (uuid {U()}))')

def _wire(lines, x1, y1, x2, y2):
    """Add a wire segment as direct child."""
    lines.append(f'  (wire (pts (xy {pos(x1,y1)}) (xy {pos(x2,y2)})) '
                 f'(stroke (width 0) (type default)) (uuid {U()}))')


if __name__ == "__main__":
    os.makedirs(PROJECT_DIR, exist_ok=True)
    sch = generate()
    print(f"Schematic: {sch}")
    print(f"Open with: kicad {sch}")
