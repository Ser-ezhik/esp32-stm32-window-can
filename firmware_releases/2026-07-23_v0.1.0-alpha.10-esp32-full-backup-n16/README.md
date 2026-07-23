# ESP32 CAN master v0.1.0-alpha.10 N16

This release adds complete system backup export and import.

- The web settings page downloads one versioned `.wbackup` file.
- The file contains Wi-Fi and system settings, all CAN objects, reed polarity,
  CAP1188 masks, 433 MHz remotes and every carrier EEPROM backup.
- A CRC32 protects the complete payload.
- Import validates the format, size, object table, remotes and every EEPROM
  backup record before changing NVS.
- Restore is rejected while actuators are moving, calibrating or an EEPROM
  provisioning transaction is active.
- ESP32 restarts after a successful restore.
- The event journal is not included because it is operational history rather
  than system configuration.

Use STM32 universal firmware v0.1.0-alpha.10.

Build result: 1,037,601 bytes Flash (32%), 69,080 bytes static RAM (21%).

