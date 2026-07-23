# ESP32 CAN master v0.1.0-alpha.11 N16

This release adds an optional two-actuator automatic sliding module.

- A single- or double-door object can be paired with one two-actuator CAN node.
- Opening completes the main mechanism first, waits for the configured delay
  and then opens the sliding module.
- Closing completes the sliding module first, waits for the configured delay
  and then closes the main mechanism.
- A fault, stale moving telemetry, sequence timeout or main-door safety-edge
  touch stops both CAN nodes.
- Direct movement commands to a paired auxiliary node are blocked; calibration
  remains available from its own object page.
- Pairing is disabled by default and stored separately, so upgrading does not
  reset existing objects.
- System backup format V2 includes pairings and both delays.
- V1 `.wbackup` files from alpha.10 remain importable with sliding disabled.
- Invalid pairings are removed automatically after CAN EEPROM reconfiguration.

Use STM32 universal firmware v0.1.0-alpha.11.

Build result: 1,046,685 bytes Flash (33%), 70,616 bytes static RAM (21%).

