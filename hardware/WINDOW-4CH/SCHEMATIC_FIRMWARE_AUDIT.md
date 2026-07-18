# WINDOW-4CH schematic and firmware audit

Audit target: routed `WINDOW-4CH.kicad_pcb`, generated flat and multisheet
schematics, `STM32_Universal_Actuator_Node` v0.1.0-alpha.8 and
`ESP32_CC1101_CAN_Master` v0.1.0-alpha.6.

## Result

The schematic-to-PCB verifier found exactly 138 component references, 447
connected numbered pads and 60 intentionally blank pads in both representations.
PCB DRC reports zero violations and zero unconnected items. Schematic ERC
reports zero errors. Warnings are isolated reserve labels on the universal
STM32 pinout and do not represent PCB opens.

## Firmware pin agreement

| Function | Firmware pin | WINDOW-4CH net | Result |
| --- | --- | --- | --- |
| Local current 1/2 | PA0 / PA1 | odd/even `CHx_CURRENT_ADC` | OK |
| Local PWM 1/2 | PA8 / PA9 | odd/even `CHx_PWM_MCU` | OK |
| Local INA 1/2 | PB14 / PB3 | odd/even `CHx_INA_MCU` | OK |
| Local INB 1/2 | PB15 / PB4 | odd/even `CHx_INB_MCU` | OK |
| Local diagnostic 1/2 | PB5 / PB12 | odd/even `CHx_DIAG` | OK |
| Slot identity | PB2 / PA7 | S1/S2 carrier straps | OK |
| Reeds | PB0 / PB1 / PB8 | open / closed / in-place on S1 | OK |
| CAP1188 SPI | PA4 / PA5 / PA6 / PA7 | CS / SCK / MISO / MOSI on S1 | OK |
| CAP1188 control | PB13 / PB9 | IRQ / RESET on S1 | OK |
| Carrier EEPROM | PA15 plus shared SPI | `EEPROM_CS` | OK |
| STM32 CAN | PA11 / PA12 | CAN1 CRX / CTX on S1 | OK |
| S1 to S2 UART | PB7 / PB6 | S2 PB6 / PB7, crossed RX/TX | OK |
| Logic power monitor | PC13 | U270 open-drain `POWER_GOOD` | OK |

Each STM32 firmware instance controls exactly two local actuators. With S1 as
MASTER and S2 as slot-1 SLAVE, telemetry indices 0..3 and all four calibration
records are supported without a board-specific firmware build.

## Configuration finding

The protocol and STM32 carrier identity accept `ObjectType::Window` with
`slaveCount = 1`. The ESP32 runtime also supports `actuatorCount = 4`, but its
current factory default object table still defines the existing window as two
actuators with no slave. The WINDOW-4CH cabinet must therefore be provisioned
with slave count 1 and represented in the ESP32 object table with actuator
count 4. This is a configuration requirement, not a PCB pin mismatch.

CAP1188 is physically present on S1. Use enabled mask `0x07` for three sensors
or `0x0F` when the spare fourth input is fitted.

## Prototype checks still required

- Calibrate `CURRENT_MA_PER_ADC_COUNT_NUM/DEN` with a populated VNH5019 channel.
- Confirm the new 5 A default trip threshold with a calibrated current source
  before commissioning the 2.5 A actuators.
- Confirm UART reliability at 250 kbit/s over the actual short cabinet wiring.
- Verify the C280 power-fail write margin on the assembled carrier.
