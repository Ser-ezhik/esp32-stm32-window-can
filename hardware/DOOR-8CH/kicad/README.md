# KiCad source: DOOR-8CH

`DOOR-8CH.kicad_pcb` is the editable KiCad 10 board source, started from the
approved universal one-board-per-cabinet architecture. It presently contains:

- the provisional 260 x 160 mm outline;
- the four board mounting holes, M3.2 NPTH;
- a four-layer stack-up declaration;
- low-voltage and actuator-zone placement envelopes for S1 through S4.

It is deliberately a placement-stage source, not a fabrication release. No
Gerbers, component coordinates, copper, schematic netlist or routing are
released until the physical module footprints have been verified at 1:1 scale.

The placement already uses KiCad's verified `ST_MultiPowerSO-30` footprint for
all eight VNH5019A-E devices, `Phoenix MKDS-3-2-5.08` two-way power terminals,
and 1x15 / 2.54 mm sockets for each STM32 header row. Each VNH has one
dedicated fused 12 V terminal and one actuator-output terminal. The 26 mm
heatsink-hole pair is above and below its VNH, avoiding overlap with a
neighbouring channel.

## Next CAD stages

1. Add exact through-hole footprints for the selected STM32 mini board,
   ESP32-S3 board, CC1101, CAP1188 and SN65HVD230 modules.
2. Capture the electrical schematic for S1 and the repeatable S2-S4 slots.
3. Add passive networks, exact module footprints, terminal labels and the
   top-side heatsink keepouts around the existing VNH positions.
4. Set net classes, route the four-layer board, then run ERC/DRC and produce
   1:1 mechanical prints for connector validation.

The older `ACT-CARRIER-2CH` files remain an archived design study and must not
be used for fabrication.
