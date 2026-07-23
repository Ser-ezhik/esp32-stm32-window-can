# STM32 Universal Actuator Node v0.1.0-alpha.12

- Sets the VNH5019A-E current-sense baseline to 5.7 mA per ADC count for the
  fitted 1 kOhm sense resistor and 3.3 V 12-bit ADC.
- Keeps the existing universal two-actuator firmware, CAP1188 event handling,
  carrier EEPROM, power-loss journal, CAN protocol, and JTAG-to-SWD remap.
- Verified against the routed UNIVERSAL-2CH carrier socket.

Each assembled VNH5019A-E channel still requires a measured current calibration
under its real load because the current-sense ratio has a wide tolerance.
