# STM32F103RCT6 pin map

The controller uses the same CAN/UART protocol and universal cabinet
configuration model as the other STM32 nodes. Four motor channels are handled
locally by one LQFP64 MCU.

This is a separate compile-time hardware target of the universal source. It is
not pin-compatible with the compiled F103C8 two-channel target.

| Function | STM32 pin |
| --- | --- |
| VNH1 current | PA0 / ADC1_IN0 |
| VNH2 current | PA1 / ADC1_IN1 |
| VNH3 current | PA2 / ADC1_IN2 |
| VNH4 current | PA3 / ADC1_IN3 |
| CAP1188 CS | PA4 |
| CAP1188 SCK | PA5 / SPI1_SCK |
| CAP1188 MISO | PA6 / SPI1_MISO |
| CAP1188 MOSI | PA7 / SPI1_MOSI |
| VNH1 PWM | PA8 / TIM1_CH1 |
| VNH2 PWM | PA9 / TIM1_CH2 |
| VNH3 PWM | PA10 / TIM1_CH3 |
| VNH4 PWM | PA11 / TIM1_CH4 |
| SWDIO | PA13 |
| SWCLK | PA14 |
| VNH1 INA / INB | PB0 / PB1 |
| VNH2 INA / INB | PB10 / PB11 |
| VNH3 INA / INB | PB12 / PB13 |
| VNH4 INA / INB | PB14 / PB15 |
| CAN RX / TX | PB8 / PB9, CAN remap |
| Reed open | PC0 |
| Reed closed | PC1 |
| Reed in-place | PC2 |
| Power-good | PC3 |
| EEPROM CS | PC4 |
| CAP1188 IRQ | PC5 |
| VNH diagnostics 1..4 | PC6 / PC7 / PC8 / PC9 |
| CAP1188 reset | PC10 |
| HSE crystal | PD0 / PD1 |

BOOT0 and BOOT1 have dedicated 10 kohm pull-down resistors. SWD remains
available for programming and recovery.

The F103 CAN peripheral must use the PB8/PB9 remap. PA11 remains available as
TIM1_CH4 for actuator 4 PWM. CAP1188 and the 25LC256 share SPI1, with separate
chip-select signals on PA4 and PC4.
