# UNIVERSAL-2CH schematic and firmware audit

Audit target: the routed PCB, generated flat/multisheet schematics, and
`STM32_Universal_Actuator_Node`.

## Functional socket mapping

| Function | STM32 pin | MOD1 pad | PCB net |
|---|---:|---:|---|
| Current 1 / 2 | PA0 / PA1 | 20 / 10 | CH1/2_CURRENT_ADC |
| PWM 1 / 2 | PA8 / PA9 | 22 / 32 | CH1/2_PWM_MCU |
| INA 1 / 2 | PB14 / PB3 | 2 / 26 | CH1/2_INA_MCU |
| INB 1 / 2 | PB15 / PB4 | 12 / 36 | CH1/2_INB_MCU |
| DIAG 1 / 2 | PB5 / PB12 | 27 / 3 | CH1/2_DIAG |
| Reeds | PB0 / PB1 / PB8 | 6 / 5 / 38 | OPEN / CLOSED / IN_PLACE |
| CAP1188 CS / IRQ / RESET | PA4 / PB13 / PB9 | 18 / 13 / 29 | CAP_CS / IRQ / RESET |
| SPI SCK / MISO / MOSI | PA5 / PA6 / PA7 | 8 / 17 / 7 | CAP_SCK / MISO / MOSI |
| Carrier EEPROM CS | PA15 | 35 | EEPROM_CS |
| Power good | PC13 | 30 | POWER_GOOD |
| CAN RX / TX | PA11 / PA12 | 33 / 24 | S1_CAN_RX / S1_CAN_TX |
| SWDIO / SWCLK / NRST | PA13 / PA14 / NRST | 34 / 25 / 16 | service nets |

PA15, PB3, and PB4 are released from JTAG at startup with
`__HAL_AFIO_REMAP_SWJ_NOJTAG()` while SWD remains available.

The VNH5019A-E current-sense baseline is 5.7 mA per ADC count for the fitted
1 kOhm sense resistor and 12-bit 3.3 V ADC. The firmware default is 57/10.
Each assembled channel still requires a measured calibration under its real
mechanical load.
