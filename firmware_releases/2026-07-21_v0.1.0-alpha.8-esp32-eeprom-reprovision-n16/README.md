# ESP32 CAN master v0.1.0-alpha.8 N16

This release adds web-controlled carrier EEPROM reconfiguration.

- Configured nodes show a `Перенастроить` action in CAN discovery.
- Cabinet ID, object name/type, actuator count and D-M9 polarity can be changed.
- A duplicate cabinet ID is rejected using both discovery and the ESP32 object table.
- The ESP32 object table is changed only after STM32 write/read/CRC confirmation.
- The old object entry is updated in place, preserving remote-control assignments.
- The current D-M9 polarity mask is retained in ESP32 NVS and prefilled in the UI.
- Busy, timeout, CAN send, incompatible STM32 and EEPROM verification errors are shown.
- STM32 firmware build `9` or newer is required for this operation.

For a two-actuator object select actuator count `2`; only S1/CH1-CH2 are enabled.

Build result: 1,031,309 bytes Flash (32%), 58,188 bytes static RAM (17%).

