# ESP32-S3 CAN coordinator v0.1.0-alpha.3

Chrome-tested web interface update. Firmware control logic and CAN protocol are
compatible with STM32 universal v0.1.0-alpha.2.

- Fixes horizontal page overflow at 390 px mobile width.
- Keeps the 650 px actuator table scrollable inside its own container.
- Desktop control, remotes, events, settings and CAN discovery views tested.
- Mobile control, remotes and settings views tested without document overflow.
- Flash application usage: 1012617 bytes (77%); static RAM: 61748 bytes (18%).
- Default setup AP: `WindowControl-Setup`, password `12345678`.
- Default web login: `admin`, password `admin12345`.

Use the merged binary for a complete first flash at address `0x00000000`.
Change default credentials before installation. Hardware bench testing is still required.
