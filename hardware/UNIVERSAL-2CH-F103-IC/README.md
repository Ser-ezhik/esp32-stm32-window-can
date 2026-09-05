# UNIVERSAL-2CH-F103-IC

Compact universal two-actuator controller board with direct-mounted
STM32F103C8T6 and CAP1188 ICs.

## Board status

- two copper layers: F.Cu and B.Cu;
- board size: 83.1 x 100.1 mm;
- 106 footprints;
- 2 VNH5019A-E actuator channels;
- 2 protected 5 V reed-sensor connectors (5V/SIG/GND);
- 3 capacitive sensor connectors;
- CAN transceiver module socket;
- external fixed 5 V DC-DC footprint: 18 x 13 mm body, 15 x 9 mm pad spacing;
- SPI EEPROM and power-fail supervision;
- full GND planes on both layers;
- local copper reinforcement on all motor output and fused 12 V routes.

## Verification

KiCad 10 DRC result:

- 0 DRC errors, 52 warnings (48 silkscreen and 4 copper slivers);
- 0 unconnected pads;
- 0 footprint errors.

These results were regenerated on 2026-09-06. Warnings remain visible and
have not been waived as a manufacturing approval. See REVIEW_FIX_2026-09-06.md.

Open `kicad/UNIVERSAL-2CH-F103-IC.kicad_pro` in KiCad.

## Assembly links

The board requires three insulated wire links: `C280+ -> J280B`,
`TP290 -> JP290 (J220.6)`, and `D230.1 -> C270.1`.
See `REED_5V_PROTECTION.md` before powering the
board.

## Fabrication releases

- All existing fabrication archives predate the September repair. Do not use
  their Gerbers or CPL files for the revised PCB. In particular C340 changed sides.
- `fabrication/v1.6-reed5v-protected` is a historical release. It
  powers J201/J202 from 5 V and adds 4.7 kOhm protected signal inputs.
- `fabrication/v1.5-c88056` is retained as the preceding release. It preserves the
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
