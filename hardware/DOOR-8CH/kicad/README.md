# KiCad source: DOOR-8CH

`DOOR-8CH.kicad_pcb` is the editable KiCad 10 board source, started from the
approved universal one-board-per-cabinet architecture. It presently contains:

- the provisional 260 x 160 mm outline;
- the four board mounting holes, M3.2 NPTH;
- a four-layer stack-up declaration;
- mechanically checked placement for S1 through S4 and the photographed
  plug-in modules.

It is deliberately a placement-stage source, not a fabrication release. No
Gerbers, component coordinates, copper, schematic netlist or routing are
released until the physical module footprints have been verified at 1:1 scale.

The placement already uses KiCad's verified `ST_MultiPowerSO-30` footprint for
all eight VNH5019A-E devices, `Phoenix MKDS-3-2-5.08` two-way power terminals,
and one-piece 4x10 / 2.54 mm socket footprints for each STM32 module. Each VNH
has one dedicated fused 12 V terminal and one actuator-output terminal. The 26 mm
heatsink-hole pair is above and below its VNH, avoiding overlap with a
neighbouring channel.

All 16 motor terminals are on the top edge. STM32 USB-C connectors face the
bottom service edge, both ESP32-S3 USB connectors face the left edge, the
CC1101 antenna faces the left edge, and CAP1188 touch-channel pins face the
right edge. The placement uses complete photo-matched footprints for the two
SN65HVD230 modules, CC1101 and CAP1188, plus Espressif's official 44-pin
ESP32-S3-DevKitC footprint. KiCad placement DRC reports zero violations.

## Next CAD stages

1. Capture the electrical schematic for S1 and the repeatable S2-S4 slots.
2. Add every VNH passive network, logic power protection, CAN protection and
   external field connector to the schematic and PCB.
3. Add the top-side heatsink keepout areas and thermal-via arrays around the
   existing VNH positions.
4. Set net classes, route the four-layer board, run ERC/DRC and produce
   1:1 mechanical prints for connector validation.

The older `ACT-CARRIER-2CH` files remain an archived design study and must not
be used for fabrication.
