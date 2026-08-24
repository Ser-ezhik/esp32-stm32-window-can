# STM32 Universal Actuator Node v0.1.0-alpha.14

Target: STM32F103C8T6, two VNH5019A-E actuator channels.

Changes from alpha.12:

- limits CAN receive processing to 20 frames per loop pass;
- limits each UART receive link to 10 frames per loop pass;
- rejects unsupported command values before they affect the heartbeat;
- validates fault and object-type values received from other controllers;
- writes the internal configuration with CRC, read-back comparison and up to
  three attempts;
- stops motion and latches `ConfigStorage` when configuration storage cannot be
  verified;
- keeps the existing EEPROM layout and alpha.12 calibration data compatible.

Build target:

`STMicroelectronics:stm32:GenF1:pnum=GENERIC_F103C8TX,xserial=none,usb=none,opt=oslto,dbg=none,rtlib=nano`

Bench-test with current-limited motor power before connecting mechanics.
