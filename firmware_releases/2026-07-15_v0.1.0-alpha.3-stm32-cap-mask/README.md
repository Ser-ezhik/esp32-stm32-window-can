# STM32 universal node v0.1.0-alpha.3

This release adds persistent per-cabinet CAP1188 channel configuration.

- Any subset of CS1...CS8 can be enabled.
- Disabled channels cannot trigger a safety-edge stop.
- Saving a mask updates the CAP1188 enable and interrupt registers and forces
  recalibration of the enabled channels.
- CAP1188 noise status is reported to ESP32 over CAN.
- RESET remains active high and is held inactive by the board's 10 kOhm
  pull-down.

The same binary is used in every STM32 slot. The hardware slot straps select
MASTER or SLAVE role at boot.
