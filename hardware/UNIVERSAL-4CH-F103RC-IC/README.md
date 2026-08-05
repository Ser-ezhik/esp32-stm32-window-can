# UNIVERSAL-4CH-F103RC-IC

Compact four-actuator controller placement based on one STM32F103RCT6.

## Placement release

- Board outline: 136.0 x 105.0 mm.
- Layers: two copper layers planned.
- Controller: STM32F103RCT6, LQFP64, soldered on the bottom.
- Motor drivers: four VNH5019A-E, soldered on the bottom.
- Motor connectors: four keyed 4-pin connectors on the top edge.
- Reed switches: three 3-pin connectors on the bottom edge.
- Capacitive sensors: three 2-pin connectors on the right edge.
- CAP1188, SPI flash EEPROM and low-voltage SMD parts are soldered on the bottom.
- CAN transceiver and MP1584 5 V converter remain replaceable top-side modules.
- Two unplated heatsink mounting holes are provided around each VNH5019A-E.

This release is placement only. It intentionally contains no tracks or copper
zones. Routing starts only after the placement is approved.

## Checks

- Custom mechanical placement check: 0 errors.
- KiCad DRC: 0 rule violations.
- Unconnected items reported by KiCad are expected in this placement release.

Open `kicad/UNIVERSAL-4CH-F103RC-IC.kicad_pcb` in KiCad 10.

