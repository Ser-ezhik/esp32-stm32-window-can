# SLIDE-2CH optional automatic-door module

## Purpose

`SLIDE-2CH` is an optional compact CAN node for two 12 V actuators that slide
door leaves after the main door mechanism has opened. It uses the same socketed
STM32 module, VNH5019A-E circuit and universal firmware as the existing boards.
No different STM32 binary is required.

The module is configured as:

- object type `Window`;
- actuator count `2`;
- slave count `0`;
- CAP1188 enabled mask `0`;
- its own unique CAN cabinet number.

ESP32 links this node to a single- or double-door object. When the option is
disabled or the module is absent, the existing door operates unchanged.

## Required hardware

- one socketed STM32F103C8T6 mini module;
- two VNH5019A-E bridges with the complete DOOR-8CH passive and current-sense
  networks;
- one SN65HVD230 CAN transceiver module;
- one 25LC256 carrier EEPROM;
- one MP1584 12 V to 5 V module and the existing protected logic-power input;
- two keyed four-pin actuator connectors carrying 12 V, GND, OUTA and OUTB;
- one CAN connector with TVS, common-mode choke and optional DNP 120 Ohm
  termination;
- three D-M9 reed inputs: fully open, fully closed and mechanism in-place;
- per-channel 7.5 A fuses and local 470 uF / 35 V capacitors;
- SWD connector, power-good circuit and MASTER hold-up supply.

The open and closed reeds are mandatory for deterministic operation after a
cold start. The actuator internal limit switches remain the normal end-of-travel
and calibration signal, but they cannot report the initial position while the
motor is unpowered.

## Safe sequence

Opening:

1. ESP32 verifies that both CAN nodes are online and fault-free.
2. The main door mechanism opens completely.
3. After the configured delay, SLIDE-2CH opens both sliding actuators.

Closing:

1. SLIDE-2CH closes both sliding actuators.
2. After the configured delay, the main door mechanism closes.

During either sequence, a fault, movement timeout or loss of fresh telemetry
stops both nodes. A CAP1188 touch on the main door during closing is sent
immediately over CAN and also stops both nodes. Each moving STM32 independently
stops within 300 ms if ESP32 heartbeats disappear.

## PCB derivation

The electrical implementation must be copied from the S1 section and channels
1/2 of `hardware/DOOR-8CH`, not from the archived `ACT-CARRIER-2CH` study.
Keep both VNH zones and actuator connectors on one board edge, and keep CAN,
STM32, EEPROM, reeds and sensor routing on the opposite quiet edge. The VNH
heatsink holes and keepouts remain identical to DOOR-8CH.

This document defines the approved architecture. A routed KiCad PCB and
fabrication package are a separate hardware release and must pass ERC/DRC and
the same schematic-to-firmware pin audit as DOOR-8CH.

