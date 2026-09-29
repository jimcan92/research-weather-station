#!/usr/bin/env python3
"""
Weather Station — Power Supply PCB
Pure S-expression generator for KiCad 9/10 format. No pcbnew import needed.

Board: 60×50mm, 2-layer, THT components
Coordinates in mm, UUIDs for identification.
"""

import os, uuid

PROJECT_DIR = os.path.expanduser("~/dev/projects/weather-station/hardware/power-pcb")
PROJECT_NAME = "weather-power-pcb"
BW, BH = 60.0, 50.0

def U(): return str(uuid.uuid4())

def indent(n, s): return "\t" * n + s

# ── Components ──────────────────────────────────────────────────────
# (ref, value, [(pad_num, x, y, drill, shape), ...], x, y, rot)
# shape: 0=circle, 1=rect

COMPS = [
    ("J1", "Barrel_Jack",
        [("1", -8.00, 0, 1.20, 1), ("2", 0.00, 0, 1.20, 0), ("3", 3.50, 0, 1.20, 0)],
        [(-12,-6,12,-6),(12,-6,12,6),(12,6,-12,6),(-12,6,-12,-6)],
        5, 7, 0),
    ("D1", "1N5819",
        [("1", -2.54, 0, 0.90, 0), ("2", 2.54, 0, 0.90, 0)],
        [(-4,-2.5,4,-2.5),(4,-2.5,4,2.5),(4,2.5,-4,2.5),(-4,2.5,-4,-2.5)],
        23, 5, 0),
    ("C1", "100uF/25V",
        [("1", -1.75, 0, 0.80, 0), ("2", 1.75, 0, 0.80, 0)],
        [(-5,-5,5,-5),(5,-5,5,5),(5,5,-5,5),(-5,5,-5,-5)],
        34, 5, 0),
    ("U1", "MP1584",
        [("1", -5.08, -5.00, 1.00, 1), ("2", -5.08, 5.00, 1.00, 0),
         ("3", 5.08, 5.00, 1.00, 0), ("4", 5.08, -5.00, 1.00, 0)],
        [(-11,-6,11,-6),(11,-6,11,6),(11,6,-11,6),(-11,6,-11,-6)],
        46, 10, 0),
    ("C2", "100uF/16V",
        [("1", -1.25, 0, 0.70, 0), ("2", 1.25, 0, 0.70, 0)],
        [(-4,-4,4,-4),(4,-4,4,4),(4,4,-4,4),(-4,4,-4,-4)],
        56, 7, 0),
    ("U2", "HT7333-A",
        [("1", 0.00, 0, 0.80, 1), ("2", 2.54, 0, 0.80, 0), ("3", 5.08, 0, 0.80, 0)],
        [(-2,-3,7,-3),(7,-3,7,3),(7,3,-2,3),(-2,3,-2,-3)],
        5, 21, 0),
    ("C3", "10uF/16V",
        [("1", -1.00, 0, 0.60, 0), ("2", 1.00, 0, 0.60, 0)],
        [(-3,-3,3,-3),(3,-3,3,3),(3,3,-3,3),(-3,3,-3,-3)],
        17, 20, 0),
    ("C4", "10uF/16V",
        [("1", -1.00, 0, 0.60, 0), ("2", 1.00, 0, 0.60, 0)],
        [(-3,-3,3,-3),(3,-3,3,3),(3,3,-3,3),(-3,3,-3,-3)],
        25, 20, 0),
    ("Q1", "IRF9540",
        [("1", 0.00, 0, 1.00, 1), ("2", 2.54, 0, 1.00, 0), ("3", 5.08, 0, 1.00, 0)],
        [(-3,-5,8,-5),(8,-5,8,5),(8,5,-3,5),(-3,5,-3,-5)],
        36, 23, 0),
    ("Q2", "2N7000",
        [("1", 0.00, 0, 0.80, 1), ("2", 2.54, 0, 0.80, 0), ("3", 5.08, 0, 0.80, 0)],
        [(-2,-3,7,-3),(7,-3,7,3),(7,3,-2,3),(-2,3,-2,-3)],
        36, 35, 0),
    ("R1", "10k",
        [("1", -2.54, 0, 0.70, 0), ("2", 2.54, 0, 0.70, 0)],
        [(-4,-2,4,-2),(4,-2,4,2),(4,2,-4,2),(-4,2,-4,-2)],
        50, 24, 0),
    ("R2", "1k",
        [("1", -2.54, 0, 0.70, 0), ("2", 2.54, 0, 0.70, 0)],
        [(-4,-2,4,-2),(4,-2,4,2),(4,2,-4,2),(-4,2,-4,-2)],
        50, 33, 0),
    ("R3", "330k",
        [("1", -2.54, 0, 0.70, 0), ("2", 2.54, 0, 0.70, 0)],
        [(-4,-2,4,-2),(4,-2,4,2),(4,2,-4,2),(-4,2,-4,-2)],
        5, 38, 0),
    ("R4", "100k",
        [("1", -2.54, 0, 0.70, 0), ("2", 2.54, 0, 0.70, 0)],
        [(-4,-2,4,-2),(4,-2,4,2),(4,2,-4,2),(-4,2,-4,-2)],
        5, 44, 0),
    ("J2", "12V_SW",
        [("1", 0.00, 0, 1.10, 1), ("2", 5.00, 0, 1.10, 0)],
        [(-2,-4,7,-4),(7,-4,7,4),(7,4,-2,4),(-2,4,-2,-4)],
        53, 27, 0),
    ("J3", "5V_OUT",
        [("1", 0.00, 0, 1.10, 1), ("2", 5.00, 0, 1.10, 0)],
        [(-2,-4,7,-4),(7,-4,7,4),(7,4,-2,4),(-2,4,-2,-4)],
        53, 34, 0),
    ("J4", "3.3V_OUT",
        [("1", 0.00, 0, 1.10, 1), ("2", 5.00, 0, 1.10, 0)],
        [(-2,-4,7,-4),(7,-4,7,4),(7,4,-2,4),(-2,4,-2,-4)],
        53, 41, 0),
    ("J5", "GPIO15",
        [("1", 0.00, 0, 0.90, 1), ("2", 2.54, 0, 0.90, 0)],
        [(-2,-3,4.5,-3),(4.5,-3,4.5,3),(4.5,3,-2,3),(-2,3,-2,-3)],
        18, 44, 0),
    ("J6", "BAT_ADC",
        [("1", 0.00, 0, 0.90, 1), ("2", 2.54, 0, 0.90, 0)],
        [(-2,-3,4.5,-3),(4.5,-3,4.5,3),(4.5,3,-2,3),(-2,3,-2,-3)],
        30, 44, 0),
]

