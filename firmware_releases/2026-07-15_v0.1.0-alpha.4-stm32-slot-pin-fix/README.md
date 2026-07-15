# STM32 universal node v0.1.0-alpha.4

This release corrects hardware slot identification for the photographed
MuLuoxing STM32F103C8T6 mini CH340 module.

- Slot ID0 moved from unavailable PC14 to exposed PB2.
- Slot ID1 moved from unavailable PC15 to exposed PA7.
- PA7 is sampled before SPI starts and is reused as CAP1188 MOSI only by S1.
- The same binary remains valid in every S1-S4 socket.

Required DOOR-8CH carrier straps:

| Slot | PB2 | PA7 | Role |
| --- | --- | --- | --- |
| S1 | pull-up | pull-up | MASTER |
| S2 | GND | pull-up | SLAVE 1 |
| S3 | pull-up | GND | SLAVE 2 |
| S4 | GND | GND | SLAVE 3 |

Do not use this build with the abandoned PC14/PC15 strap proposal.
