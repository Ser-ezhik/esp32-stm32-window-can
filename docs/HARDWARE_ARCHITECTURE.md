# Hardware architecture

## Cabinet topology

Each physical object is one CAN node regardless of actuator count.

```text
CAN_H / CAN_L / GND
        |
        +-- universal STM32 in MASTER slot -- 2 x VNH5019A-E
                   |-- UART 1 -- universal STM32 SLAVE1 -- 2 x VNH5019A-E
                   |-- UART 2 -- universal STM32 SLAVE2 -- 2 x VNH5019A-E
                   `-- UART 3 -- universal STM32 SLAVE3 -- 2 x VNH5019A-E
```

A window uses master only. A four-actuator door uses master plus one slave. An
eight-actuator double door uses master plus all three slaves.

## ESP32 controller board

The selected board is the two-USB-C `ESP32-S3-WROOM-1` development board shown
in the project photo. It is compatible with the ESP32 firmware in this repository.
Use its USB-UART port for initial flashing and serial diagnostics; the second
USB-C connector is not required by the control system.

| Function | ESP32-S3 GPIO | Connection |
| --- | ---: | --- |
| CAN RX | 38 | MCP2562 `RXD` |
| CAN TX | 39 | MCP2562 `TXD`, through 47 Ohm |
| CC1101 SCK / MISO / MOSI / CS | 12 / 13 / 11 / 10 | CC1101 SPI bus |
| CC1101 GDO0 / GDO2 | 4 / 5 | CC1101 digital outputs |
| Learn button | 9 | Button to GND, use internal pull-up |

Supply the board with regulated **5 V** from the cabinet DC/DC converter through
its `5V` pin and connect a common GND. Never feed the 12 V actuator supply into
the ESP32 board. The onboard RGB LED on GPIO47/48 is not used by the controller
firmware and remains free.

### CC1101 433 MHz module

The selected 28 x 15 mm `433M V2.0` CC1101 module has an eight-pin, two-column
header. Connect it exactly as follows; its VCC and all I/O are **3.3 V only**.

| CC1101 pin | Label | ESP32-S3 connection |
| ---: | --- | --- |
| 1 | VCC | 3.3V |
| 2 | GND | GND |
| 3 | GDO0 | GPIO4 |
| 4 | CSN | GPIO10 |
| 5 | SCK | GPIO12 |
| 6 | MOSI | GPIO11 |
| 7 | MISO / GDO1 | GPIO13; GDO1 is unused |
| 8 | GDO2 | GPIO5 |

Fit the 100 nF and 10 uF bypass capacitors listed in the BOM directly beside
this connector. Mount the supplied 433 MHz spring antenna vertically, keep it
away from the CAN cable and motor wiring, and do not place it against a metal
wall of the cabinet.

### CAN prototype module

The pictured six-pin `3V3 / GND / CTX / CRX / CANH / CANL` module is the common
`SN65HVD230` 3.3 V CAN-transceiver board. It is electrically compatible with
the 500 kbit/s project CAN bus and may be used for the first prototype instead
of the carrier's MCP2562 footprint. It is a transceiver, not a CAN controller;
the ESP32-S3 and STM32F103 provide the CAN controller themselves.

| Module pin | STM32 MASTER | ESP32 controller |
| --- | --- | --- |
| 3V3 | 3.3V | 3.3V |
| GND | GND | GND |
| CTX | PA12 (CAN TX) | GPIO39 (CAN TX) |
| CRX | PA11 (CAN RX) | GPIO38 (CAN RX) |
| CANH | CANH trunk | CANH trunk |
| CANL | CANL trunk | CANL trunk |

Before fitting all six modules, use an unpowered multimeter to measure each
one between `CANH` and `CANL`. If it reads about 120 Ohm, it has a fitted
termination resistor and may be installed only at a physical end of the CAN
cable, or its resistor must be removed. Across the complete unpowered CAN
trunk, with exactly two 120 Ohm terminators installed, the reading must be
about **60 Ohm**. Intermediate cabinets have no termination.

This small module has no connector-level surge protection. Keep the BOM's CAN
TVS, common-mode choke and CAN_GND reference conductor at every cabinet entry.

### CAP1188 touch module

The selected `CAP1188 8-Key CapTouch SPI/I2C w/LEDs` breakout is suitable. Use
its **SPI** interface only; do not enable or connect I2C. Power its `VIN` pin
from 3.3 V, connect `GND`, and leave its `3Vo` output unconnected. The eight
LEDs are indication outputs and do not replace the capacitive inputs `C1...C8`.

| CAP1188 label | STM32 MASTER pin | Notes |
| --- | --- | --- |
| VIN | 3.3V | Do not feed 5 V in this system. |
| GND | GND | Common signal ground. |
| CS | PA4 | SPI chip select. |
| SCK | PA5 | SPI clock. |
| MISO | PA6 | SPI data from CAP1188. |
| MOSI | PA7 | SPI data to CAP1188. |
| RST | PB9 | Reset, pulled up to 3.3 V. |
| IRQ | PB13 | Interrupt, pulled up to 3.3 V. |
| C1...C8 | Touch perimeter electrodes | Every reported touch is treated as a safety-edge event while closing. |

Keep the breakout and the cable to its touch electrodes away from 12 V motor
wiring and PWM tracks. For a long perimeter, use one conductor per electrode
with a nearby GND reference or screened cable; final sensitivity is adjusted
during commissioning with the actual door and cable installed. Connect every
enabled channel to a real electrode; reserve unused channels only after their
configuration is explicitly added to the firmware.

## Replaceable module identity

Every STM32 module carries the same firmware and interface circuit. Two carrier
signals select the role at boot:

| SLOT_ID1 | SLOT_ID0 | Role |
| --- | --- | --- |
| 1 | 1 | MASTER |
| 1 | 0 | SLAVE1 |
| 0 | 1 | SLAVE2 |
| 0 | 0 | SLAVE3 |

The firmware reads active-low straps, therefore an empty/unstrapped test module
starts as MASTER. The cabinet address is not stored only on the replaceable MCU.
A 25LCxx-compatible SPI EEPROM on the carrier stores cabinet ID, object type and
slave count. Until that record has a valid CRC, all bridge outputs remain disabled.

## STM32F103C8T6 pin assignment

The selected MCU module is the compact USB-C `STM32F103C8T6 mini` board shown
in the project photo. Every carrier accepts the same module; MASTER or SLAVE
identity comes only from the carrier straps and its configuration EEPROM, not
from a different STM32 firmware.

| Function | Pins |
| --- | --- |
| VNH current sense | PA0, PA1 |
| Master UART 2 | PA2 RX, PA3 TX |
| CAP1188 SPI1 | PA4 CS, PA5 SCK, PA6 MISO, PA7 MOSI |
| VNH PWM | PA8, PA9 |
| CAN | PA11 RX, PA12 TX |
| SWD | PA13, PA14 |
| Carrier EEPROM CS | PA15 |
| Reeds | PB0, PB1, PB8 |
| VNH direction | PB3, PB4, PB14, PB15 |
| VNH diagnostics | PB5, PB12 |
| Master UART 1 / slave upstream | PB7 RX, PB6 TX |
| CAP1188 reset / IRQ | PB9, PB13 |
| Master UART 3 | PB11 RX, PB10 TX |
| 12 V power-good input | PC13 |
| SLOT_ID | PC14, PC15 |

Feed the module with regulated 5 V through its `5V` pin and GND from the
cabinet low-voltage supply. Its `3V3` pin is the logic rail for its local
signals; never apply 5 V to any STM32 GPIO. The USB-C connection is for service
flashing and diagnostics. Do not connect USB power and an external 5 V cabinet
supply at the same time until the carrier's service-power isolation diode is
implemented.

JTAG must be disabled while SWD remains enabled to release PB3 and PB4. Native
USB is not used because PA11/PA12 are assigned to CAN. The board CH340 connection
on PA9/PA10 is not used as the control UART.

PC14 and PC15 can only be used for `SLOT_ID` if the mini-board does not populate
the 32.768 kHz LSE crystal on those pins. Verify the actual board before making
the carrier PCB; otherwise move the two slot straps to free GPIO pins.

## Power and signal rules

- 12 V motor power and logic DC/DC branches are fused separately.
- Every actuator channel has its own fuse.
- Motor returns and logic ground meet at the cabinet power entry, not through a
  development-board ground trace.
- VNH inputs have external pull-downs so reset cannot start an actuator.
- D-M9N and D-M9P sensors may be powered from 3.3 V when that voltage has been
  verified on the exact sensors. D-M9N inputs use pull-ups; D-M9P inputs use
  pull-downs. A three-bit polarity mask is stored in the cabinet EEPROM, so the
  replaceable STM32 firmware remains universal. Do not power a sensor output from
  5 V when it is connected directly to an STM32 input.
- CAP1188 `ADDR_COMM` is tied to GND for normal 4-wire SPI mode.
- CAN uses 120 Ohm termination only at the two physical ends of the complete bus.
- The final carrier must include transient suppression and reverse-polarity protection.

## Power-good input

All ADC-capable pins are already allocated, so 12 V is monitored by a comparator or
supervisor on the carrier. Its open-drain output drives PC13 low when motor supply is
below the safe threshold. This avoids an unsafe analog pin conflict with current sense,
SPI or UART.
