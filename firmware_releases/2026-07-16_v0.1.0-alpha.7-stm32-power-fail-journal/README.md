# STM32 Universal Actuator Node v0.1.0-alpha.7

Changes:

- Detects a falling `POWER_GOOD` signal on MASTER PC13.
- Stops local outputs and sends STOP to populated SLAVE slots.
- Stores one CRC-protected outage record in the held carrier EEPROM.
- Reports `PowerRecovered` over CAN after restart and then acknowledges the
  saved record.

Build result:

- Flash: 23832 bytes, 36 percent of STM32F103C8T6 64 KB target.
- RAM: 3508 bytes, 17 percent of 20 KB target.
