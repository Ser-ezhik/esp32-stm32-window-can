# DOOR-8CH JLCPCB fabrication package v1.47

Upload `DOOR-8CH_JLCPCB_Gerber_v1.47.zip` directly to the JLCPCB PCB quote.

Order parameters:

- material: FR-4;
- layers: 4;
- nominal board size: 260 x 160 mm;
- board thickness: 1.6 mm;
- outer copper: 2 oz;
- inner copper: 0.5 oz;
- solder mask: green;
- silkscreen: white;
- surface finish: HASL with lead;
- delivery format: single PCB;
- quantity for the initial quote: 5.

The production ZIP contains nine Gerber layers, separate PTH and NPTH Excellon
drill files, and the Gerber job file. KiCad DRC passed with zero violations and
zero unconnected items before export.

For JLCPCB top-side SMD assembly, use the BOM and CPL from `v1.47/`:

- `DOOR-8CH_BOM_JLCPCB_SMD_ONLY.csv`;
- `DOOR-8CH_CPL_JLCPCB_SMD_ONLY.csv`.

The assembly files intentionally exclude the plug-in STM32, ESP32-S3, CAN,
CAP1188, CC1101 and DC-DC modules, all eight VNH5019A-E devices, through-hole
parts, and bottom-side D280. These parts are installed manually after delivery.
The CPL includes the verified JLCPCB rotation corrections for SOT-23,
SOT-23-6, SOT-223 and SOIC-8 packages. `DOOR-8CH_PCBA_ORIENTATION_AUDIT.csv`
records each correction.

Version v1.47 corrects the photographed YD ESP32-S3 N16R8 female-socket row
spacing from 22.86 mm to 25.40 mm. The ESP32 outline, right-side labels,
female-header placement coordinates and the two connected CAN tracks are
updated. Inner reed tracks are routed around the widened through-hole row and
H1 is moved clear of the module. DRC passes with zero violations and zero
unconnected items.

Version v1.46 enlarges all 44 ESP32 female-socket drills from 0.80 mm to
1.00 mm. The oval ESP32 pads are 1.27 x 2.00 mm, preserving copper around the
larger finished hole while maintaining the reviewed routing clearances.

Version v1.45 retains the v1.44 connector changes and exposes the reference of
every electronic and useful mechanical footprint on front silkscreen. This
includes diodes, protection parts, the DC-DC module, fuse, CAN choke, mounting
holes and heatsink holes. Only the internal `QR1` service reference remains
hidden because the QR graphic is already self-identifying.

Version v1.44 replaces each separate actuator-power and motor-output pair with
one keyed DINKLE 2EHDRC-04P connector. Its pinout is `+12V, GND, MA, MB`, the
finished power-terminal drill is 1.70 mm, and the pad diameter is 3.20 mm.
Signal-terminal drills are 1.30 mm. Front silkscreen now shows all resistor and
capacitor references plus the four actuator-connector pin functions. The D230
polarity correction and Telegram QR code from v1.43 are retained.

SHA-256:

`22AB6B0D419EB8FEE658949089B4AA8E29D951DA397C86C450E947D43B0CF0CB`
