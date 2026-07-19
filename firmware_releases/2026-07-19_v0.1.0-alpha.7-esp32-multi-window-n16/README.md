# ESP32-S3 CAN coordinator v0.1.0-alpha.7 N16

This release preserves the existing two-actuator window and adds discovered
CAN cabinets as separate objects instead of replacing a fixed object profile.

During provisioning the web UI now asks for:

- cabinet name and CAN id;
- object type;
- 2, 4, 6 or 8 actuators;
- D-M9 sensor polarity mask.

The coordinator derives the number of local STM32 SLAVEs from the actuator
count: 0, 1, 2 or 3. Existing object records in ESP32 NVS are not reset by this
firmware update.

- Target: ESP32-S3 N16, 16 MB flash, DIO, PSRAM disabled.
- Application size: 1024032 bytes, 32% of the 3 MB application partition.
- Static RAM: 57936 bytes, 17%.
- Arduino-ESP32 core: 3.0.7.

Use the normal `.bin` for web OTA. Use `-merged.bin` only for a full USB/UART
flash starting at address `0x0000`.
