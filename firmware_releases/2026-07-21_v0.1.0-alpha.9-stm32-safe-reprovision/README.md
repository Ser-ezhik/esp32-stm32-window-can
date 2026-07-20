# STM32 universal node v0.1.0-alpha.9

This release adds confirmed and power-loss-safe carrier EEPROM reprovisioning.

- Carrier identity is stored as A/B records at `0x0000` and `0x0020`.
- The inactive record is written, read back and CRC-checked before activation.
- The previous valid identity remains usable if power is lost during a write.
- CAN provisioning returns success, invalid-request, busy or write/verify error.
- Reconfiguration is rejected while actuators are moving or calibrating.
- Firmware build reported during discovery is `9`.

Use this release together with ESP32 master `v0.1.0-alpha.8` or newer.

Build result: 24,028 bytes Flash (36%), 3,508 bytes static RAM (17%).

