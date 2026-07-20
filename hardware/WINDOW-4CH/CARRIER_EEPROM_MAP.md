# WINDOW-4CH carrier EEPROM

The 25LC256 on the carrier keeps both socketed STM32 modules universal. S1
reads the cabinet identity; S2 obtains its operating configuration over UART.

## Identity at 0x0000 and 0x0020

The two addresses form an A/B pair. Reconfiguration writes and verifies the
inactive copy first. The valid copy with the newest `configRevision` is loaded,
so loss of power during a write does not destroy the previous configuration.

| Offset | Size | Field | WINDOW-4CH value |
| ---: | ---: | --- | --- |
| `0x00` | 4 | magic | `0x314E4957` (`WIN1`) |
| `0x04` | 1 | version | `1` |
| `0x05` | 1 | cabinetId | unique CAN address, `0..63` |
| `0x06` | 1 | objectType | `0` for window |
| `0x07` | 1 | slaveCount | `0` for two actuators, `1` for four actuators |
| `0x08` | 2 | configRevision | incremented after each verified web reconfiguration |
| `0x0A` | 2 | reserved | D-M9 polarity mask |
| `0x0C` | 2 | crc | CRC-16/CCITT with this field zeroed |

Only reed polarity bits 0..2 are used: open, closed and in-place. A zero bit is
active-low D-M9N; a one bit is active-high D-M9P wired for a 3.3 V output.

## Power-loss record at 0x0040

The existing universal firmware uses the same 64-byte page and `PWR1` record
layout documented for `DOOR-8CH`. U250 is supplied from held `S1_3V3`, while
D280 and C280 keep S1 alive long enough to finish one protected EEPROM write.
