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

## Next CAD stages

1. Add exact through-hole footprints for the selected STM32 mini board,
   ESP32-S3 board, CC1101, CAP1188 and SN65HVD230 modules.
2. Capture the electrical schematic for S1 and the repeatable S2-S4 slots.
3. Add VNH5019A-E MultiPowerSO-30 footprints, passive networks, terminal
   blocks and the top-side heatsink keepouts.
4. Set net classes, route the four-layer board, then run ERC/DRC and produce
   1:1 mechanical prints for connector validation.

The older `ACT-CARRIER-2CH` files remain an archived design study and must not
be used for fabrication.
