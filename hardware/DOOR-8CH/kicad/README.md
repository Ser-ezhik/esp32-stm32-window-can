# KiCad source: DOOR-8CH

`DOOR-8CH.kicad_pcb` is the editable KiCad 10 board source, started from the
approved universal one-board-per-cabinet architecture. It presently contains:

- the provisional 260 x 160 mm outline;
- the four board mounting holes, M3.2 NPTH;
- a four-layer stack-up declaration;
- mechanically checked placement for S1 through S4 and the photographed
  plug-in modules.

It is deliberately a design-stage source, not a fabrication release. The v1.41
board contains the repeated VNH passive blocks, slot straps, named power,
motor, control, diagnostic, current-sense and low-voltage communication nets.
The routed PCB passes DRC with zero violations and zero unconnected pads.

Two electrically equivalent principle-schematic views are included:

- `DOOR-8CH.kicad_sch` is the complete flat schematic;
- `DOOR-8CH-multisheet.kicad_sch` is the recommended entry point, split into
  power, control/CAN, CAP1188, reeds, eight actuator channels and mechanical
  sheets.

Both schematic views are generated from the routed PCB and verified by
`tools/verify_door8ch_schematic_sync.py`. The firmware comparison is recorded
in `../SCHEMATIC_FIRMWARE_AUDIT.md`.

The placement already uses KiCad's verified `ST_MultiPowerSO-30` footprint for
all eight VNH5019A-E devices, `Phoenix MKDS-3-2-5.08` two-way power terminals,
and one-piece 4x10 / 2.54 mm socket footprints for each STM32 module. Each VNH
has one dedicated fused 12 V terminal and one actuator-output terminal. The 26 mm
heatsink-hole pair is above and below its VNH, avoiding overlap with a
neighbouring channel.

Each VNH now has three 100 Ohm input resistors, reset-safe pull-downs, a 4.7
kOhm diagnostic pull-up, CS_DIS pull-down, 1 kOhm current-sense load, protected
and filtered ADC input, 470 uF local bulk capacitor and 100 nF ceramic bypass.
The PB2/PA7 slot straps are also present and match the universal firmware.
The low-voltage stage also includes the MP1584 input/output nets, a carrier
3.3 V regulator, CAN trunk connector with choke/ESD/optional termination,
both SN65HVD230 modules, 25LC256 carrier EEPROM, CAP1188 SPI and field-sensor nets, six reed
connectors, ESP32-S3 power/CAN, CC1101 SPI/GDO lines and the internal UART
links between S1 and S2-S4. In v0.7 the CAN trunk entry and its protection
parts are moved to the lower service area beside `CAN2`, and `MOD3` is shifted
right to keep that CAN area away from the actuator power terminals.

Version v1.41 adds U270 (`TLV6700DDCR`) on the fused 12 V logic input, an
open-drain `POWER_GOOD` connection to S1 PC13, and an isolated MASTER hold-up
rail using D280 (`SS34`) and C280 (4700 uF / 10 V low ESR). U250 and its SPI
pull-ups are powered by the held `S1_3V3` rail so an outage record can finish.

All 16 motor terminals are on the top edge. STM32 USB-C connectors face the
bottom service edge, both ESP32-S3 USB connectors face the left edge, the
CC1101 antenna faces the left edge, and CAP1188 touch-channel pins face the
right edge. The placement uses complete photo-matched footprints for the two
SN65HVD230 modules, CC1101 and CAP1188, plus Espressif's official 44-pin
ESP32-S3-DevKitC footprint. KiCad placement DRC reports zero violations.

## Before fabrication

1. Verify all photographed module footprints, row orientation and connector
   polarity on 1:1 prints and physical samples.
2. Populate one VNH5019 channel and calibrate the current-sense conversion and
   protection thresholds before releasing production Gerbers.
3. Measure the C280 hold-up time at cold temperature and maximum MASTER load;
   verify a complete U250 write after removing 12 V repeatedly.

The older `ACT-CARRIER-2CH` files remain an archived design study and must not
be used for fabrication.
