# CAN and local UART protocol

Protocol version: 1. Classic CAN 2.0B, standard 11-bit identifiers, 500 kbit/s.

## CAN identifiers

| Range | Direction | Purpose |
| --- | --- | --- |
| 0x100-0x13F | ESP32 to cabinet | command and heartbeat |
| 0x180-0x1BF | cabinet to ESP32 | aggregate state |
| 0x200-0x23F | cabinet to ESP32 | reeds, CAP1188 and power status |
| 0x280-0x37F | cabinet to ESP32 | actuator telemetry, four frames per cabinet |
| 0x380-0x3BF | cabinet to ESP32 | asynchronous fault/event |
| 0x3C0-0x3FF | ESP32 to cabinet | configuration fragments |
| 0x700 | ESP32 to all | discovery request |
| 0x740-0x77F | cabinet to ESP32 | discovery response |
| 0x7C0 | ESP32 to unconfigured master | provision carrier identity by UID hash |

For cabinet `N`, actuator telemetry frame `0x280 + N*4 + slot` contains the two
actuators controlled by that STM32. Slot 0 is master, slots 1-3 are local slaves.

Commands carry a sequence counter. A motor command is accepted only after a recent
ARM command or with an explicit armed flag. While moving, ESP32 repeats the active
command as a heartbeat. Loss of a valid command for 300 ms stops the cabinet.

## Local UART

Master-to-slave links use 250000 8N1 and a binary frame:

```text
A5 | type | payload_length | sequence | payload | CRC16-CCITT
```

CRC covers `type`, `length`, `sequence` and payload. Each slave is point-to-point,
so there is no bus address or collision arbitration. All slaves use the same physical
PB6/PB7 UART pins; the carrier connects that pair to the corresponding master USART.

## Telemetry rate

- moving/calibrating: 10 Hz;
- idle: 1 Hz;
- fault events: immediate plus normal status;
- recommended capacity: 32 cabinets per 500 kbit/s segment;
- firmware table capacity on ESP32: 64 objects.
