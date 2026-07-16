# DOOR-8CH v0.1

## Status

This is the active PCB architecture for the project. One DOOR-8CH board is
installed in each cabinet. It is universal: the same board serves a window, a
four-actuator single door or an eight-actuator double door by populating one,
two or four identical two-channel slots.

The earlier `ACT-CARRIER-2CH` concept remains in the repository as a superseded
study only. Do not fabricate it.

## Slot population

| Cabinet | Fitted slots | STM32 | VNH5019A-E |
| --- | ---: | ---: | ---: |
| Window | S1 | 1 | 2 |
| Single door | S1, S2 | 2 | 4 |
| Double door | S1, S2, S3, S4 | 4 | 8 |

Every slot has one socketed STM32 mini board and two VNH5019A-E channels. S1 is
always MASTER. S2 through S4 are SLAVEs when populated. This preserves the
repair rule: any programmed STM32 mini board can replace any other STM32 mini
board after inserting it in the same slot.

The carrier identifies the slot with two board straps sampled on PB2 and PA7
before peripheral initialisation. See
[`kicad/STM32_MODULE_PINMAP.md`](kicad/STM32_MODULE_PINMAP.md). This replaces
the earlier PC14/PC15 proposal, because both pins are not available on the
photographed module.

## Internal UART routing

No UART cable leaves the board. The following tracks are routed directly on the
DOOR-8CH PCB, with a shared signal-ground plane:

| Master UART | MASTER STM32 pins | SLAVE STM32 pins | Destination slot |
| --- | --- | --- | --- |
| UART 1 | PB6 TX, PB7 RX | PB7 RX, PB6 TX | S2 |
| UART 2 | PA2 TX, PA3 RX | PB7 RX, PB6 TX | S3 |
| UART 3 | PB10 TX, PB11 RX | PB7 RX, PB6 TX | S4 |

Place 100 Ohm series resistors at each transmitter, as specified in the BOM.
These links are short PCB traces within one cabinet and operate at 250 kbit/s.

## On-board modules

All selected off-the-shelf modules plug directly into headers on the DOOR-8CH
board. There are no loose SPI, CAN or UART jumpers between them.

| Zone / module | Fitted on | Board connection |
| --- | --- | --- |
| MASTER CAN: SN65HVD230 | Every board, S1 zone | PA12 CTX, PA11 CRX, CANH/CANL trunk |
| ESP32-S3 board | Double-door board only | 5 V, GND, its CAN and CC1101 signals |
| ESP CAN: SN65HVD230 | Double-door board only | GPIO39 CTX, GPIO38 CRX, same CAN trunk |
| CC1101 433 MHz | Double-door board only | GPIO10-13, GPIO4, GPIO5, 3.3 V |
| CAP1188 SPI breakout | Every board, including the window | PA4-PA7, PB9, PB13, 5 V VIN; eight C/GND field connectors |
| 25LC256 carrier EEPROM | Every board, S1 zone | PA15 CS plus shared SPI pins PA5, PA6, PA7 |
| Reeds A | Every board, S1 zone | S1 PB0, PB1, PB8 |
| Reeds B | Double-door build only | S2 PB0, PB1, PB8, reported to S1 over UART |
| Power-good comparator | Every board, S1 zone | PC13 |

CAN enters at the quiet lower service edge next to the optional ESP CAN module
`CAN2`. The connector is followed by TVS protection, a common-mode choke and
optional 120 Ohm termination, then branches to both `CAN1` and `CAN2`. S2-S4
have no CAN transceivers or external CAN connectors.

## Power architecture

The selected MP1584 module plugs or solders directly into the DOOR-8CH board and
produces one protected `LOGIC_5V` feed for the whole board. Its dedicated edge
input, 1 A branch fuse, reverse-polarity diode, SMBJ16A and input/output filters
are all on the same PCB; no loose DC/DC wiring is used.
The board generates one `LOGIC_3V3` rail from `LOGIC_5V` with a local AMS1117
style regulator for CAN, CC1101 and other plug-in module supplies. STM32 mini
board 3.3 V pins remain local to their own slot and are not tied together.
Each STM32 mini board receives 5 V from the protected logic rail.

S1 is supplied through D280 (`SS34`) from `LOGIC_5V`; C280 (4700 uF / 10 V,
low ESR) holds its isolated `S1_5V_HOLD` rail during a power failure. U270
monitors the fused 12 V input and pulls S1 PC13 low near 9.3 V. The EEPROM and
its pull-ups use the resulting held `S1_3V3` rail, allowing the MASTER to stop
outputs and finish one outage-record write before brownout.

The external SPI EEPROM stores the cabinet identity, object type, slave count
and reed polarity mask. See [CARRIER_EEPROM_MAP.md](CARRIER_EEPROM_MAP.md).
This keeps the STM32 firmware universal: a replacement STM32 module reads the
same carrier data after installation.

Motor power is intentionally not bussed across the PCB:

- each VNH channel receives its own `FUSED_12V_CHx` and GND pair from the
  cabinet fuse distribution;
- every channel remains protected by its own 7.5 A fuse;
- there is no 40 A trace from the double-door supply input to the VNH slots;
- local 470 uF / 35 V capacitors remain beside every VNH5019.

This keeps the double-door's eight-channel current out of a single board-wide
power bottleneck while eliminating inter-board UART and logic-power wiring.

## Mandatory VNH passives and heatsink provision

Every VNH5019 receives its complete passive network: reset-safe input pull-downs,
series resistors, diagnostic pull-up, CS_DIS pull-down, calibrated current-sense
resistors, ADC filter and local 470 uF / 35 V plus 100 nF power decoupling.
Each VNH zone also has a 30 x 30 mm heatsink keepout and two M3 holes for a
small external heatsink. See [VNH_THERMAL_AND_PASSIVES.md](VNH_THERMAL_AND_PASSIVES.md).

## Preliminary mechanical plan

- One board, maximum initial outline: 260 x 160 mm.
- Four VNH zones along the long actuator-connector edge; each zone has two
  actuator terminal blocks and two separately fused power-input pairs.
- Four STM32 sockets form the low-voltage centre strip.
- CAN, CAP1188, reeds, SWD, ESP32-S3, CC1101 and both CAN-module sockets sit at
  the lower/right service edges, away from the top motor-current terminals.
- S3 / `MOD3` is shifted right to keep the CAN trunk connector and protection
  physically close to `CAN2`.
- Eight separate 2-pin `CSx/GND` connectors for CAP1188 twisted pairs sit at a
  board edge. Firmware selects any active subset; unused channels remain disabled.
- Six three-pin reed connectors sit at the same field-connector edge: 3V3,
  signal and GND. A double door uses three on S1 for leaf A and three on S2 for
  leaf B.
- Four layers, 2 oz external copper. VNH exposed pads receive thermal via arrays
  to internal copper areas.

The final outline is set after the selected 5.08 mm terminals are checked on a
1:1 print. This is a PCB design input, not a Gerber release.
