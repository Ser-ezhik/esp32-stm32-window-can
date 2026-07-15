# Vendor and photo-derived footprints

- `ESP32-S3-DevKitC.kicad_mod` is copied from Espressif's official
  `espressif/kicad-libraries` repository. The library is CC-BY-SA 4.0 with the
  design-output exception stated in `ESPRESSIF_KICAD_LICENSE.md`.
- `CAP1188_Adafruit1602_Module_2x13.kicad_mod` uses the exact outline, header
  and mounting-hole coordinates from Adafruit's official product 1602 Eagle
  board. The purchased blue module shown in the project photograph matches
  this board geometry.
- `SN65HVD230_Module_14.5x16.1mm_1x06.kicad_mod` is derived from the supplied
  listing photograph, which explicitly gives 14.5 x 16.1 mm.
- `CC1101_433MHz_Module_28x15mm_2x04.kicad_mod` is derived from the supplied
  listing photograph, which explicitly gives 28 x 15 mm and a 2x4 header.

All photo-derived footprints still require a 1:1 print check against one
physical purchased module before fabrication.
