# STM32 universal actuator node, integrated 4-channel F103RC target

Dedicated firmware for `UNIVERSAL-4CH-F103RC-IC` with one soldered
STM32F103RCT6 and four local VNH5019A-E channels.

- CAN: 500 kbit/s on remapped PB8/PB9.
- PWM: PA8/PA9/PA10/PA11, TIM1 channels 1 through 4, 20 kHz.
- Current ADC: PA0/PA1/PA2/PA3, initial scale 5.7 mA/count.
- CAP1188 and 25LC256: shared SPI1 with PA4 and PC4 chip selects.
- Sensors: three protected reed inputs and three CAP1188 electrodes.
- Power-fail input: PC3; identity and power-loss record: external 25LC256.

The classic CAN protocol still represents actuators in groups of two. This
node therefore publishes channels 1-2 in actuator slot 0 and channels 3-4 in
slot 1. ESP32 provisioning must specify four actuators (`slaveCount = 1`), but
there is no physical UART slave on this board.

The target accepts `Window` and `SingleDoor`. It rejects `DoubleDoor` because
the PCB has only one set of three reed-switch inputs.

Build from the repository root:

```powershell
.\tools\build-stm32-4ch-f103rc.ps1
```

Do not flash the two-channel F103C8 binary onto this board.