# ── Nets ────────────────────────────────────────────────────────────
# net_code, net_name, [(ref, pin), ...]
NETS = [
    (1, "GND", [
        ("J1","2"),("J1","3"),("C1","2"),("U1","2"),("U1","4"),
        ("C2","2"),("U2","2"),("C3","2"),("C4","2"),
        ("Q2","2"),("R2","2"),("R4","2"),
        ("J2","2"),("J3","2"),("J4","2"),("J5","2"),("J6","2"),
    ]),
    (2, "12V_IN_RAW", [("J1","1"),("D1","2")]),
    (3, "12V", [("D1","1"),("C1","1"),("U1","1"),("Q1","3"),("R1","2"),("R3","2")]),
    (4, "5V", [("U1","3"),("C2","1"),("U2","3"),("C3","1"),("J3","1")]),
    (5, "3.3V", [("U2","1"),("C4","1"),("J4","1")]),
    (6, "12V_SW", [("Q1","2"),("J2","1")]),
    (7, "GPIO_SIG", [("J5","1"),("R2","1"),("Q2","1")]),
    (8, "GATE", [("Q1","1"),("R1","1"),("Q2","3")]),
    (9, "BAT_ADC", [("R3","1"),("R4","1"),("J6","1")]),
]

# ── Track widths per net ────────────────────────────────────────────
TRACK_WIDTHS = {
    "GND": 0.8, "12V_IN_RAW": 0.8, "12V": 0.8, "5V": 0.8,
    "3.3V": 0.8, "12V_SW": 0.8, "GPIO_SIG": 0.4, "GATE": 0.4,
    "BAT_ADC": 0.4,
}


