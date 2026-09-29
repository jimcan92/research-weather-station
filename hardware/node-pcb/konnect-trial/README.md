# Konnect trial — 2026-09-29

Open `weather-node-complete.kicad_sch` in this folder to inspect the trial. The canonical schematic in the parent folder remains unchanged.

Konnect v0.12.1 (official Linux standalone release) reset 172 Reference/Value field positions to their embedded-library anchors. Three power symbols were moved out of component bodies, and their wire stubs were explicitly replaced using Konnect's wire tools.

Final Konnect checks: zero symbol-geometry overlaps, zero shorted nets, zero orphan items. All pin-to-net mappings across 38 non-power circuit components match the original schematic. Reports are included here. Overlap checks exclude free text, so these results do not prove complete visual cleanliness.

KiCad CLI is not installed in this environment: full visual rendering and ERC remain unverified. This is a limited layout cleanup trial, not the proposed multi-sheet redesign. RS485 UART direction remains provisional as noted on the schematic.

The release's `move_connected` is not implemented; `move_region` also leaves wires in place. Do not rely on either to preserve connections automatically. The binary was run from `/tmp/konnect-trial/konnect`; no persistent MCP registration or skill installation was made.

Source: https://github.com/mixelpixx/Konnect/releases/tag/v0.12.1
