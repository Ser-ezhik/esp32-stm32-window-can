# ESP32-S3 coordinator v0.1.0-alpha.6 N16

Changes:

- Receives cabinet power-recovery event frames over CAN.
- Stores the 48-entry web event journal as a persistent NVS ring.
- Preserves journal entries across ESP32 power cycles and restarts.
- Persists journal clearing requested from the web interface.

Hardware target: ESP32-S3 with 16 MB DIO Flash, PSRAM disabled and the 3 MB
application partition. Use the merged image at address `0x00000000` for a full
first flash.

Build result:

- Flash: 1022033 bytes, 32 percent of the 3 MB application partition.
- RAM: 57936 bytes, 17 percent of 320 KB.
