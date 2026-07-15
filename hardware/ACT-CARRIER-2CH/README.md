# ACT-CARRIER-2CH v0.1

## Status

This is the electrical and layout design input for the first custom PCB. It is
**not yet released for fabrication**. The board accepts one removable
STM32F103C8T6 mini module and controls two 12 V linear actuators through two
bare VNH5019A-E H-bridges.

The same PCB is used for every slot. MASTER-only functions use unpopulated
headers or DNP parts on SLAVE boards. Board role is selected by two straps on
the carrier; firmware never depends on which physical STM32 board is inserted.

The current visual placement study is
[PRELIMINARY_PLACEMENT.svg](PRELIMINARY_PLACEMENT.svg). It is a component
placement guide, not a routed PCB or fabrication file.

## Board boundary

The PCB contains:

- socket footprint for the STM32F103C8T6 mini board;
- two VNH5019A-E channels and their current-sense circuits;
- motor connectors, 12 V motor input and 5 V logic input;
- 3.3 V auxiliary LDO for CAN, EEPROM, CAP1188 and VNH diagnostic pull-ups;
- slot straps, local UART headers and optional MASTER headers;
- test pads for 12 V, 5 V, 3.3 V, both CS signals and both diagnostic signals.

The cabinet, not this carrier, contains the MP1584 12 V to 5 V module, the
logic-branch fuse, reverse-polarity protection, SMBJ16A and cabinet-level
power-entry capacitors. Per-actuator 7.5 A fuses are also external so they can
be inspected and replaced without removing a PCB.

## Electrical design

### Power nets

| Net | Source | Use |
| --- | --- | --- |
| `MOTOR_12V_CH1` | Cabinet fuse F1 output | U1 `VBAT` and `VCC` pins only. |
| `MOTOR_12V_CH2` | Cabinet fuse F2 output | U2 `VBAT` and `VCC` pins only. |
| `MOTOR_GND` | Cabinet star ground | VNH `GNDA` and `GNDB`, motor-current return. |
| `LOGIC_5V` | Cabinet MP1584 output | STM32 mini board `5V`, carrier 3.3 V LDO input. |
| `LOGIC_3V3` | Carrier 5 V to 3.3 V LDO | CAN/CAP/EEPROM, DIAG pull-ups, sensor headers. |
| `SIGNAL_GND` | Joined to `MOTOR_GND` at board power entry | Logic and measurement reference. |

The 3.3 V auxiliary LDO deliberately powers external peripherals instead of
loading the small regulator on an unknown STM32 mini board. The STM32 board is
fed through its `5V` pin and generates 3.3 V only for itself.

### One VNH5019A-E channel

`U1` and `U2` use the ST MultiPowerSO-30 footprint and the exact pin mapping
from the VNH5019A-E data sheet:

| VNH pins | Connection |
| --- | --- |
| `3, 13, 23, slug 1 (VCC)` and `12 (VBAT)` | That channel's `MOTOR_12V_CHx`; VBAT and VCC are shorted because reverse-polarity protection is at the cabinet entry. |
| `26, 27, 28 (GNDA)` and `18, 19, 20 (GNDB)` | `MOTOR_GND`, joined immediately under the package. |
| `1, 25, 30, slug 2 (OUTA)` | Actuator terminal A. |
| `15, 16, 21, slug 3 (OUTB)` | Actuator terminal B. |
| `4 INA`, `10 INB`, `7 PWM` | STM32 output through 100 Ohm; every signal has a 10 kOhm pull-down at the VNH side. |
| `5 ENA/DIAGA`, `9 ENB/DIAGB` | Tied together, pulled to `LOGIC_3V3` by 4.7 kOhm and routed to the corresponding STM32 diagnostic input. |
| `6 CS_DIS` | 10 kOhm pull-down to `SIGNAL_GND`; current sensing stays enabled. |
| `8 CS` | Current-sense chain below. |
| `11 CP` | DNP test pad. It is not used because reverse-polarity protection is external to the carrier. |

For each bridge, fit `470 uF / 35 V low-ESR` plus `100 nF / 50 V X7R` directly
between its `MOTOR_12V_CHx` net and `MOTOR_GND`. The 470 uF value follows ST's basic
orientation of 500 uF per 10 A motor load; it is local energy storage and must
not be moved to the cabinet end of a long wire.

### Current sense

Each channel is implemented identically:

```text
VNH CS --+-- 1.00k 1% -- SIGNAL_GND
          |
          +-- 68k 1% -- SENSE_DIV -- 100k 1% -- SIGNAL_GND
                                |
                             1k series
                                |
                          PA0 or PA1
                                |
                            100nF to GND
```

`PA0` measures actuator 1 and `PA1` measures actuator 2. The known nominal
conversion is about 84.6 mV/A at the ADC. It is calibrated from a real current
measurement on the first assembled board before the 5 A software limit is used.

