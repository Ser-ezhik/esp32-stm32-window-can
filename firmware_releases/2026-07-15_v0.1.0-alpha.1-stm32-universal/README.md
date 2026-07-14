# STM32 universal controller v0.1.0-alpha.1

First buildable firmware for bench testing only.

- Target: genuine STM32F103C8T6, 64 KiB Flash.
- Arduino FQBN: `GENERIC_F103C8TX`, LTO, no USB, no generic Serial.
- Flash usage: 23464 bytes (35%).
- Static RAM usage: 3472 bytes (16%).
- `.bin` is intended for SWD/STM32CubeProgrammer at address `0x08000000`.
- `.hex` includes the target address and can be opened directly in STM32CubeProgrammer.

Do not connect the mechanics during first power-on. Current-sense scaling and VNH
diagnostic polarity must be verified on the exact carrier and VNH2SP30 modules.
