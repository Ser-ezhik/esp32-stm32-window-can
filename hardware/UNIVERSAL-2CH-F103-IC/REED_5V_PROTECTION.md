# Reed sensor 5 V input protection

## Connectors

`J201` is the open-position sensor and `J202` is the closed-position sensor.
Both connectors use the same pin order printed on the front silkscreen:

1. `5V`
2. `SIG`
3. `GND`

The intended sensors are NPN D-M9N units. The firmware-selectable reed polarity
and STM32 internal pull resistor remain unchanged.

## Accidental PNP connection protection

`R290` and `R291` are 4.7 kOhm series resistors between the two sensor signal
pins and STM32 pins PB0/PB1. If a 5 V PNP D-M9P output is connected by mistake,
the resistor limits the current into the STM32 input clamp to approximately
0.3 mA. This protects against an accidental 5 V PNP output; it does not protect
the signal input from 12 V, reversed power, or arbitrary field wiring faults.

R290 and R291 are top-side SMD parts. The September 2026 repair also moves C340
to the top side. The historical PCBA CPL files do not contain this change.
R290 and R291 were kept on top because the corresponding
bottom-side areas contain power copper and cannot accept the parts without a
major reroute.

## Required assembly wires

Three insulated wire links must be installed after PCB assembly:

- `TP290` to `JP290` (`J220.6`): CAP1188 3.3 V supply link. `TP290` is the
  0.6 mm exposed SMD pad on the bottom side. `JP290` is the 0.6 mm plated hole
  near the front-side `WIRE TP290 -> JP290` marking.
- `C280+` to `J280B`: existing 5 V hold-up capacitor supply link.
- `D230.1` (cathode, protected 12 V) to `C270.1` (positive supply): feeds
  U270 and R270 after reverse-polarity protection. These are existing SMD pads,
  not new through-hole terminals. Do not connect this wire to D230.2.

Use insulated copper wire around 0.2-0.35 mm2. Thin PTFE-insulated wire is also
acceptable for these low-current logic supplies when it is mechanically fixed
and strain relieved.

Do not power the board before all three links have been installed and checked for
continuity and shorts to GND.
