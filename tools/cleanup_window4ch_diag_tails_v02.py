"""Remove three obsolete v0.1 DIAG trunk tails retained with local copper."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))
points = [
    pcbnew.VECTOR2I_MM(41.1749, 72.6863),
    pcbnew.VECTOR2I_MM(66.3635, 72.8612),
    pcbnew.VECTOR2I_MM(106.0770, 73.3942),
]

for item in list(board.GetTracks()):
    if item.GetNetname() not in {"CH2_DIAG", "CH3_DIAG", "CH4_DIAG"}:
        continue
    if isinstance(item, pcbnew.PCB_VIA):
        remove = any(item.GetPosition() == point for point in points)
    else:
        remove = any(item.GetStart() == point or item.GetEnd() == point for point in points)
    if remove:
        board.Delete(item)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Removed obsolete historical DIAG tails")
