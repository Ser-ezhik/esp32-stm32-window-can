# STM32 Universal Actuator Node v0.1.0-alpha.6

Changes:
- Uses carrier SPI EEPROM data for universal STM32 replacement.
- Passes reed polarity mask slices to slave STM32 boards over local UART config.
- Reconfigures slave reed inputs immediately after receiving configuration.

Build result:
- Flash: 24232 bytes, 36 percent of STM32F103C8T6 64 KB target.
- RAM: 3492 bytes, 17 percent of 20 KB target.
