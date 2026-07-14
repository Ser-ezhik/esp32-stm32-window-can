# Hardware architecture

## Cabinet topology

Each physical object is one CAN node regardless of actuator count.

```text
CAN_H / CAN_L / GND
        |
        +-- universal STM32 in MASTER slot -- 2 x VNH2SP30
                   |-- UART 1 -- universal STM32 SLAVE1 -- 2 x VNH2SP30
                   |-- UART 2 -- universal STM32 SLAVE2 -- 2 x VNH2SP30
                   `-- UART 3 -- universal STM32 SLAVE3 -- 2 x VNH2SP30
```

A window uses master only. A four-actuator door uses master plus one slave. An
eight-actuator double door uses master plus all three slaves.

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

JTAG must be disabled while SWD remains enabled to release PB3 and PB4. Native
USB is not used because PA11/PA12 are assigned to CAN. The board CH340 connection
on PA9/PA10 is not used as the control UART.

## Power and signal rules

- 12 V motor power and logic DC/DC branches are fused separately.
- Every actuator channel has its own fuse.
- Motor returns and logic ground meet at the cabinet power entry, not through a
  development-board ground trace.
- VNH inputs have external pull-downs so reset cannot start an actuator.
- D-M9N sensors are powered from 5 V and use external 4.7-10 kOhm pull-ups to 3.3 V.
- CAP1188 `ADDR_COMM` is tied to GND for normal 4-wire SPI mode.
- CAN uses 120 Ohm termination only at the two physical ends of the complete bus.
- The final carrier must include transient suppression and reverse-polarity protection.

## Power-good input

All ADC-capable pins are already allocated, so 12 V is monitored by a comparator or
supervisor on the carrier. Its open-drain output drives PC13 low when motor supply is
below the safe threshold. This avoids an unsafe analog pin conflict with current sense,
SPI or UART.
