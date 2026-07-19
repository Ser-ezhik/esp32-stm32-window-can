"""Route the final two nets displaced by restored DIAG copper."""

from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))


def position(reference, number):
    pad = board.FindFootprintByReference(reference).FindPadByNumber(str(number))
    p = pad.GetPosition()
    return round(pcbnew.ToMM(p.x), 4), round(pcbnew.ToMM(p.y), 4)


grid.GRID = 0.25
grid.CLEARANCE = 0.35
grid.PAD_EXTRA = 0.25
router.route_multilayer(
    board, "CH4_INA_MCU", position("MOD2", 26), position("R1401", 1),
    0.20, None, pcbnew.F_Cu, False,
)
pcbnew.SaveBoard(str(BOARD_PATH), board)

grid.GRID = 0.25
grid.CLEARANCE = 0.32
grid.PAD_EXTRA = 0.0
router.route_multilayer(
    board, "CAP_MOSI", position("MOD1", 7), position("U250", 5),
    0.20, None, pcbnew.F_Cu, False,
)
router.route_multilayer(
    board, "CAP_MOSI", position("U250", 5), position("CAP1", 14),
    0.20, pcbnew.F_Cu, pcbnew.F_Cu, True,
)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Routed CH4_INA_MCU and CAP_MOSI")