def fmt(n):
    """Format a number: integer if whole, 2 decimals otherwise."""
    if isinstance(n, float) and n == int(n):
        return str(int(n))
    return f"{n:.2f}"


def fmtp(x, y):
    return f"{fmt(x)} {fmt(y)}"


def pad_pos(ref, pnum):
    """Get absolute pad position (x, y) for a given refdes and pad number."""
    for r, _v, pads, _s, px, py, _rot in COMPS:
        if r == ref:
            for pn, rx, ry, *_ in pads:
                if str(pn) == str(pnum):
                    return (px + rx, py + ry)
    raise ValueError(f"Pad {pnum} on {ref} not found")


def route_net(net_name, nodes, lines, width):
    """Generate L-shaped track segments for a net (star from first pad)."""
    positions = []
    for ref, pnum in nodes:
        try:
            positions.append(pad_pos(ref, pnum))
        except ValueError:
            pass

    if len(positions) < 2:
        return 0

    count = 0
    x0, y0 = positions[0]
    for xN, yN in positions[1:]:
        # Two segments: (x0,y0)→(xN,y0) then (xN,y0)→(xN,yN)
        for (sx, sy), (ex, ey) in [((x0,y0), (xN,y0)), ((xN,y0), (xN,yN))]:
            lines.append(indent(2, f'(segment (start {fmtp(sx,sy)}) (end {fmtp(ex,ey)}) '
                f'(width {fmt(width)}) (layer "F.Cu") (net {NET_CODE[net_name]}) '
                f'(uuid "{U()}"))'))
            count += 1
    return count


