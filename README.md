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

`0.1.0-alpha.2` contains buildable universal STM32 and ESP32-S3 firmware:

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
- ESP32-S3 CAN coordinator with CC1101 receiver and configuration stored in NVS;
- object-based web UI for up to 64 windows/doors, actuator telemetry, events and emergency stop;
- editable 433 MHz button assignments;
- separate open/close calibration, position-aware full-cycle calibration and calibration reset;
- per-input D-M9N/D-M9P polarity stored in the cabinet carrier EEPROM.

The `alpha.1` STM32 binaries and tag remain unchanged. `alpha.2` is a new release
because the CAN protocol gained a calibration-reset command.

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

## Build ESP32-S3 firmware

```powershell
powershell -ExecutionPolicy Bypass -File tools\embed-web.ps1
arduino-cli compile --fqbn "esp32:esp32:esp32s3" --libraries libraries `
  --export-binaries ArduinoIDE\ESP32_CC1101_CAN_Master
```

The current web interface intentionally exposes only full open, full close and
stop. A partial ventilation command will be added only after its position rule
or dedicated sensor is defined and bench-tested.

## Documentation

- `docs/HARDWARE_ARCHITECTURE.md`
- `docs/CAN_PROTOCOL.md`
- `docs/SAFETY_AND_RECOVERY.md`

This is safety-related motion-control software. Test with disconnected mechanics
and current-limited power before connecting a door or window.
