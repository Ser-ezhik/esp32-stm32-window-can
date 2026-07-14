# STM32 universal controller v0.1.0-alpha.2

Bench-test release for every master and slave STM32F103C8T6 module.

- Target: genuine STM32F103C8T6, 64 KiB Flash.
- Flash usage: 23708 bytes (36%).
- Static RAM usage: 3476 bytes (16%).
- Adds calibration reset and reliable calibrated-state telemetry.
- Adds per-input D-M9N/D-M9P polarity from the cabinet EEPROM.
- `.bin` is flashed at address `0x08000000`; `.hex` contains its own address.

Do not connect mechanics during first power-on. Verify current-sense scaling,
VNH2SP30 diagnostic polarity, slot straps and all stop paths on the bench.
