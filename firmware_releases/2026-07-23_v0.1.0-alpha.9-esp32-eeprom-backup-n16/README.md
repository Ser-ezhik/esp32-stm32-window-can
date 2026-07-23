# ESP32 CAN master v0.1.0-alpha.9 N16

This release adds carrier EEPROM backup and replacement-board restoration.

- A CRC-protected backup is stored in ESP32 NVS for every cabinet.
- Backups contain cabinet identity, name/type, actuator and slave count,
  D-M9 polarity and the CAP1188 enabled-channel mask.
- CAN discovery offers `Restore` for an unconfigured replacement MASTER.
- The operator selects the old cabinet number in the web interface.
- Restore is blocked while the old cabinet is online, the CAN number is in use
  or the selected target is already configured.
- The ESP32 object is rebound only after STM32 write/read/CRC confirmation.
- The historical power-loss record and per-actuator speed calibration are not
  copied to replacement hardware.

STM32 universal firmware build 9 or newer is required for EEPROM restoration.
Build 10 is recommended because it also enables all PCB-assigned JTAG pins.

Build result: 1,033,281 bytes Flash (32%), 61,392 bytes static RAM (18%).

