# WINDOW-4CH carrier

`WINDOW-4CH` is the separate four-actuator carrier for one window. It does not
replace or modify `DOOR-8CH`.

## Architecture

- S1 is the MASTER STM32F103C8T6 and controls actuator channels 1 and 2.
- S2 is the SLAVE STM32F103C8T6 and controls channels 3 and 4.
- S1 and S2 use a direct 250 kbit/s UART link inside the cabinet.
- Only S1 is connected to the 500 kbit/s CAN bus through one SN65HVD230 module.
- One CAP1188 module provides four field connectors: three working edge
  sensors and one spare channel.
- Three D-M9 reed inputs report open, closed and in-place positions.
- One 25LC256 carrier EEPROM stores cabinet identity and the power-loss record.
- U270, D280 and C280 provide power-fail detection and MASTER hold-up.

The compact board outline is 155 x 150 mm and uses four copper layers. All external
power, actuator, CAN, reed and capacitive-sensor connectors are placed at board
edges. The SWD service connector remains inside the low-voltage service area.
Four VNH5019A-E channels retain the same protection, current sensing, bulk
capacitance and top-mounted heatsink hole pattern as the validated 8-channel
design. Clearance-checked GND stitching vias tie all four copper layers together
around the power section.

## KiCad files

- `kicad/WINDOW-4CH.kicad_pcb` - routed KiCad 10 PCB.
- `kicad/WINDOW-4CH.kicad_sch` - complete flat schematic.
- `kicad/WINDOW-4CH-multisheet.kicad_sch` - recommended multisheet entry.
- `WINDOW-4CH-BOM.csv` - grouped bill of materials.
- `SCHEMATIC_FIRMWARE_AUDIT.md` - firmware pin and configuration audit.

The PCB passes DRC with zero violations and zero unconnected items. The flat
and multisheet schematics pass ERC with zero errors. Isolated-label warnings
are retained for universal STM32 pins that are deliberately unused on this
two-controller carrier.

## Required cabinet configuration

Provision S1 as an object with:

- object type: window (`0`);
- actuator count in the ESP32 object table: `4`;
- slave count in the carrier EEPROM: `1`;
- CAP enabled mask: normally `0x07`; use bit 3 only when the spare sensor is
  populated;
- reed polarity mask bits 0..2 according to the installed D-M9N/D-M9P sensors.

S2 is identified by the carrier slot straps and uses the same universal STM32
firmware as S1. A replacement STM32 module therefore requires no location-
specific firmware.

## Before fabrication

1. Check the photographed STM32, CAP1188, CAN and MP1584 modules on a 1:1 print.
2. Assemble and test one VNH5019 channel before ordering the full quantity.
3. Calibrate current conversion and overcurrent limits on the real actuator.
4. Measure C280 hold-up time at low temperature and confirm a complete EEPROM
   power-loss write after repeated 12 V removal.
5. Do not release production Gerbers until those physical checks are complete.
