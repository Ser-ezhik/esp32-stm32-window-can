"""Route 12 V logic input from the edge terminal to the protection fuse."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "LOGIC_12V_IN"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing logic 12 V input")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


for item in list(board.GetTracks()):
    if item.GetNetname() == NET_NAME and item.GetLayer() in {pcbnew.F_Cu, pcbnew.B_Cu}:
        board.Delete(item)

# The route remains inside the left-side keep-clear corridor and enters F230
# from below. Its width matches the protected 12 V distribution.
points = ((5.00, 42.00), (5.00, 46.00), (13.00, 46.00), (13.00, 76.00), (84.00, 76.00), (84.00, 88.00))
for start, end in zip(points, points[1:]):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(pcbnew.F_Cu)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetWidth(pcbnew.FromMM(1.00))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
