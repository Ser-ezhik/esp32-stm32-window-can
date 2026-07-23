# STM32 universal node v0.1.0-alpha.10

This release keeps SWD programming available and disables full JTAG before
initialising the application pins.

- PA15 is released for carrier EEPROM chip select.
- PB3 and PB4 are released for the second VNH5019 channel.
- Safe A/B carrier EEPROM provisioning from build 9 remains unchanged.
- The same binary is used for MASTER and every SLAVE slot.

Use this release with ESP32 master v0.1.0-alpha.9 or newer.

Build result: 24,092 bytes Flash (36%), 3,508 bytes static RAM (17%).

