# UNIVERSAL-4CH-F103RC-IC

Compact four-actuator controller based on one STM32F103RCT6.

## Routed board

- Board outline: 124.05 x 93.05 mm.
- Layers: two copper layers.
- Controller: STM32F103RCT6, LQFP64, soldered on the bottom.
- Motor drivers: four VNH5019A-E, soldered on the bottom.
- Motor connectors: four keyed 4-pin connectors on the top edge.
- Reed switches: three 3-pin connectors on the bottom edge.
- Capacitive sensors: three 2-pin connectors on the right edge.
- CAP1188, SPI flash EEPROM and low-voltage SMD parts are soldered on the bottom.
- CAN transceiver and MP1584 5 V converter remain replaceable top-side modules.
- Two unplated heatsink mounting holes are provided around each VNH5019A-E.
- Motor supply and output routes are reinforced by 2.0 mm copper zones.
- Both copper layers include GND planes.
- Reed connectors supply 5 V and use 4.7 kohm series protection for accidental
  D-M9P connection to a 3.3 V MCU input.

## Assembly note

Fit one short insulated wire from the positive lead of `C280` to `J280B` on the
bottom side. This connects the hold-up capacitor after `D280` to the input of
the 3.3 V regulator. The connection is explicitly marked on B.Silkscreen.

## Checks

- KiCad DRC: 0 violations, 0 unconnected pads.
- Automated critical pad/net contract check: PASS.
- Four VNH channels, CAP1188 SPI, EEPROM SPI, remapped CAN, SWD, power-good and
  three protected reed inputs are included in the contract check.

## Firmware status

The board uses the universal CAN protocol, but it requires the dedicated
`STM32F103RCT6 / 4CH integrated` build configuration. The existing F103C8
two-channel binary must not be flashed onto this board. The pin contract for
the four-channel build is documented in `PINMAP.md`.

Open `kicad/UNIVERSAL-4CH-F103RC-IC.kicad_pcb` in KiCad 10.
