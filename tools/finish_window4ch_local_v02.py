"""Add deterministic short local routes around U250 and U270."""

from pathlib import Path

import pcbnew

import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))


def p(reference, number):
    pad = board.FindFootprintByReference(reference).FindPadByNumber(str(number))
    position = pad.GetPosition()
    return round(pcbnew.ToMM(position.x), 4), round(pcbnew.ToMM(position.y), 4)


def path(net, *points, width=0.20):
    for first, second in zip(points, points[1:]):
        router.add_track(board, net, pcbnew.F_Cu, first, second, width)


# EEPROM carrier local pull resistors and supply decoupling.
path("EEPROM_CS", p("U250", 1), (76.5, 107.1), (76.5, 112.0), (87.0, 112.0), p("R260", 1))
path("EEPROM_WP", p("U250", 3), (76.5, 109.635), (76.5, 113.0), (91.0, 113.0), p("R261", 1))
path("EEPROM_HOLD", p("U250", 7), (85.0, 108.365), (85.0, 114.0), (95.0, 114.0), p("R262", 1))
path("S1_3V3", p("U250", 8), (85.5, 107.095), (85.5, 105.0), p("C250", 1), width=0.30)

# Power-fail monitor local connections. Inner board routing already reaches the
# surrounding passives; these traces only close the SOT-23-6 pin fan-out.
path("POWER_GOOD", p("U270", 1), p("U270", 6))
path("POWER_GOOD", p("U270", 1), (98.5, 98.05), (98.5, 97.0), (96.0, 97.0), p("R272", 2))
path("PGOOD_SENSE", p("U270", 3), (98.5, 99.95), (98.5, 102.0), (108.0, 102.0), (108.0, 97.825), p("R271", 1))
path("LOGIC_12V_FUSED", p("U270", 5), p("C270", 1), width=0.80)
path("LOGIC_12V_FUSED", p("U270", 5), (104.5, 100.5), (108.0, 100.5), (108.0, 93.175), p("R270", 1), width=0.80)

board.FindFootprintByReference("C280").Reference().SetVisible(False)
board.FindFootprintByReference("D280").Reference().SetVisible(False)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Added local U250/U270 routes")
