# ESP32 + STM32 window and door controller

New hardware generation of the original `esp32-rp2040-window-rs485` project.
The legacy source and all historic firmware releases remain in Git history and
under the `legacy-rp2040-import` tag. New releases never replace previous binaries.

## Target architecture

- ESP32-S3: CC1101 433 MHz radio, Wi-Fi, web UI, configuration backup and CAN coordinator.
- One cabinet per physical window or door.
- One universal STM32F103C8T6 master in each cabinet: two VNH2SP30 channels, CAN,
  CAP1188 over 4-wire SPI, three D-M9 position sensors and up to three local UART slaves.
- Up to three identical STM32 boards as local slaves, two VNH2SP30 channels per board.
- One firmware image for every STM32 board. `SLOT_ID` pins on the cabinet carrier select
  master/slave role, so a pre-flashed spare module can replace any controller.
- Cabinet identity is stored in a 25LCxx SPI EEPROM on the non-removable carrier board.

## Current development status

`0.1.0-alpha.1` contains the first buildable universal STM32 firmware:

- hardware bxCAN at 500 kbit/s;
- three hardware UART links at 250 kbit/s with CRC16 frames;
- VNH2SP30 PWM, direction, current sense and diagnostic monitoring;
- CAP1188 4-wire SPI driver, no I2C;
- three active-low D-M9N inputs;
- current disappearance end-stop detection;
- overcurrent, no-current, timeout, edge and communication fail-safe states;
- per-direction full-stroke calibration data and PWM equalization;
- carrier provisioning/discovery protocol;
- watchdog and safe outputs at boot.

ESP32 CAN coordinator and the object-based web interface are under active development.

## Build STM32 firmware

Install Arduino CLI and the official STM32 core, then run:

```powershell
arduino-cli compile `
  --fqbn "STMicroelectronics:stm32:GenF1:pnum=GENERIC_F103C8TX,xserial=none,usb=none,opt=oslto,dbg=none,rtlib=nano" `
  --libraries libraries `
  --export-binaries `
  ArduinoIDE\STM32_Universal_Actuator_Node
```

The project deliberately targets the real 64 KiB capacity of STM32F103C8T6 and
does not rely on unofficial 128 KiB clone behaviour.

## Documentation

- `docs/HARDWARE_ARCHITECTURE.md`
- `docs/CAN_PROTOCOL.md`
- `docs/SAFETY_AND_RECOVERY.md`

This is safety-related motion-control software. Test with disconnected mechanics
and current-limited power before connecting a door or window.
