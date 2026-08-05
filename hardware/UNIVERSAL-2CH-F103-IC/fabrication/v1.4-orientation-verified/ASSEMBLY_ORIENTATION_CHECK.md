# Assembly orientation check

Release: `v1.4-orientation-verified`

The bottom-side JLCPCB placement preview was checked against pad 1, cathode,
and footprint markings on the KiCad PCB.

## JLCPCB SMD assembly

| References | Check |
| --- | --- |
| CAP1 | Pin 1 marker matches QFN pad 1 |
| U300 | Pin 1 marker matches LQFP pad 1 |
| U250 | Pin 1 marker matches SOIC pad 1 |
| U270 | Pin 1 marker matches SOT-23-6 pad 1 |
| U230 | Pin 1 marker matches SOT-223 pad 1 |
| D1101, D1201 | Pin 1 marker matches BAT54S pad 1 |
| D230 | Cathode matches pad 1 and `LOGIC_12V_PROTECTED` |
| D231 | Cathode matches pad 1 and the PCB cathode marking |
| D280 | Cathode matches pad 1 and the PCB cathode marking |
| D240, D241 | Bidirectional ESD parts; landing and rotation checked |
| Y300 | Pin 1 marker matches crystal pad 1 |
| L240 | CPL pin 1 matches footprint pad 1; part is currently DNP due to JLCPCB stock shortage |

All non-polarized resistors and ceramic capacitors were checked for landing,
centering, board-edge clearance, and overlap.

## Manual assembly

The following parts are not included in the JLCPCB SMD placement and must be
installed using PCB silkscreen and pad markings:

- `U1`, `U2`: VNH5019A-E pin 1 and exposed power pads.
- `C1101`, `C1201`, `C230`, `C233`, `C280`: electrolytic capacitor polarity.
- `D240`, `D241`, `L240`, or any other DNP SMD part if fitted manually.
- `CAN1`, `DC1`: module header orientation and supply polarity.
- All pluggable terminal blocks: wire order must follow the silkscreen labels.

KiCad DRC result: 0 violations, 0 unconnected pads, 0 footprint errors.
