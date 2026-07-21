# Module measurements required before fabrication

The following sockets are already based on the pictured 2.54 mm module
headers: two SN65HVD230 modules and the 2x4 CC1101 module. Verify this with a
physical module before ordering boards.

The photographed module dimensions currently used by the board are:

| Module | Needed measurements | Why |
| --- | --- | --- |
| STM32F103C8T6 mini | confirm 20.32 mm between the outer rows, 2.54 mm within each pair, and the 32 x 22.86 mm outline | the photographed board has four 1x10 rows, not two 1x15 rows; a single 40-pin footprint is used |
| YD ESP32-S3 N16R8, dual USB-C | 22 pins per side, 2.54 mm pitch, 25.40 mm row spacing | photo-matched footprint; still verify with a 1:1 print |
| CAP1188 breakout | left/right header row spacing, pin count, full outline, mounting-hole positions | the supplied photo shows a vendor-specific breakout with more than the minimum SPI pins |

Measure with a ruler or caliper and photograph each module next to it. Values
to 0.5 mm are sufficient for the first board outline; header pitch should be
confirmed as 2.54 mm.

No fabrication output is generated until these measurements are entered and a
1:1 print is checked against the real modules.
