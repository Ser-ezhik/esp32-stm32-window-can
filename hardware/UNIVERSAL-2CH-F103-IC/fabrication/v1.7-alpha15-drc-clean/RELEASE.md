# Two-channel fabrication revision v1.7

Generated 2026-09-06 for the direct-IC STM32F103C8T6 board and alpha15 firmware.
Older releases are retained for history, not for this revised board.

## Digital checks completed

- KiCad 10: zero errors, zero warnings, zero unconnected pads.
- Existing rule severities and exclusions were not changed.
- Conflicting silkscreen labels relocated; no component positions changed.
- Zone minimum feature width is 0.8 mm; zones refilled to remove copper slivers.
- All 106 footprints, both motor track sets and MCU/connector pad assignments
  checked against the previous electrical repair. No new pin changes.
- Direct-IC firmware/power-net audit passes, including the protected monitor
  supply and CAP1188 decoupling.
- Both copper layers, both mask layers, silkscreens, outline and separate
  plated/nonplated drills exported together from the current PCB.
- BOM/CPL regenerated: 75 SMD placements, 3 top and 72 bottom, excluding VNH.
  C340 is now top-side. Do not use an older CPL.

## Required manual assembly

Three insulated wires are still part of this design:

1. C280 positive to J280B.
2. TP290 to JP290 (J220.6).
3. D230 pad 1 (cathode, protected supply) to C270 pad 1.

They connect intentionally separate net names and therefore are not counted
as unrouted tracks by DRC. Zero unconnected pads does not remove these wires.

## Manufacturing versus operation

The archive is current and passes the listed digital fabrication checks.
No physical board has been tested in this revision. Initial current calibration,
power-fail hold-up timing, loaded motor temperature and obstruction-stop testing
must be performed on an assembled prototype; these cannot be validated by DRC.

BOM stock and JLCPCB model orientation have not been checked in a live new order.
CPL uses the existing package corrections; validate pin 1/polarity in the
manufacturer's assembly preview before submitting a populated-board order.
The preview PNGs are KiCad views, not evidence of JLCPCB placement approval.

No order has been created or paid for by this release operation.
