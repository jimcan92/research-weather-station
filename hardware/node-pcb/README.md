# Weather node schematic

`weather-node-complete.kicad_sch` is the current complete schematic (v2.1, 2026-09-29).
`gen_node_complete.py` is its generator; `DIYMORE-RS485.kicad_sym` defines the new U4 module.

`rs485-module-wiring.svg` shows the revised RS485 wiring. **UART signal directions remain provisional**; see `../../docs/sensor-wiring.md` before wiring.

The existing `weather-node-complete.pdf`, `weather-node-complete.svg/`, and PNG previews are older MAX485 exports and must be regenerated with KiCad before use. The older `weather-node.kicad_sch` is not the canonical complete design.

KiCad ERC and generator execution were unavailable in this environment. Native syntax and affected pin/net connections were checked with a local S-expression reader.
