# DOOR-8CH schematic and firmware audit

Audit target: routed `DOOR-8CH.kicad_pcb`, generated principle schematics,
`STM32_Universal_Actuator_Node` v0.1.0-alpha.6 and
`ESP32_CC1101_CAN_Master` v0.1.0-alpha.5.

## Result

The generated flat and multisheet schematics contain all 230 PCB references,
all numbered pads and the same net labels as the routed PCB. KiCad ERC reports
zero errors. The two remaining warnings are intentionally isolated optional
nets: the ESP32 GPIO9 learn-button input and the unused S1 PA7 slot-ID pull-up.

## Firmware pin agreement

| Function | Firmware pin | PCB connection | Result |
| --- | --- | --- | --- |
| Actuator current 1/2 | PA0 / PA1 | local odd/even `CHx_CURRENT_ADC` | OK |
| VNH PWM 1/2 | PA8 / PA9 | local odd/even `CHx_PWM_MCU` | OK |
| VNH INA 1/2 | PB14 / PB3 | local odd/even `CHx_INA_MCU` | OK |
| VNH INB 1/2 | PB15 / PB4 | local odd/even `CHx_INB_MCU` | OK |
| VNH diagnostic 1/2 | PB5 / PB12 | local odd/even `CHx_DIAG` | OK |
| Slot identity | PB2 / PA7 | S1-S4 carrier straps | OK |
| Reeds A/B | PB0 / PB1 / PB8 | open / closed / in-place | OK |
| CAP1188 SPI | PA4 / PA5 / PA6 / PA7 | CS / SCK / MISO / MOSI | OK |
| CAP1188 control | PB13 / PB9 | IRQ / RESET | OK |
| Cabinet EEPROM | PA15 plus shared SPI | `EEPROM_CS` | OK |
| STM32 CAN | PA11 / PA12 | CAN1 CRX / CTX | OK |
| Master UART 1 | PB7 / PB6 | S2 RX / TX link | OK |
| Master UART 2 | PA3 / PA2 | S3 RX / TX link | OK |
| Master UART 3 | PB11 / PB10 | S4 RX / TX link | OK |
| ESP32 CC1101 SPI | GPIO10-13 | CS / MOSI / SCK / MISO | OK |
| ESP32 CC1101 data | GPIO4 / GPIO5 | GDO0 / GDO2 | OK |
| ESP32 CAN | GPIO38 / GPIO39 | CAN2 CRX / CTX | OK |
| Logic power monitor | PC13 | MOD1 pad 30 is not connected | **MISMATCH** |

## Required correction before fabrication

The STM32 firmware samples `POWER_GOOD` on PC13 and reports low-supply state,
but the current PCB has no `POWER_GOOD` net or comparator connected to MOD1 pad
30. Until the hardware monitor is added, PC13 remains high through the internal
pull-up, so low-supply telemetry is not real. Add the planned open-drain
power-good detector to PC13 or explicitly remove this function from firmware
and documentation before releasing Gerbers.

The current-sense scale in `config.h` is still marked for calibration. Its
conversion constant and protection thresholds must be measured on a populated
VNH5019 channel before field commissioning.
