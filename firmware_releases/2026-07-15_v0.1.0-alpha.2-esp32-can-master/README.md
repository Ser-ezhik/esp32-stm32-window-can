# ESP32-S3 CAN coordinator v0.1.0-alpha.2

First buildable ESP32-S3 release for the CAN hardware generation.

- Flash application usage: 1012601 bytes (77%).
- Static RAM usage: 61748 bytes (18%).
- CAN coordinator for up to 64 configured objects.
- CC1101 433 MHz receiver and editable remote-button assignments.
- Object-based web UI with telemetry, event log, discovery and provisioning.
- Position-aware two-direction actuator speed calibration.
- Default setup AP: `WindowControl-Setup`, password `12345678`.
- Default web login: `admin`, password `admin12345`.

Use the merged binary for a complete first flash at address `0x00000000`.
Change default credentials before installation. This release has been compiled
and statically checked, but still requires bench testing with the final carrier.
