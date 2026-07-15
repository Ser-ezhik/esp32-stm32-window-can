# STM32F103C8T6 mini CH340 module pin map

This table is derived from the supplied photographs of the exact black
MuLuoxing module. The view is from the component side with USB-C at the top.
Pad numbers match `STM32F103C8T6_Mini_CH340_4x10.kicad_mod`.

| Left outer | Signal | Left inner | Signal | Right inner | Signal | Right outer | Signal |
| ---: | --- | ---: | --- | ---: | --- | ---: | --- |
| 1 | GND | 11 | 3V3 | 21 | 5V | 31 | GND |
| 2 | PB14 | 12 | PB15 | 22 | PA8 | 32 | PA9 |
| 3 | PB12 | 13 | PB13 | 23 | PA10 | 33 | PA11 |
| 4 | PB10 | 14 | PB11 | 24 | PA12 | 34 | PA13/SWDIO |
| 5 | PB1 | 15 | PB2/BOOT1 | 25 | PA14/SWCLK | 35 | PA15 |
| 6 | PB0 | 16 | NRST | 26 | PB3 | 36 | PB4 |
| 7 | PA7 | 17 | PA6 | 27 | PB5 | 37 | PB6 |
| 8 | PA5 | 18 | PA4 | 28 | PB7 | 38 | PB8 |
| 9 | PA3 | 19 | PA2 | 29 | PB9 | 39 | VERIFY ON MODULE |
| 10 | PA1 | 20 | PA0 | 30 | PC13 | 40 | VBAT |

Pad 39 is not legible enough in the listing photograph to release to copper.
It is deliberately unused. Confirm it by continuity measurement against the
STM32 package before a fabrication release.

## Slot identity straps

The photographed module does not expose both PC14 and PC15, so those pins must
not be used for slot identity. The carrier samples PB2 and PA7 at reset, before
initialising SPI. Both inputs have pull-ups; a fitted 0 Ohm link codes a zero by
connecting the corresponding input to GND.

| Slot | PB2 strap | PA7 strap | Firmware role |
| --- | --- | --- | --- |
| S1 | open | open | MASTER |
| S2 | fitted | open | SLAVE 1 |
| S3 | open | fitted | SLAVE 2 |
| S4 | fitted | fitted | SLAVE 3 |

PA7 is reused as CAP1188 SPI MOSI only in S1. S2-S4 never initialise the
CAP1188 bus, so their PA7 strap cannot conflict with an active peripheral.
PB2 is BOOT1 on the MCU; BOOT0 remains pulled low on the module for normal
Flash boot, therefore the carrier strap does not alter normal startup.

Before ordering boards, print the footprint at 1:1 and verify row spacing,
orientation, pad 1, 5 V, both GND pins and pad 39 on a physical module.
