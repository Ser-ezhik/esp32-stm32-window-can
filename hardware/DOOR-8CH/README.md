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

## Internal UART routing

No UART cable leaves the board. The following tracks are routed directly on the
DOOR-8CH PCB, with a shared signal-ground plane:

| Master UART | MASTER STM32 pins | SLAVE STM32 pins | Destination slot |
| --- | --- | --- | --- |
| UART 1 | PB6 TX, PB7 RX | PB7 RX, PB6 TX | S2 |
| UART 2 | PA3 TX, PA2 RX | PB7 RX, PB6 TX | S3 |
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
| CAP1188 SPI breakout | Every door board; window only when required | PA4-PA7, PB9, PB13, 3.3 V |
| 25LC256 EEPROM | Every board, S1 zone | PA15 plus shared SPI pins |
| Reeds and power-good comparator | Every board, S1 zone | PB0, PB1, PB8, PC13 |

CAN enters the S1 edge through TVS and a common-mode choke, then branches only
to the S1 CAN module and, on the double-door board, to the ESP CAN module.
S2-S4 have no CAN components or external sensor connectors.

## Power architecture

The cabinet MP1584 produces one protected `LOGIC_5V` feed for the whole board.
The board generates one `LOGIC_3V3` rail for all module headers and VNH DIAG
pull-ups. Each STM32 mini board receives 5 V through its own protected branch.

Motor power is intentionally not bussed across the PCB:

- each VNH channel receives its own `FUSED_12V_CHx` and GND pair from the
  cabinet fuse distribution;
- every channel remains protected by its own 7.5 A fuse;
- there is no 40 A trace from the double-door supply input to the VNH slots;
- local 470 uF / 35 V capacitors remain beside every VNH5019.

This keeps the double-door's eight-channel current out of a single board-wide
power bottleneck while eliminating inter-board UART and logic-power wiring.

## Preliminary mechanical plan

- One board, maximum initial outline: 260 x 160 mm.
- Four VNH zones along the long actuator-connector edge; each zone has two
  actuator terminal blocks and two separately fused power-input pairs.
- Four STM32 sockets form the low-voltage centre strip.
- CAN, CAP1188, reeds, SWD, ESP32-S3, CC1101 and both CAN-module sockets sit at
  the opposite edge, far from motor-current loops.
- Four layers, 2 oz external copper. VNH exposed pads receive thermal via arrays
  to internal copper areas.

The final outline is set after the selected 5.08 mm terminals are checked on a
1:1 print. This is a PCB design input, not a Gerber release.
