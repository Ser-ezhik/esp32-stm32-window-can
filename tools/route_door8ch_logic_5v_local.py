"""Route the local 5 V distribution around DC1 and the 3.3 V regulator."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "LOGIC_5V"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing local 5 V")

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

# Main 5 V trunk, positioned between DC1 and the regulator decoupling parts.
route((140.00, 100.50), (145.00, 100.50), (145.00, 95.00), (182.85, 95.00))

# DC1 output decoupling and AMS1117 input network.
route((169.00, 100.00), (169.00, 95.00))
route((163.53, 88.00), (163.53, 95.00))
route((170.22, 88.00), (170.22, 95.00))
route((182.85, 90.30), (182.85, 95.00))
route((176.53, 91.00), (176.53, 95.00))
route((177.22, 86.00), (177.22, 95.00))

# CAP1188 is supplied from the same protected 5 V rail. The route approaches
# its VIN pad horizontally to avoid the adjacent GND pin and mounting hole.
route((182.85, 95.00), (212.00, 95.00), (212.00, 90.80), (221.27, 90.80))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