### STM32 signal assignment

| Channel / function | STM32 pin |
| --- | --- |
| Actuator 1: CS / PWM / INA / INB / DIAG | PA0 / PA8 / PB14 / PB15 / PB5 |
| Actuator 2: CS / PWM / INA / INB / DIAG | PA1 / PA9 / PB3 / PB4 / PB12 |
| Slot straps | PC14, PC15 |
| Slave upstream UART | PB7 RX, PB6 TX |
| Master UART links 1 / 2 / 3 | PB7/PB6, PA2/PA3, PB11/PB10 |
| CAN module header | PA11 RX, PA12 TX |
| CAP1188 header | PA4, PA5, PA6, PA7, PB9, PB13 |
| Reed header | PB0, PB1, PB8 |
| EEPROM chip select | PA15 |
| 12 V power-good input | PC13 |

PB3 and PB4 require JTAG disabled while retaining SWD, as the firmware already
does. The selected mini-board is documented in
[STM32_MINI_BOARD_VARIANT.md](STM32_MINI_BOARD_VARIANT.md). It must use its
CH340 UART configuration, not its native USB configuration: PA11/PA12 are
reserved for CAN. PC14/PC15 can be occupied by an LSE crystal on some variants.

## Connectors and optional population

| Ref | Part / function | Fit on |
| --- | --- | --- |
| J1 | `MOTOR_12V_CH1`, GND, `MOTOR_12V_CH2`, GND; 4-pin locking power input | Every carrier. Each 12 V pin comes after its own 7.5 A fuse. |
| J2, J3 | 2-pin, 5.08 mm-pitch actuator output, >=10 A per contact | Every carrier; selected terminal is documented in [TERMINAL_BLOCK_SELECTION.md](TERMINAL_BLOCK_SELECTION.md). |
| J4 | `LOGIC_5V`, `SIGNAL_GND`, 2-pin locking input | Every carrier |
| J5 | SWD: 3.3 V, SWDIO, SWCLK, GND, NRST | Every carrier |
| J6 | Upstream UART: TX, RX, GND, 3.3 V reference | Every carrier |
| J7/J8/J9 | Downstream UART 1/2/3 | MASTER only |
| J10 | SN65HVD230 module: 3V3, GND, CTX, CRX, CANH, CANL | MASTER only |
| J11 | CAP1188: 3V3, GND, CS, SCK, MISO, MOSI, RST, IRQ | MASTER only |
| J12 | Reeds: 3.3 V, GND, REED1, REED2, REED3 | MASTER only |
| U3 | 25LC256 EEPROM and its pull-ups | MASTER only |
| U4 | 12 V power-good comparator | MASTER only |

## PCB stack-up and placement rules

1. Four layers; 2 oz outer copper, 1 oz inner copper; FR-4 1.6 mm.
2. Layer 2 is an uninterrupted `MOTOR_GND` plane except for a controlled logic
   island near the STM32 socket. Layer 3 carries `MOTOR_12V` and low-current
   routing.
3. Put U1/U2 at the actuator-connector edge. Each exposed slug has a large
   copper island with dense thermal via arrays to layers 2 and 3.
4. Keep the motor-current loop: VNH VCC - bridge - OUTA/OUTB - actuator cable -
   return - VNH GND as short and wide as possible. No signal trace may cross it.
5. Place the 470 uF capacitor and 100 nF capacitor beside their VNH power pins,
   not beside J1.
6. Keep CS divider, PA0/PA1 and their 100 nF capacitors beside the STM32 socket
   and away from OUTA/OUTB and PWM routes.
7. Use no thermal relief on VNH power pads or motor connector pads. Use at least
   4 mm copper width for a 5 A outer-layer path, wider wherever space permits.
8. Maintain at least 3 mm clearance between motor copper and low-voltage logic
   copper; use a grounded copper guard where it improves noise immunity.
9. No copper pours under the CAP1188 connector or its electrode-cable exit.

## Fabrication gate

Before generating Gerbers, complete all four checks:

1. Verify one physical STM32 mini board against the documented 2x15 footprint,
   including continuity of PA9/PA10, PC14 and PC15 to its USB/LSE circuitry.
2. Implement the ST MultiPowerSO-30 recommended land pattern exactly, verify it
   in KiCad against the data sheet, then inspect solder wetting and thermal-pad
   voiding on the first assembled prototype.
3. Obtain the selected 5.08 mm actuator-output terminal and confirm pin diameter
   and body outline against the carrier footprint.
4. Review the resulting KiCad schematic with ERC, then check the 3D/1:1 print
   of connector and module placement before ordering boards.

The authoritative source for VNH5019 pin use, current-sense behavior, input
thresholds and thermal layout is the [ST VNH5019A-E data sheet](https://www.st.com/resource/en/datasheet/vnh5019a-e.pdf).
