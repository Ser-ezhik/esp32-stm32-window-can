"""Route AMS1117 3.3 V output to its mandatory local decoupling capacitors."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "LOGIC_3V3"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing local 3.3 V")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def route(*points):
    for start, end in zip(points, points[1:]):
        item = pcbnew.PCB_TRACK(board)
        item.SetLayer(pcbnew.F_Cu)
        item.SetNet(board.FindNet(NET_NAME))
        item.SetWidth(pcbnew.FromMM(0.50))
        item.SetStart(point(*start))
        item.SetEnd(point(*end))
        board.Add(item)


for item in list(board.GetTracks()):
    if item.GetNetname() == NET_NAME and item.GetLayer() == pcbnew.F_Cu:
        board.Delete(item)

# Start at the regulator tab/output pad and keep the output capacitors close.
route((182.85, 88.00), (189.15, 88.00))
route((189.15, 88.00), (191.00, 91.00), (196.53, 91.00))
route((197.22, 86.00), (197.22, 91.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
