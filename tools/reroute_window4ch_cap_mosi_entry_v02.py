"""Move only the CAP_MOSI header approach from B.Cu to In2.Cu."""

from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))
junction = (124.25, 97.0)

for item in list(board.GetTracks()):
    if item.GetNetname() != "CAP_MOSI" or isinstance(item, pcbnew.PCB_VIA):
        continue
    sx, sy = pcbnew.ToMM(item.GetStart().x), pcbnew.ToMM(item.GetStart().y)
    ex, ey = pcbnew.ToMM(item.GetEnd().x), pcbnew.ToMM(item.GetEnd().y)
    if min(sx, ex) >= 124.249 and min(sy, ey) <= 97.001:
        board.Delete(item)

router.add_via(board, "CAP_MOSI", junction)
grid.GRID = 0.25
grid.CLEARANCE = 0.35
grid.PAD_EXTRA = 0.25
grid.route(board, "CAP_MOSI", pcbnew.In2_Cu, junction, (141.01, 80.215), 0.20)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Moved CAP_MOSI header approach to In2.Cu")
