# Module measurements required before fabrication

The following sockets are already based on the pictured 2.54 mm module
headers: two SN65HVD230 modules and the 2x4 CC1101 module. Verify this with a
physical module before ordering boards.

Two modules must be measured before their final KiCad footprints are added:

| Module | Needed measurements | Why |
| --- | --- | --- |
| STM32F103C8T6 mini | centre-to-centre distance of the two 1x15 header rows; board outline | the socket currently uses the known 20.32 mm row spacing, but this must be confirmed on the purchased revision |
| ESP32-S3 board | pin count per side, row spacing, full width and length, USB overhang | several ESP32-S3 boards look alike but do not share a footprint |
| CAP1188 breakout | left/right header row spacing, pin count, full outline, mounting-hole positions | the supplied photo shows a vendor-specific breakout with more than the minimum SPI pins |

Measure with a ruler or caliper and photograph each module next to it. Values
to 0.5 mm are sufficient for the first board outline; header pitch should be
confirmed as 2.54 mm.

No fabrication output is generated until these measurements are entered and a
1:1 print is checked against the real modules.
