# UNIVERSAL-2CH

Compact universal carrier for two 12 V linear actuators. The same assembled
board can be provisioned as an optional sliding-door drive or as a two-actuator
vent/window node.

## Hardware

- Board: 120 x 135 mm, four copper layers.
- Controller: one socketed STM32F103C8T6 Mini.
- Drivers: two VNH5019A-E channels with mounting holes for top heatsinks.
- Network: socketed SN65HVD230 CAN transceiver module and protected edge entry.
- Touch safety: optional socketed CAP1188 SPI module with three field inputs.
- Position: three protected reed-switch inputs.
- Identity and journal: 25LC256 carrier EEPROM.
- Supply: socketed MP1584 12 V to 5 V converter, 3.3 V regulator, power-good
  monitor, and logic hold-up capacitor.

## Connectors

- `J1`, `J2`: actuator connectors, `+12V / GND / MA / MB`.
- `J201` to `J203`: open, closed, and in-place reed sensors.
- `J211` to `J213`: capacitive field sensors.
- `J230`: protected 12 V logic input.
- `J240`: `CANH / CANL / GND / shield`.
- `J220`: SWD service header.

All external field connectors are placed on board edges. Power routing and
VNH5019 devices occupy the upper half; CAN and touch electronics are kept away
from the motor outputs.

## KiCad Files

- `kicad/UNIVERSAL-2CH.kicad_pcb`: routed PCB.
- `kicad/UNIVERSAL-2CH.kicad_sch`: complete flat schematic.
- `kicad/UNIVERSAL-2CH-multisheet.kicad_sch`: multisheet root schematic.
- `kicad/UNIVERSAL-2CH-top.png`: top-side 3D render.
- `UNIVERSAL-2CH-BOM.csv`: grouped BOM.

## Verification

- PCB DRC: 0 violations, 0 unconnected items.
- Flat schematic ERC: 0 errors, 0 warnings.
- Multisheet schematic ERC: 0 errors, 0 warnings.
- PCB-to-schematic sync: 90 references, 283 connected pads, 38 explicit NCs.
- STM32 pin audit: 27 functional socket connections match `config.h`.
- STM32 build: 24,136 bytes Flash (36%), 3,500 bytes RAM (17%).
