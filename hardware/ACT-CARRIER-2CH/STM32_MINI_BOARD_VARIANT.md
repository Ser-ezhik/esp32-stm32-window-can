# Required STM32 mini-board variant

## Selected module

Use the compact `STM32F103C8T6 mini` module shown in the supplier diagram. It
has two 1x15, 2.54 mm pin rows, a USB-C connector and a selectable USB/UART
implementation.

## Mandatory order / assembly option

Order the board in **UART mode**:

- the CH340 USB-UART bridge is fitted;
- the board's R4 and R5 UART selection links are fitted;
- the alternative native-USB path is not fitted.

The supplier describes USB and UART as mutually exclusive Type-C functions. This
choice is mandatory because native USB uses `PA11` and `PA12`, while a MASTER
carrier needs those pins for bxCAN. The UART bridge normally connects to PA9 and
PA10. PA9 remains usable as the second 20 kHz PWM output because the CH340 RX
input is high impedance; PA10 is not used by the actuator firmware.

All replacement modules must be bought in this same configuration. It preserves
the project's "any STM32 board can replace any STM32 board" repair rule.

## Carrier footprint

The carrier uses two 1x15 female sockets:

| Parameter | Value |
| --- | --- |
| Contacts | 2 rows x 15 |
| Contact pitch along row | 2.54 mm |
| Row centre-to-centre spacing | 20.32 mm |
| Nominal module envelope | 38.1 x 22.86 mm |
| Mounting | Socketed; USB-C must face a board edge for service access |

Before Gerber release, compare this footprint with one physical purchased board
using a 1:1 print. Low-cost listings sometimes change the USB-C daughter layout
or fit an LSE crystal without changing the listing photo.

## LSE and slot straps

The board exposes PC14 and PC15 and shows optional LSE circuitry. Purchase the
version with the LSE crystal **not fitted**, otherwise PC14/PC15 cannot provide
the two carrier `SLOT_ID` straps. This is checked with a continuity meter on the
first physical sample before the PCB layout is released.
