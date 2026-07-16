# BOM v0.1 - 22 actuator system

## Scope and assumptions

This bill of materials covers these objects:

| Object | Objects | Actuators per object | Total actuators | STM32 boards |
| --- | ---: | ---: | ---: | ---: |
| Double door | 1 | 8 | 8 | 4 |
| Single door | 3 | 4 | 12 | 6 |
| Window | 1 | 2 | 2 | 1 |
| **Total** | **5** | - | **22** | **11** |

One STM32 controls two VNH5019A-E channels. Each physical object uses one universal DOOR-8CH PCB with up to four STM32/VNH two-channel slots. Only slot 1 (MASTER) is connected to CAN; UART connections to the other slots are internal PCB tracks, not external cables.

This is a low-voltage 12 V DC design. Do not connect mains voltage to any board, signal connector or ESP32 input.

## Design current basis

The measured maximum actuator current is 2.5 A. This design uses a two-times reserve,
therefore every actuator channel is designed and protected for **5 A**. VNH5019 carrier
thermal design nevertheless keeps copper and heatsinking margin for a 10 A continuous
channel, so 5 A operation is not at the edge of the board capability.

| Cabinet | Actuators moving together | Design current | Recommended 12 V supply | Main fuse |
| --- | ---: | ---: | ---: | ---: |
| Double door | 8 | 40 A | 12 V, 50 A minimum | 50 A slow-blow / automotive blade |
| Each single door | 4 | 20 A | 12 V, 25 A minimum | 25 A slow-blow / automotive blade |
| Window | 2 | 10 A | 12 V, 15 A minimum | 15 A slow-blow / automotive blade |

Use a **7.5 A slow-blow or automotive blade fuse** per actuator channel. It is above the
5 A design current so brief startup current does not nuisance-trip it, while still protecting
the VNH channel and cable. This value must be confirmed once with one fully assembled
mechanism.

## Main modules

| Item | Quantity | Notes |
| --- | ---: | --- |
| ESP32-S3 N16R8 | 1 | Central controller, socketed directly on the double-door DOOR-8CH board. |
| CC1101, 433 MHz, 3.3 V module | 1 | Socketed directly on the double-door DOOR-8CH board. Include an antenna matched for 433 MHz. |
| STM32F103C8T6 mini board | 11 | Same firmware on every board. Buy 1 spare. |
| Universal DOOR-8CH PCB | 5 | One board per physical object. It has four two-channel slots; populate 4/2/1 slots for double door/single door/window. |
| VNH5019A-E IC | 22 | Two ICs in every populated two-channel slot. Buy at least 4 spare ICs from a traceable supplier. |
| VNH heatsink mounting provision | 22 zones | Two M3.2 **NPTH** holes at 26 mm centres, each with 6 mm copper/solder-mask keepout, plus a 30 x 30 mm top-side keepout per VNH. |
| Optional VNH heatsink | 22 maximum | 20 x 20 x 10 mm finned aluminium, fit after thermal test or in poorly ventilated cabinets. |
| Electrically insulating thermal pad | 22 maximum | Silicone/Sil-Pad or Kapton thermal pad, 0.2 to 0.5 mm; mandatory when a VNH heatsink is fitted. |
| Nylon M3 screw and spacer set | 22 maximum | One set per optional VNH heatsink; avoids electrical connection to the live thermal slugs. |
| CAP1188, SPI-capable breakout | 5 | One per physical object, including the window. All eight channels are routed to field connectors. |
| D-M9N / D-M9P reed sensor | 18 recommended, 17 minimum | Three per single door, six on the double door (three per leaf), and two for the window. Add the eighteenth sensor when the window also needs its third position. |
| 25LC256-I/P or 25LC256-I/SN SPI EEPROM | 5 | One in S1 MASTER zone of each DOOR-8CH board. SLAVE slots receive configuration from S1 over internal UART. |
| SN65HVD230, 3.3 V CAN transceiver module | 5 | Socketed in the S1 MASTER zone of every DOOR-8CH board. SLAVE STM32 slots use only internal UART. |
| SN65HVD230, 3.3 V CAN transceiver module | 1 | Socketed in the ESP32 zone of the double-door board. |
| 12 V to 5 V DC/DC converter, **MP1584 5 V module** | 5 + 2 spare | Plugs or solders directly to the DOOR-8CH PCB. Fit the fixed 5 V version; its actual 5 V load is below 1 A per cabinet. The double-door cabinet also powers the ESP32. |
| 12 V actuator power supply | 5 or 1 central supply | Size from actual actuator current as described below. Separate cabinet supplies are preferred for easier fault isolation. |
| SWD programmer, ST-Link V2 or V3 | 1 | For STM32 commissioning and recovery. |

