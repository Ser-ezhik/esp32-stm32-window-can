# ESP32-S3 CAN coordinator v0.1.0-alpha.4 N16R8

Hardware-specific release for the tested ESP32-S3 on COM7.

- Detected chip: ESP32-S3 QFN56 revision 0.2.
- Flash: 16 MB quad interface, DIO 80 MHz.
- PSRAM: 8 MB embedded OPI, intentionally disabled because this firmware does not require it.
- Partition scheme: 3 MB application plus 9.9 MB FATFS.
- Arduino-ESP32 core: 3.0.7.
- Serial startup diagnostics: 115200 baud.
- GPIO48 RGB control is disabled until the exact board LED circuit is confirmed.
- Web UI includes the Chrome-tested mobile overflow fix from alpha.3.

Use the merged binary at address `0x00000000` for a complete first flash.
This build supersedes the generic 4 MB alpha.3 image for N16R8 boards.

Validation on the target board: five consecutive cold starts completed with
`panic = 0`; the setup AP was available at `192.168.4.1` on every start.
