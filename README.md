# ESP32 + STM32 window and door controller

New hardware generation of the original `esp32-rp2040-window-rs485` project.
The legacy source and all historic firmware releases remain in Git history and
under the `legacy-rp2040-import` tag. New releases never replace previous binaries.

## Target architecture

- ESP32-S3: CC1101 433 MHz radio, Wi-Fi, web UI, configuration backup and CAN coordinator.
- One cabinet per physical window or door.
- One universal STM32F103C8T6 master in each cabinet: two VNH5019A-E channels, CAN,
  CAP1188 over 4-wire SPI, three D-M9 position sensors and up to three local UART slaves.
- Up to three identical STM32 boards as local slaves, two VNH5019A-E channels per board.
- One firmware image for every STM32 board. `SLOT_ID` pins on the cabinet carrier select
  master/slave role, so a pre-flashed spare module can replace any controller.
- Cabinet identity is stored in a 25LCxx SPI EEPROM on the non-removable carrier board.

## Current development status

The current releases are STM32 `0.1.0-alpha.8` and ESP32-S3 `0.1.0-alpha.7`:

- hardware bxCAN at 500 kbit/s;
- three hardware UART links at 250 kbit/s with CRC16 frames;
- VNH5019A-E PWM, direction, current sense and diagnostic monitoring;
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

ESP32 `alpha.3` fixes mobile-width overflow found during Chrome testing. The
wide actuator table now scrolls inside its own container without widening the page.

ESP32 `alpha.4` targets the tested ESP32-S3 N16R8 module: 16 MB quad Flash,
PSRAM disabled (the firmware does not need it), and a 3 MB application partition. It also prints startup diagnostics
at 115200 baud. This hardware is verified with Arduino-ESP32 core `3.0.7`;
do not use core `3.3.8` for it because Wi-Fi startup is unstable on the tested board.
Generic 4 MB images remain archived under their original tags.

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
arduino-cli core install esp32:esp32@3.0.7
arduino-cli compile `
  --fqbn "esp32:esp32:esp32s3:FlashMode=dio,FlashSize=16M,PartitionScheme=app3M_fat9M_16MB,PSRAM=disabled" `
  --libraries libraries `
  --export-binaries ArduinoIDE\ESP32_CC1101_CAN_Master
```

The current web interface intentionally exposes only full open, full close and
stop. A partial ventilation command will be added only after its position rule
or dedicated sensor is defined and bench-tested.

## Documentation

- `docs/HARDWARE_ARCHITECTURE.md`
- `docs/CAN_PROTOCOL.md`
- `docs/SAFETY_AND_RECOVERY.md`
- `docs/BOM_v0.1.md`
- `hardware/DOOR-8CH/README.md`
- `hardware/WINDOW-4CH/README.md`

This is safety-related motion-control software. Test with disconnected mechanics
and current-limited power before connecting a door or window.
