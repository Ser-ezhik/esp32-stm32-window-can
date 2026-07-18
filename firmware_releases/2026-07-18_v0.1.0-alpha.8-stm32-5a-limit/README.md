# STM32 universal actuator node v0.1.0-alpha.8

This release keeps the universal MASTER/SLAVE firmware and changes the default
software overcurrent threshold from 8 A to 5 A for the measured 2.5 A linear
actuators with a two-times design margin.

- Target: generic STM32F103C8Tx, 64 KiB flash profile.
- Binary size: 24120 bytes.
- Flash usage: 36%.
- Static RAM usage: 3508 bytes (17%).
- Source: `ArduinoIDE/STM32_Universal_Actuator_Node`.

The current-sense conversion must still be calibrated on the populated
VNH5019 carrier before this threshold is treated as an accurate 5 A trip point.
