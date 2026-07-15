# BOM v0.1 - 22 actuator system

## Scope and assumptions

This bill of materials covers these objects:

| Object | Objects | Actuators per object | Total actuators | STM32 boards |
| --- | ---: | ---: | ---: | ---: |
| Double door | 1 | 8 | 8 | 4 |
| Single door | 3 | 4 | 12 | 6 |
| Window | 1 | 2 | 2 | 1 |
| **Total** | **5** | - | **22** | **11** |

One STM32 controls two VNH2SP30 channels. Only the MASTER STM32 of each cabinet is physically connected to CAN. Other STM32 boards use short, point-to-point 3.3 V UART links to the MASTER.

This is a low-voltage 12 V DC design. Do not connect mains voltage to any board, signal connector or ESP32 input.

## Main modules

| Item | Quantity | Notes |
| --- | ---: | --- |
| ESP32-S3 N16R8 | 1 | Central controller, installed in the double-door cabinet. |
| CC1101, 433 MHz, 3.3 V module | 1 | Radio receiver for existing remotes. Include an antenna matched for 433 MHz. |
| STM32F103C8T6 mini board | 11 | Same firmware on every board. Buy 1 spare. |
| Carrier PCB for one STM32 plus two actuator channels | 11 | The carrier, not the removable STM32 board, holds slot straps and configuration EEPROM. |
| VNH2SP30 module | 22 | One module per actuator. Buy at least 2 identical spares. Provide airflow or metal mounting if the actual current requires it. |
| CAP1188, SPI-capable breakout | 4 | One per door: double door plus three single doors. |
| CAP1188, optional | 1 | Add for the window only when it also needs an anti-pinch touch perimeter. |
| D-M9N / D-M9P reed sensor | 15 | Three per physical object, including the window: OPEN, CLOSED and door/leaf position. If the window does not need the third state, populate 2 instead. |
| 25LC256-I/P or 25LC256-I/SN SPI EEPROM | 11 | One on every carrier so a replacement STM32 remains interchangeable. |
| MCP2562-E/SN CAN transceiver | 5 | One on the MASTER carrier in each physical cabinet. SLAVE STM32 boards use only local UART and do not need a CAN transceiver. |
| MCP2562-E/SN CAN transceiver | 1 | ESP32 CAN interface. |
| 12 V to 5 V DC/DC converter, regulated, 3 A minimum | 5 | One in each cabinet. Use the same model everywhere. The double-door cabinet also powers the ESP32. |
| 12 V actuator power supply | 5 or 1 central supply | Size from actual actuator current as described below. Separate cabinet supplies are preferred for easier fault isolation. |
| SWD programmer, ST-Link V2 or V3 | 1 | For STM32 commissioning and recovery. |

