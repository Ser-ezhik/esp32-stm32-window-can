# Two-channel review corrections, 2026-09-06

## Status

The current KiCad PCB and STM32 alpha.15 source contain the focused review
corrections below. This is an engineering revision, not approval of the old
manufacturing archives or the JLCPCB cart. No order was placed or changed.

## PCB

- U270.5, C270.1 and R270.1 now share POWER_MONITOR_12V. The old feed from
  LOGIC_12V_FUSED was disconnected and its unused branch removed.
- Install a wire from D230.1 (cathode, LOGIC_12V_PROTECTED) to C270.1 to supply
  this branch after the reverse-polarity diode. Both ends are existing SMD
  pads. The divider now measures the protected rail, so the input-referred
  trip voltage additionally includes the forward drop of D230.
- C340 (100 nF) moved to F.Cu at (83.5, 54.8) mm and connects to S1_3V3,
  after the existing TP290-to-JP290 wire. Its ground connection uses a local
  via. C341 remains on the MCU supply branch.
- Existing C280+ -> J280B and TP290 -> JP290 (J220.6) wires remain mandatory.
  The total is THREE wires. Check continuity and polarity before powering.
- Connector placement, drill sizes, STM32 mappings, VNH footprints and motor
  tracks were not changed. The automatic comparison checked all 106 footprints.

## Firmware

- Time is refreshed after command processing, before protection uses it.
  This prevents unsigned underflow when direction dead-time advances millis().
- Movement completion only runs in Moving or Calibrating state and preserves
  the completed direction before clearing the active command.
- Before reporting successful completion, the master requires the target reed
  input; a double door requires both corresponding reed inputs. Missing
  confirmation raises NoCurrent and skips calibration application.
- A configured CAP1188 is required for windows as well as doors. A zero sensor
  mask explicitly disables this requirement.
- Before motion, CAP identity and enabled/interrupt masks are read back. An
  already-touched edge blocks closing before PWM starts.
- CAP identity and masks are checked every 250 ms during normal polling.
  Failure raises Cap1188Offline; ClearFault can reinitialize the device.
- EEPROM structure and protocol numbers are unchanged. Version is alpha.15.

## Verification

- Arduino STM32 Generic F103C8 build: 24,792 bytes Flash, 3,508 bytes static RAM.
- KiCad 10 DRC: 0 errors, 0 unconnected pads, 52 warnings. The warnings are
  48 silkscreen issues and 4 copper-sliver warnings. They were not suppressed
  to obtain this result.
- tools/verify_2ch_review_fix.py passed: all footprint/pad mappings compared
  against 7606dc24930b113c63ee8d6200549ff06856821e, with only the four intended
  net changes and C340 relocation allowed. Motor track sets match the baseline.
- Firmware was compiled and reviewed; motion/fault behavior has not been run
  on physical hardware. No thermal, EMC, force or contact-safety test was done.

## Remaining limits

- A group reed confirms the window position, not the position of every motor.
  Current disappearance alone cannot distinguish every individual cable fault
  from an internal limit switch. Independent actuator feedback is required
  for that distinction.
- CAP health polling is not an independent hardware safety circuit. Blocking
  command handling means the configured polling periods are not a guaranteed
  worst-case reaction time.
- Current conversion still needs per-channel bench calibration. Hold-up time
  and actual power-fail EEPROM writes also require power-interruption testing.
- Existing Gerbers/CPL files predate this change. C340 changed side and supply
  routing changed; do not reuse those files for this PCB revision.
- The 52 DRC warnings and mechanical/thermal checks remain before a production
  release. The focused correction does not certify the entire design.