VNH5019A-E is an active ST product with 3 V CMOS-compatible inputs, current sense and PWM operation up to 20 kHz. It is used as a bare IC on the custom DOOR-8CH board, so the CS scaling and 3.3 V ADC protection are defined by our own schematic rather than by an unknown breakout board. [ST product page](https://www.st.com/en/motor-drivers/vnh5019a-e.html)

## Cabinet allocation

| Cabinet | STM32 MASTER | STM32 SLAVE | VNH5019A-E | CAP1188 | Reeds | Local UART links |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Double door | 1 | 3 | 8 | 1 | 6 | 3 |
| Single door 1 | 1 | 1 | 4 | 1 | 3 | 1 |
| Single door 2 | 1 | 1 | 4 | 1 | 3 | 1 |
| Single door 3 | 1 | 1 | 4 | 1 | 3 | 1 |
| Window | 1 | 0 | 2 | 1 | 2 minimum, 3 recommended | 0 |
| **Total** | **5** | **6** | **22** | **5** | **17 minimum, 18 recommended** | **6** |

## One populated two-actuator slot: mandatory passive parts

Quantities in this table are **per populated two-actuator slot**. There are 11 populated slots across five DOOR-8CH boards.

| Reference / purpose | Component and nominal | Per populated slot | Total for 11 slots |
| --- | --- | ---: | ---: |
| PWM, INA and INB safe state | 10 kOhm, 1%, 0.125 W pull-down | 6 | 66 |
| PWM, INA and INB series protection | 100 Ohm, 0.125 W | 6 | 66 |
| VNH DIAG pull-up | 4.7 kOhm, 1%, 0.125 W to **3.3 V** | 2 | 22 |
| VNH supply bulk capacitor | 470 uF, **35 V**, low-ESR electrolytic, >=105 C | 2 | 22 |
| VNH local ceramic capacitor | 100 nF, 50 V, X7R | 2 | 22 |
| VNH CS load resistor | 1.00 kOhm, 1%, 0.125 W from CS to GND | 2 | 22 |
| VNH CS ADC divider | 68 kOhm upper + 100 kOhm lower, both 1%, 0.125 W | 2 + 2 | 22 + 22 |
| VNH CS ADC filter | 1 kOhm series plus 100 nF, 16 V, X7R at PA0/PA1 | 2 + 2 | 22 + 22 |
| VNH CS_DIS default | 10 kOhm, 1%, 0.125 W pull-down to GND | 2 | 22 |
| Slot 3.3 V bulk decoupling | 10 uF, 10 V, X5R/X7R | 1 | 11 |
| Carrier 3.3 V local decoupling | 100 nF, 16 V, X7R; near LDO and digital loads | 4 | 44 |

## Shared DOOR-8CH board parts

| Purpose | Component and nominal | Per board | Total for 5 boards |
| --- | --- | ---: | ---: |
| Board 3.3 V LDO | AP2112K-3.3 or equivalent, >=300 mA, SOT-23-5 | 1 | 5 |
| 3.3 V LDO bulk decoupling | 10 uF, 10 V, X5R/X7R; one at input and one at output | 2 | 10 |
| 12 V window supervisor | TLV6700DDCR, SOT-23-6, dual open-drain output | 1 | 5 |
| 12 V monitor divider | 226 kOhm upper + 10 kOhm lower, both 1%, 0.125 W | 1 + 1 | 5 + 5 |
| Supervisor supply and sense filters | 100 nF, 25 V, X7R | 2 | 10 |
| PC13 pull-up | 10 kOhm, 1%, 0.125 W to `S1_3V3` | 1 | 5 |
| MASTER hold-up diode | SS34, 3 A / 40 V Schottky | 1 | 5 |
| MASTER hold-up capacitor | 4700 uF, 10 V, low ESR, radial | 1 | 5 |

The `226 kOhm / 10 kOhm` divider and TLV6700 400 mV reference give nominal thresholds of approximately 9.44 V rising and 9.31 V falling using the device's internal hysteresis. Fit this circuit once per DOOR-8CH board. Verify the thresholds and C280 hold-up time on a populated board before enabling field operation.

For each VNH5019A-E, tie its two open-drain `DIAG/EN` pins into the one diagnostic node for that actuator, use the listed 4.7 kOhm pull-up and route that node to PB5 or PB12. This enables both bridge legs and lets either diagnostic pull the STM32 input low.

## MASTER-slot CAN parts only

These parts are fitted only beside slot S1 on the five DOOR-8CH boards. A failed MASTER STM32 is replaced by inserting the same spare STM32 board into slot S1, so the spare board itself does not need a CAN transceiver.

| Purpose | Component and nominal | Per S1 MASTER zone | Total |
| --- | --- | ---: | ---: |
| CAN module socket | 1x6, 2.54 mm female header for SN65HVD230 | 1 | 5 |
| CAN module 3.3 V bypass | 100 nF, 16 V, X7R + 1 uF, 16 V, X7R | 1 + 1 | 5 + 5 |
| CAN TX series resistor | 47 Ohm, 0.125 W | 1 | 5 |
| EEPROM | 25LC256-I/P or 25LC256-I/SN | 1 | 5 |
| EEPROM VCC decoupling | 100 nF, 16 V, X7R | 1 | 5 |
| EEPROM /WP and /HOLD | 10 kOhm, 1%, 0.125 W pull-up to 3.3 V | 2 | 10 |
| EEPROM CS default inactive | 10 kOhm, 1%, 0.125 W pull-up to 3.3 V | 1 | 5 |

## ESP32 CAN and radio interface parts

The ESP32 is in the double-door cabinet and is connected internally to the same CAN trunk as that cabinet's MASTER. It is a separate CAN node, therefore its transceiver needs its own local decoupling even though it does not need a second external cabinet connector.

| Purpose | Component and nominal | Quantity |
| --- | --- | ---: |
| ESP32 CAN module socket | 1x6, 2.54 mm female header for SN65HVD230 | 1 |
| ESP32 CAN module 3.3 V bypass | 100 nF, 16 V, X7R + 1 uF, 16 V, X7R | 1 + 1 |
| ESP32 CAN TX series resistor | 47 Ohm, 0.125 W | 1 |
| CC1101 supply bypass at its connector | 100 nF, 16 V, X7R + 10 uF, 10 V, X5R | 1 + 1 |

### VNH5019A-E CS interface

For each VNH5019A-E use this fixed connection: `CS -> 1.00 kOhm -> GND`; the CS node also goes through `68 kOhm` to the divider node, with `100 kOhm` from that node to GND. Then place `1 kOhm` in series to STM32 `PA0` or `PA1` and `100 nF` from the STM32 pin to GND. Keep the CS traces away from PWM and motor tracks.

The divider ratio is 0.595. With the typical VNH5019 current ratio of about 7030 and the 1.00 kOhm CS load, the STM32 ADC sees approximately **84.6 mV/A**: about 0.42 V at the 5 A design current and about 2.54 V at 30 A. Thus the 3.3 V ADC stays protected even if the bridge is driven far above the normal 5 A operating current. `CS_DIS` is held low through its listed 10 kOhm resistor so current sense remains enabled.

The VNH5019 current-sense ratio has production and temperature tolerance, therefore this circuit is for repeatable measurement, not an absolute current meter. After the first DOOR-8CH board is assembled, measure one known load current, calibrate `CURRENT_MA_PER_ADC_COUNT_NUM` in the STM32 firmware, then set the per-actuator over-current limit to **5 A** in the cabinet configuration.

## Master-only sensor and UART parts

| Purpose | Component and nominal | Quantity for system |
| --- | --- | ---: |
| CAP1188 INT pull-up | 10 kOhm, 1%, 0.125 W to 3.3 V | 5 |
| CAP1188 RESET pull-down | 10 kOhm, 1%, 0.125 W to GND; RESET is active high | 5 |
| CAP1188 supply bypass near connector | 100 nF, 16 V, X7R + 4.7 uF, 10 V, X5R | 5 + 5 |
| CAP1188 field connector | 2-pin, 3.5 mm pitch, SENSOR/GND, one per channel | 40 |
| CAP1188 sensor-line series resistor | 1 kOhm, 0.125 W initial value; provide 0 Ohm tuning option | 40 |
| Reed input pull resistor | 4.7 kOhm, 1%, 0.125 W; fit to 3.3 V for D-M9N or GND for D-M9P | 17 minimum, 18 recommended |
| Reed input series resistor | 1 kOhm, 0.125 W | 17 minimum, 18 recommended |
| Reed input noise filter | 100 nF, 16 V, X7R at the STM32 connector | 17 minimum, 18 recommended |
| UART TX series resistor | 100 Ohm, 0.125 W, one at each end of each link | 12 |
| SLOT_ID low strap | 10 kOhm, 1%, 0.125 W to GND | 7 |

For every reed location fit **one**, not both, 4.7 kOhm pull directions. D-M9N and D-M9P polarity is then selected in the cabinet configuration. Use screened or twisted sensor cable when it leaves the cabinet.

Each CAP1188 channel has its own two-pin edge connector. Connect one twisted-pair
conductor to `SENSOR` and the other to `GND`; the GND conductor is a nearby return
or shield and must not be electrically joined to the isolated touch electrode.
Populate only the connectors needed by the installation, while retaining all eight
channels on every universal board.

## CAN bus and cable entry

| Item | Quantity | Specification |
| --- | ---: | --- |
| CAN connector, 4-pin | 8 | CANH, CANL, CAN_GND, shield/drain. In a five-cabinet daisy chain: one at each endpoint and two at each of three intermediate cabinets. ESP32 is wired internally in the double-door cabinet. |
| CAN termination jumper footprint | 5 | One on every MASTER carrier. Fit 120 Ohm, 0.25 W only at the two physical ends of the complete cable. Buy 5 resistors, populate 2. |
| CAN common-mode choke | 5 | One at each cabinet cable entry, for example a 51 Ohm common-mode impedance class part suitable for CAN. |
| Dual CAN TVS protector | 5 | Automotive CAN-rated dual-line protector, for example SM24CANB class, at each cabinet cable entry. |
| CAN cable | As measured | 120 Ohm twisted pair plus reference ground; use shielded cable in electrically noisy routes. |

The system total is **six CAN transceiver modules**: five in S1 MASTER zones and one beside the ESP32. The selected SN65HVD230 module uses 3.3 V logic directly, matching STM32 and ESP32 GPIO. Its `CANH` and `CANL` pins still require the board-level TVS, common-mode choke and correct two-end termination described above.

## 12 V cabinet power entry and protection

### Low-voltage DC/DC selection

Do **not** use the pictured `CA-1235` / MP1495 mini-module in a permanent cabinet.
Its stated 5 to 15 V input range leaves no practical margin for motor-supply
transients on a nominal 12 V line. It is acceptable only on a clean bench supply
for a short test.

For a preferred long-term DC/DC part, select a fixed 5 V buck module with all
of the following:

- input operating range of 9 to 36 V or wider;
- regulated 5.0 V output, 3 A continuous rating or higher;
- short-circuit and thermal protection;
- screw terminals or locking connectors, rather than loose Dupont wiring.

Install it after the cabinet's reverse-polarity circuit and main fuse. The listed
input TVS and capacitors remain mandatory: a wide-range converter does not remove
the need to suppress motor transients at the 12 V entry. The MP1584 exception
below is permitted only with its stricter listed protection parts.

**Preferred part when available:** `Mean Well RSD-30G-5`, five pieces. Its
specified 9 to 36 V input and 5 V / 6 A output leave ample margin for the actual
low-voltage load while remaining within the protected 12 V cabinet branch. [Manufacturer data sheet](https://www.meanwell.com/Upload/PDF/RSD-30/RSD-30-spec.pdf)

**Compact alternative:** `Pololu D24V50F5`, when its small PCB form factor is
more important than a screw-terminal enclosed converter. It accepts 6 to 38 V,
delivers a typical 5 A continuous at fixed 5 V, and includes reverse-voltage,
over-current, short-circuit and thermal protection. It still requires the same
cabinet TVS, fuse and secure mounting. [Pololu specifications](https://www.pololu.com/product/2851)

**Available selected part:** the pictured `MP1584` 5 V / 3 A mini-module. Buy
seven modules: five installed and two spares. It is acceptable because the actual
5 V load in every cabinet is below 1 A, but it is not a 3 A continuous thermal
design. Select the fixed **5 V** version, solder the wires to its pads, add
strain relief and mount it on an insulated carrier; do not use Dupont jumpers.

The original MP1584 specifies 28 V maximum operating input and 30 V absolute
maximum. Its seller marking of 30 V is therefore not a design target. Use it
only behind the listed `SMBJ16A` TVS and a branch fuse, which keep the protected
logic branch below the operating limit during short motor transients. [MP1584 data sheet](https://www.digikey.com/en/htmldatasheets/production/1785679/0/0/1/mp1584.html)

| Item | Quantity | Specification |
| --- | ---: | --- |
| Main cabinet fuse holder | 5 | DIN-rail or automotive blade type. |
| Main cabinet fuse | 1 x 50 A, 3 x 25 A, 1 x 15 A | Slow-blow or automotive blade. |
| Logic DC/DC branch fuse holder | 5 | One after the reverse-polarity circuit, before the MP1584 input. |
| Logic DC/DC branch fuse | 5 x 1 A | Slow-blow or automotive blade. |
| Per-actuator fuse holder | 22 | One per VNH5019A-E motor supply. |
| Per-actuator fuse | 22 x 7.5 A | Slow-blow or automotive blade. |
| Reverse-polarity MOSFET | 5 | P-channel, >=40 V, low Rds(on), current rating above cabinet peak; IRF4905 class or a proper ideal-diode controller solution. |
| Gate resistor / gate pull-up | 100 Ohm + 100 kOhm, 0.125 W | 5 + 5 |
| Gate-source zener | 12 V, 0.5 W | 5 |
| 12 V transient suppressor | SMBJ16A, 600 W, unidirectional | 5 | Required when using an MP1584 module; its approximate 26 V clamp preserves margin below the converter's 28 V operating maximum. |
| DC/DC input bulk capacitor | 470 uF, **50 V**, low-ESR, >=105 C | 5 |
| DC/DC input ceramic | 1 uF, 50 V, X7R + 100 nF, 50 V, X7R | 5 + 5 |
| DC/DC output bulk capacitor | 220 uF, 10 V, low-ESR | 5 |
| DC/DC output ceramic | 10 uF, 10 V, X5R + 100 nF, 16 V, X7R | 5 + 5 |

The `5 A` current limit and `7.5 A` fuse are based on the measured 2.5 A maximum with a
two-times reserve. Before commissioning, record the short start current at 12 V. If it is
above 7.5 A for long enough to blow the fuse, increase the fuse only after confirming that
the cable, connectors, VNH thermal design and programmed current limit remain protected.

The current 8 A firmware default is a commissioning placeholder. It must be changed to
5 A only after VNH5019 CS calibration is verified on the finished DOOR-8CH board.

## Enclosures, wiring and installation hardware

| Item | Quantity | Notes |
| --- | ---: | --- |
| IP-rated control cabinet | 5 | One per physical object. Choose size after heat and cable-entry layout. |
| DIN rail | 5 sets | For fuses, DC/DC, terminals and power distribution. |
| 12 V distribution terminal blocks | 5 sets | Separate motor positive distribution and star ground point. |
| 2-pin actuator terminal blocks | 22 | **Phoenix Contact MKDS 1,5/ 2-5,08, 1715721**; 5.08 mm pitch, 17.5 A. Search-compatible substitute: KF2EDG 5.08-2P straight, >=10 A, >=1.0 mm2. |
| 4-pin two-channel-slot motor-power terminal blocks | 11 | 5.08 mm pitch; MKDS 1,5/ 4-5,08 or KF2EDG 5.08-4P. Carries separately fused CH1 and CH2 inputs. |
| 3-pin sensor terminals | 14 minimum, 15 recommended | 3.3 V, signal, GND. |
| 8-pin CAP1188 terminals/headers | 4 | 3.3 V, GND, CS, SCK, MISO, MOSI, IRQ, RESET. |
| External UART cable assemblies | 0 | Master-to-slave UART links are internal DOOR-8CH PCB tracks. |
| 4-pin CAN terminal blocks | 8 | CANH, CANL, CAN_GND, shield/drain; IN/OUT at the three intermediate cabinets. |
| Cable glands | As measured | Separate motor, sensor and CAN entries. |
| Motor cable | As measured | Cross-section selected from length and fuse rating. Do not use thin Dupont wire. |
| Ferrules, labels and heat-shrink | As needed | Label every actuator, sensor and CAN address. |
| 40 mm / 60 mm cabinet fan | As thermal test requires | Add when VNH module or DC/DC temperature exceeds its safe limit. |

## Commissioning spares

Buy these in addition to the calculated total:

| Item | Spare quantity |
| --- | ---: |
| STM32F103C8T6 board | 1 |
| VNH5019A-E IC | 4 |
| CAN transceiver | 2 |
| 25LC256 EEPROM | 2 |
| CAP1188 module | 1 |
| 12 V to 5 V DC/DC | 1 |
| Assorted 100 nF / 1 uF / 10 uF capacitors and 1 kOhm / 4.7 kOhm / 10 kOhm resistors | 20% above calculated count |