def generate():
    os.makedirs(PROJECT_DIR, exist_ok=True)

    pcb_path = os.path.join(PROJECT_DIR, f"{PROJECT_NAME}.kicad_pcb")
    lines = []

    # ── Header ───────────────────────────────────────────────────────
    lines.append("(kicad_pcb")
    lines.append(indent(1, '(version 20241229)'))
    lines.append(indent(1, '(generator "pcbnew")'))
    lines.append(indent(1, '(generator_version "9.0")'))

    lines.append(indent(1, "(general"))
    lines.append(indent(2, "(thickness 1.6)"))
    lines.append(indent(2, "(legacy_teardrops no)"))
    lines.append(indent(1, ")"))

    lines.append(indent(1, '(paper "A4")'))

    # ── Layers ───────────────────────────────────────────────────────
    lines.append(indent(1, "(layers"))
    layers = [
        (0, "F.Cu", "signal"), (2, "B.Cu", "signal"),
        (9, "F.Adhes", 'user "F.Adhesive"'), (11, "B.Adhes", 'user "B.Adhesive"'),
        (13, "F.Paste", "user"), (15, "B.Paste", "user"),
        (5, "F.SilkS", 'user "F.Silkscreen"'), (7, "B.SilkS", 'user "B.Silkscreen"'),
        (1, "F.Mask", "user"), (3, "B.Mask", "user"),
        (17, "Dwgs.User", 'user "User.Drawings"'), (19, "Cmts.User", 'user "User.Comments"'),
        (21, "Eco1.User", 'user "User.Eco1"'), (23, "Eco2.User", 'user "User.Eco2"'),
        (25, "Edge.Cuts", "user"), (27, "Margin", "user"),
        (31, "F.CrtYd", 'user "F.Courtyard"'), (29, "B.CrtYd", 'user "B.Courtyard"'),
        (35, "F.Fab", "user"), (33, "B.Fab", "user"),
    ]
    for lid, lname, ltype in layers:
        lines.append(indent(2, f'({lid} "{lname}" {ltype})'))
    lines.append(indent(1, ")"))

    # ── Setup ────────────────────────────────────────────────────────
    lines.append(indent(1, "(setup"))
    lines.append(indent(2, "(pad_to_mask_clearance 0)"))
    lines.append(indent(2, "(allow_soldermask_bridges_in_footprints no)"))
    lines.append(indent(1, ")"))

    # ── Nets ─────────────────────────────────────────────────────────
    lines.append(indent(1, '(net 0 "")'))
    for code, name, _nodes in NETS:
        lines.append(indent(1, f'(net {code} "{name}")'))

    # ── Board outline ────────────────────────────────────────────────
    outline = [(0,0), (BW,0), (BW,BH), (0,BH)]
    for i in range(4):
        x1, y1 = outline[i]
        x2, y2 = outline[(i+1)%4]
        lines.append(indent(1, f"(gr_line"))
        lines.append(indent(2, f"(start {fmtp(x1,y1)})"))
        lines.append(indent(2, f"(end {fmtp(x2,y2)})"))
        lines.append(indent(2, "(stroke"))
        lines.append(indent(3, "(width 0.15)"))
        lines.append(indent(3, "(type default)"))
        lines.append(indent(2, ")"))
        lines.append(indent(2, f'(layer "Edge.Cuts")'))
        lines.append(indent(2, f'(uuid "{U()}")'))
        lines.append(indent(1, ")"))

    # ── Footprints ───────────────────────────────────────────────────
    for ref, value, pads, silk, px, py, rot in COMPS:
        pad_size_offset = 0.7  # annular ring mm on each side

        lines.append(indent(1, f"(footprint \"\""))
        lines.append(indent(2, f'(at {fmtp(px, py)} {rot})'))
        lines.append(indent(2, '(layer "F.Cu")'))
        lines.append(indent(2, f'(uuid "{U()}")'))

        # Reference property
        lines.append(indent(2, f'(property "Reference" "{ref}" '
            f'(at 0 -3 0) (layer "F.SilkS") (uuid "{U()}"))'))
        # Value property
        lines.append(indent(2, f'(property "Value" "{value}" '
            f'(at 0 3 0) (layer "F.Fab") (uuid "{U()}"))'))
        # Footprint property
        lines.append(indent(2, f'(property "Footprint" "" '
            f'(at 0 0 0) (layer "F.Fab") (uuid "{U()}"))'))
        # Datasheet property
        lines.append(indent(2, f'(property "Datasheet" "" '
            f'(at 0 0 0) (layer "F.Fab") (uuid "{U()}"))'))
        # Hide extra properties
        lines.append(indent(2, f'(property "Description" "" '
            f'(at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}"))'))

        # Pads
        for pnum, rx, ry, drill, shape in pads:
            shape_s = "rect" if shape else "circle"
            psize = drill + pad_size_offset
            lines.append(indent(2, f'(pad "{pnum}" thru_hole {shape_s} '
                f'(at {fmtp(rx, ry)}) (size {fmt(psize)} {fmt(psize)}) '
                f'(drill {fmt(drill)}) (layers "*.Cu" "*.Mask") '
                f'(uuid "{U()}"))'))

        # Silkscreen lines
        for x1, y1, x2, y2 in silk:
            fp_line_str = (
                "(fp_line "
                f"(start {fmtp(x1, y1)}) (end {fmtp(x2, y2)}) "
                "(stroke (width 0.12) (type default)) "
                f'(layer "F.SilkS") (uuid "{U()}"))'
            )
            lines.append(indent(2, fp_line_str))

        # Courtyard (clearance box, 0.25mm bigger than silkscreen)
        min_x = min(x1 for x1,_,_x2,_ in silk) - 0.25
        min_y = min(y1 for _,y1,_,y2 in silk) - 0.25
        max_x = max(x2 for _,_,x2,_ in silk) + 0.25
        max_y = max(y2 for _,_,_,y2 in silk) + 0.25
        for (cx1, cy1, cx2, cy2) in [
            (min_x, min_y, max_x, min_y), (max_x, min_y, max_x, max_y),
            (max_x, max_y, min_x, max_y), (min_x, max_y, min_x, min_y),
        ]:
            courtyard_str = (
                "(fp_line "
                f"(start {fmtp(cx1, cy1)}) (end {fmtp(cx2, cy2)}) "
                "(stroke (width 0.05) (type default)) "
                f'(layer "F.CrtYd") (uuid "{U()}"))'
            )
            lines.append(indent(2, courtyard_str))

        lines.append(indent(1, ")"))

    # ── Tracks (routing) ─────────────────────────────────────────────
    total_tracks = 0
    for code, name, nodes in NETS:
        width = TRACK_WIDTHS.get(name, 0.4)
        total_tracks += route_net(name, nodes, lines, width)
    print(f"  Tracks: {total_tracks}")

    # ── Copper zones (GND pour) ──────────────────────────────────────
    for layer_name in ["F.Cu", "B.Cu"]:
        lines.append(indent(1, "(zone"))
        lines.append(indent(2, '(net 1)'))
        lines.append(indent(2, f'(net_name "GND")'))
        lines.append(indent(2, f'(layer "{layer_name}")'))
        lines.append(indent(2, f'(uuid "{U()}")'))
        lines.append(indent(2, "(name empty)"))
        lines.append(indent(2, "(hatch edge 0.500)"))
        lines.append(indent(2, "(priority 0)"))
        lines.append(indent(2, "(connect_pads yes (clearance 0.300))"))
        lines.append(indent(2, "(min_thickness 0.250)"))
        lines.append(indent(2, "(fill yes (thermal_gap 0.500) (thermal_bridge_width 0.500))"))
        lines.append(indent(2, "(polygon"))
        lines.append(indent(3, "(pts"))
        mid_margin = 0.5
        lines.append(indent(4, f'(xy {fmtp(mid_margin, mid_margin)})'))
        lines.append(indent(4, f'(xy {fmtp(BW - mid_margin, mid_margin)})'))
        lines.append(indent(4, f'(xy {fmtp(BW - mid_margin, BH - mid_margin)})'))
        lines.append(indent(4, f'(xy {fmtp(mid_margin, BH - mid_margin)})'))
        lines.append(indent(3, ")"))
        lines.append(indent(2, ")"))
        lines.append(indent(1, ")"))

    # ── Mounting holes (M3) ──────────────────────────────────────────
    for mx, my in [(3,3), (BW-3,3), (BW-3,BH-3), (3,BH-3)]:
        lines.append(indent(1, "(footprint \"\""))
        lines.append(indent(2, f'(at {fmtp(mx, my)} 0)'))
        lines.append(indent(2, '(layer "F.Cu")'))
        lines.append(indent(2, f'(uuid "{U()}")'))
        lines.append(indent(2, f'(property "Reference" "MH*" '
            f'(at 0 3 0) (layer "F.SilkS") (uuid "{U()}"))'))
        lines.append(indent(2, f'(property "Value" "M3" '
            f'(at 0 -3 0) (layer "F.Fab") (uuid "{U()}"))'))
        lines.append(indent(2, f'(pad "" np_thru_hole circle '
            f'(at 0 0) (size 3.2 3.2) (drill 3.2) '
            f'(layers "*.Cu" "*.Mask") (uuid "{U()}"))'))
        lines.append(indent(1, ")"))

    # ── Silkscreen text labels ────────────────────────────────────────
    labels = [
        ("Weather Station Power v1.0", 30, 48.5, 0.8),
        ("12V IN -> 5V/3.3V OUT", 30, 47.2, 0.7),
        ("12V IN", 5, 2.5, 0.8),
        ("12V_SW", 50, 25, 0.7),
        ("5V", 50, 32.4, 0.7),
        ("3.3V", 50, 39.4, 0.7),
        ("GPIO15", 10, 42.5, 0.7),
        ("BAT_ADC", 22, 42.5, 0.7),
    ]
    for text, tx, ty, th in labels:
        lines.append(indent(1, f"(gr_text \"{text}\" "
            f'(at {fmtp(tx, ty)} 0) '
            f'(layer "F.SilkS") (uuid "{U()}")'))
        lines.append(indent(2, f'(effects (font (size {fmt(th)} {fmt(th)}) '
            f'(thickness {fmt(th*0.15)}) (bold no) (italic no)) '
            f'(justify left bottom)))'))

    # ── Close ────────────────────────────────────────────────────────
    lines.append(indent(1, "(embedded_fonts no)"))
    lines.append(")")

    with open(pcb_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return pcb_path


def write_companion():
    """Write project, schematic, and README files."""
    os.makedirs(PROJECT_DIR, exist_ok=True)

    with open(os.path.join(PROJECT_DIR, f"{PROJECT_NAME}.kicad_pro"), "w") as f:
        f.write(f"""(kicad_project (version 1)
  (title "{PROJECT_NAME}")
  (date "2026-06-10")
  (paper "A4")
)
""")

    with open(os.path.join(PROJECT_DIR, f"{PROJECT_NAME}.kicad_sch"), "w") as f:
        f.write(f"""(kicad_sch (version 20241229) (generator "eeschema")
  (uuid {U()})
  (paper "A4")
  (title_block
    (title "Weather Station Power Supply")
    (date "2026-06-10")
    (rev "v1.0")
    (company "Weather Station Research")
  )
)
""")

    with open(os.path.join(PROJECT_DIR, "README.md"), "w") as f:
        f.write(f"""# Weather Station — Power Supply PCB

## Board Specs
- {BW:.0f}mm × {BH:.0f}mm, 2-layer, 1.6mm FR4, 1oz copper
- HASL lead-free finish
- KiCad 9/10 format

## Ordering (JLCPCB / PCBWay)
Upload `{PROJECT_NAME}.kicad_pcb` directly, or export Gerbers:
```
kicad-cli pcb export gerbers -o gerber/ {PROJECT_NAME}.kicad_pcb
kicad-cli pcb export drill -o gerber/ {PROJECT_NAME}.kicad_pcb
```

## BOM ({len(COMPS)} components)
| Ref | Value | Qty |
|-----|-------|-----|
""")
        for ref, val, *_ in COMPS:
            if not ref.startswith("MH"):
                f.write(f"| {ref} | {val} | 1 |\n")
        f.write("| MH* | M3 screw | 4 |\n")
        f.write(f"""
## Verify
```
kicad-cli pcb drc {PROJECT_NAME}.kicad_pcb
```

---
Generated by Hermes Agent — June 10, 2026
""")


# ── Build net_code lookup ────────────────────────────────────────────
NET_CODE = {}
for code, name, _nodes in NETS:
    NET_CODE[name] = code


if __name__ == "__main__":
    print("=" * 55)
    print("  Weather Station — Power Supply PCB")
    print("  (Pure S-expression generator)")
    print("=" * 55)
    pcb = generate()
    write_companion()
    print(f"  Board: {BW:.0f}×{BH:.0f}mm, 2-layer")
    print(f"  Components: {len(COMPS)}")
    print(f"  Nets: {len(NETS)}")
    print(f"  Saved: {pcb}")
    print("=" * 55)
