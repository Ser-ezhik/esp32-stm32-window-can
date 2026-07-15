# STM32 Universal Actuator Node v0.1.0-alpha.5

Changes:
- Adds three reed inputs from S2 to the internal UART status payload for double-door leaf B.
- Combines S1 and S2 reed masks into the CAN sensor frame on double-door cabinets.
- Keeps S1-only reed behavior for windows and single doors.

Build result:
- Flash: 24132 bytes, 36 percent of STM32F103C8T6 64 KB target.
- RAM: 3488 bytes, 17 percent of 20 KB target.