The original VNH2SP30 is obsolete. The modules must be electrically tested before installation because cheap breakouts differ, especially at the CS current-sense output. ST describes the VNH2SP30 as a protected H-bridge with current sense and PWM operation up to 20 kHz; it does not make a random breakout electrically identical to another one. [ST product page](https://www.st.com/en/automotive-analog-and-power/vnh2sp30-e.html)

## Cabinet allocation

| Cabinet | STM32 MASTER | STM32 SLAVE | VNH2SP30 | CAP1188 | Reeds | Local UART links |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Double door | 1 | 3 | 8 | 1 | 3 | 3 |
| Single door 1 | 1 | 1 | 4 | 1 | 3 | 1 |
| Single door 2 | 1 | 1 | 4 | 1 | 3 | 1 |
| Single door 3 | 1 | 1 | 4 | 1 | 3 | 1 |
| Window | 1 | 0 | 2 | 0 | 3 | 0 |
| **Total** | **5** | **6** | **22** | **4** | **15** | **6** |

## One universal two-actuator carrier: mandatory passive parts

Quantities in this table are **per carrier**. Multiply by 11 for the total purchase quantity shown in the final column.

| Reference / purpose | Component and nominal | Per carrier | Total for 11 |
| --- | --- | ---: | ---: |
| PWM, INA and INB safe state | 10 kOhm, 1%, 0.125 W pull-down | 6 | 66 |
| PWM, INA and INB series protection | 100 Ohm, 0.125 W | 6 | 66 |
| VNH DIAG pull-up | 4.7 kOhm, 1%, 0.125 W to **3.3 V** | 2 | 22 |
| VNH supply bulk capacitor | 470 uF, 25 V, low-ESR electrolytic, >=105 C | 2 | 22 |
| VNH local ceramic capacitor | 100 nF, 50 V, X7R | 2 | 22 |
| VNH CS ADC filter | 1 kOhm series plus 100 nF, 16 V, X7R at PA0/PA1 | 2 + 2 | 22 + 22 |
| VNH CS divider, **only when CS can reach 5 V** | 10 kOhm upper + 20 kOhm lower, both 1% | 2 + 2 | 22 + 22 |
| EEPROM VCC decoupling | 100 nF, 16 V, X7R | 1 | 11 |
| EEPROM /WP and /HOLD | 10 kOhm, 1%, 0.125 W pull-up to 3.3 V | 2 | 22 |
| EEPROM CS default inactive | 10 kOhm, 1%, 0.125 W pull-up to 3.3 V | 1 | 11 |
| 12 V power-good comparator | TLV3012 or equivalent open-drain comparator with reference | 1 | 11 |
| 12 V monitor divider | 100 kOhm upper + 15 kOhm lower, both 1%, 0.125 W | 1 + 1 | 11 + 11 |
| Comparator input filter | 100 nF, 50 V, X7R | 1 | 11 |
| Comparator hysteresis | 1 MOhm, 1%, 0.125 W | 1 | 11 |
| PC13 pull-up | 10 kOhm, 1%, 0.125 W to 3.3 V | 1 | 11 |
| Carrier 3.3 V bulk decoupling | 10 uF, 10 V, X5R/X7R | 2 | 22 |
| Carrier 3.3 V local decoupling | 100 nF, 16 V, X7R | 4 | 44 |

The `100 kOhm / 15 kOhm` divider gives an approximately 9.5 V 12-V-power threshold with a 1.242 V reference. The 1 MOhm feedback resistor adds hysteresis. Confirm its exact trip and release voltage on the finished carrier before enabling actuator motion.

## MASTER-carrier CAN parts only

These parts are fitted only to the five MASTER carriers. A failed MASTER STM32 is replaced by inserting the same spare STM32 board into its existing MASTER carrier, so the spare board itself does not need a CAN transceiver.

| Purpose | Component and nominal | Per MASTER carrier | Total |
| --- | --- | ---: | ---: |
| CAN transceiver | MCP2562-E/SN | 1 | 5 |
| CAN transceiver 5 V decoupling | 100 nF, 16 V, X7R + 1 uF, 16 V, X7R | 1 + 1 | 5 + 5 |
| CAN transceiver 3.3 VIO decoupling | 100 nF, 16 V, X7R | 1 | 5 |
| MCP2562 STBY normal-mode pull-down | 10 kOhm, 1%, 0.125 W | 1 | 5 |
| CAN TX series resistor | 47 Ohm, 0.125 W | 1 | 5 |

### VNH2SP30 CS warning

Never connect an unknown module's `CS` pin directly to PA0 or PA1. First measure it with the actuator at maximum expected current.

- If the module already provides a 0 to 3.3 V analog output, install only the 1 kOhm and 100 nF filter.
- If it can reach 5 V, use the listed `10 kOhm / 20 kOhm` divider followed by the filter.
- If it is the raw VNH current-source output, its load resistor must be selected from that module's exact schematic and the VNH datasheet. Do not fit a guessed resistor.

After this measurement, calibrate `CURRENT_MA_PER_ADC_COUNT_NUM` in the STM32 firmware and set the per-actuator over-current limit in the cabinet configuration.

## Master-only sensor and UART parts

| Purpose | Component and nominal | Quantity for system |
| --- | --- | ---: |
| CAP1188 INT pull-up | 10 kOhm, 1%, 0.125 W to 3.3 V | 4 |
| CAP1188 RESET pull-up | 10 kOhm, 1%, 0.125 W to 3.3 V | 4 |
| CAP1188 supply bypass near connector | 100 nF, 16 V, X7R + 4.7 uF, 10 V, X5R | 4 + 4 |
| Reed input pull resistor | 4.7 kOhm, 1%, 0.125 W; fit to 3.3 V for D-M9N or GND for D-M9P | 15 |
| Reed input series resistor | 1 kOhm, 0.125 W | 15 |
| Reed input noise filter | 100 nF, 16 V, X7R at the STM32 connector | 15 |
| UART TX series resistor | 100 Ohm, 0.125 W, one at each end of each link | 12 |
| SLOT_ID low strap | 10 kOhm, 1%, 0.125 W to GND | 7 |

For every reed location fit **one**, not both, 4.7 kOhm pull directions. D-M9N and D-M9P polarity is then selected in the cabinet configuration. Use screened or twisted sensor cable when it leaves the cabinet.

## CAN bus and cable entry

| Item | Quantity | Specification |
| --- | ---: | --- |
| CAN connector, 4-pin | 6 | CANH, CANL, CAN_GND, shield/drain. One at ESP32 and one at each MASTER cabinet connection. |
| CAN termination jumper footprint | 6 | Fit 120 Ohm, 0.25 W only at the two physical ends of the complete cable. Buy 6 resistors, populate 2. |
| CAN common-mode choke | 5 | One at each cabinet cable entry, for example a 51 Ohm common-mode impedance class part suitable for CAN. |
| Dual CAN TVS protector | 5 | Automotive CAN-rated dual-line protector, for example SM24CANB class, at each cabinet cable entry. |
| CAN cable | As measured | 120 Ohm twisted pair plus reference ground; use shielded cable in electrically noisy routes. |

The system total is **six CAN transceivers**: five on MASTER carriers and one at the ESP32. The MCP2562 has a 5 V supply and a separate 1.8 to 5 V `VIO` digital I/O supply, so it connects directly to 3.3 V STM32/ESP32 logic. It also disconnects unpowered nodes from the bus, which is useful during cabinet service. [MCP2562 product data](https://www.microchip.com/en-us/product/MCP2562)

## 12 V cabinet power entry and protection

| Item | Quantity | Specification |
| --- | ---: | --- |
| Main cabinet fuse holder | 5 | DIN-rail or automotive blade type. |
| Main cabinet fuse | 5 | Select from actual simultaneous actuator current; see rule below. |
| Per-actuator fuse holder | 22 | One per VNH2SP30 motor supply. |
| Per-actuator fuse | 22 | Select from the exact actuator data and wire cross-section; see rule below. |
| Reverse-polarity MOSFET | 5 | P-channel, >=40 V, low Rds(on), current rating above cabinet peak; IRF4905 class or a proper ideal-diode controller solution. |
| Gate resistor / gate pull-up | 100 Ohm + 100 kOhm, 0.125 W | 5 + 5 |
| Gate-source zener | 12 V, 0.5 W | 5 |
| 12 V transient suppressor | SMBJ18A, 600 W, unidirectional | 5 |
| DC/DC input bulk capacitor | 470 uF, 25 V, low-ESR, >=105 C | 5 |
| DC/DC input ceramic | 1 uF, 50 V, X7R + 100 nF, 50 V, X7R | 5 + 5 |
| DC/DC output bulk capacitor | 220 uF, 10 V, low-ESR | 5 |
| DC/DC output ceramic | 10 uF, 10 V, X5R + 100 nF, 16 V, X7R | 5 + 5 |

Fuse values cannot be selected safely without the actuator datasheet or a measured stall-current test.

1. Measure each actuator's maximum normal running current and short startup peak at 12 V.
2. Choose each channel fuse around `1.25 x maximum normal current`, while staying below the safe current of the VNH module, the cable and its connectors.
3. Choose each cabinet main fuse for `1.25 x` the sum of channels that may move simultaneously.
4. Size the 12 V supply at least `1.3 x` that same simultaneous load. Do not size it from the average current only.

The current 8 A firmware default is only a commissioning placeholder, not a fuse rating.

## Enclosures, wiring and installation hardware

| Item | Quantity | Notes |
| --- | ---: | --- |
| IP-rated control cabinet | 5 | One per physical object. Choose size after heat and cable-entry layout. |
| DIN rail | 5 sets | For fuses, DC/DC, terminals and power distribution. |
| 12 V distribution terminal blocks | 5 sets | Separate motor positive distribution and star ground point. |
| 2-pin actuator terminal blocks | 22 | Rated above actuator maximum current. |
| 3-pin sensor terminals | 15 | 3.3 V, signal, GND. |
| 4-pin CAP1188 terminals | 4 | 3.3 V, GND, SPI/IRQ harness as required by the module. |
| 4-pin UART headers/cables | 6 | TX, RX, 3.3 V reference, GND. Keep inside cabinet and under 30 cm. |
| 2-pin CAN terminal blocks | 10 | IN/OUT at intermediate cabinets, plus CAN_GND/shield terminals. |
| Cable glands | As measured | Separate motor, sensor and CAN entries. |
| Motor cable | As measured | Cross-section selected from length and fuse rating. Do not use thin Dupont wire. |
| Ferrules, labels and heat-shrink | As needed | Label every actuator, sensor and CAN address. |
| 40 mm / 60 mm cabinet fan | As thermal test requires | Add when VNH module or DC/DC temperature exceeds its safe limit. |

## Commissioning spares

Buy these in addition to the calculated total:

| Item | Spare quantity |
| --- | ---: |
| STM32F103C8T6 board | 1 |
| VNH2SP30 module | 2 |
| CAN transceiver | 2 |
| 25LC256 EEPROM | 2 |
| CAP1188 module | 1 |
| 12 V to 5 V DC/DC | 1 |
| Assorted 100 nF / 1 uF / 10 uF capacitors and 1 kOhm / 4.7 kOhm / 10 kOhm resistors | 20% above calculated count |
