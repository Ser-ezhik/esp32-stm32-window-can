# UNIVERSAL-2CH-F103-IC

Compact universal two-actuator controller board with direct-mounted
STM32F103C8T6 and CAP1188 ICs.

## Board status

- two copper layers: F.Cu and B.Cu;
- board size: 83.1 x 100.1 mm;
- 101 footprints;
- 2 VNH5019A-E actuator channels;
- 2 reed-switch connectors;
- 3 capacitive sensor connectors;
- CAN transceiver module socket;
- external 5 V MP1584 DC-DC module footprint;
- SPI EEPROM and power-fail supervision;
- full GND planes on both layers;
- local copper reinforcement on all motor output and fused 12 V routes.

## Verification

KiCad 10 DRC result:

- 0 DRC violations;
- 0 unconnected pads;
- 0 footprint errors.

Silkscreen-to-mask and silkscreen-overlap checks are disabled in the project
settings because the module outlines intentionally overlap connector and module
pad keepouts. Electrical, copper, drill, clearance, and connectivity checks
remain enabled.

Open `kicad/UNIVERSAL-2CH-F103-IC.kicad_pro` in KiCad.

## Fabrication releases

- `fabrication/v1.5-c88056` is the current production release. It preserves the
  verified v1.4 Gerber/CPL and replaces the unavailable L240 with TDK
  ACT45B-101-2P-TL003 (`C88056`).
- `fabrication/v1.4-orientation-verified` is retained as the preceding release.
  It includes `F.Mask` and `B.Mask`, the corrected JLCPCB BOM/CPL files, DRC
  report, Gerber ZIP, the JLCPCB placement screenshot, and a component-by-
  component orientation check. The JLCPCB cart project is `Y14`.
- `fabrication/v1.1-maskfix`, `v1.2-orientationfix`, and
  `v1.3-orientation-audit` are retained for history and must not be ordered.
- `fabrication/v1.0-audited` must not be manufactured: its Gerber archive was
  generated without the solder-mask layers.

The release build stops with an error if either copper layer, either
solder-mask layer, or the board outline is missing.
