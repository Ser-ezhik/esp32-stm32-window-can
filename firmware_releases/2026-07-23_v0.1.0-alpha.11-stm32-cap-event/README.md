# STM32 universal node v0.1.0-alpha.11

This release immediately reports CAP1188 touch-mask changes over CAN.

- CAP1188 remains sampled every 10 ms.
- A touch or release sends a sensor frame immediately, including while the main
  door controller itself is idle.
- This lets ESP32 stop an optional SLIDE-2CH module without waiting for the
  one-second idle telemetry period.
- The local 300 ms command-heartbeat timeout remains the independent fallback
  if ESP32 or the CAN bus disappears.
- JTAG remains disabled with SWD retained.
- The same binary remains valid for every MASTER and SLAVE socket.

Build result: 24,128 bytes Flash (36%), 3,500 bytes static RAM (17%).

