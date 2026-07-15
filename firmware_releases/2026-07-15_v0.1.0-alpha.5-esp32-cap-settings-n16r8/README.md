# ESP32-S3 coordinator v0.1.0-alpha.5 N16R8

This release adds per-object CAP1188 setup to the web interface.

- Eight individual CS1...CS8 checkboxes are available for every window or
  door.
- The page displays the number of enabled channels and a CAP1188 noise warning.
- Settings are stored on ESP32 and sent to the cabinet immediately.
- ESP32 automatically restores the saved mask after a cabinet STM32 restart.
- Defaults are three enabled channels for a window or single door and six for
  a double door.

Hardware target: ESP32-S3 N16R8, 16 MB DIO Flash, PSRAM disabled, 3 MB
application partition. Use the merged image at address `0x00000000` for a full
first flash.
