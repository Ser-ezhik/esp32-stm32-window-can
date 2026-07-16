"""Route the protected 12 V distribution feeding the MP1584 module."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "LOGIC_12V_PROTECTED"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing protected 12 V")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def route(*points):
    for start, end in zip(points, points[1:]):
        item = pcbnew.PCB_TRACK(board)
        item.SetLayer(pcbnew.F_Cu)
        item.SetNet(board.FindNet(NET_NAME))
        item.SetWidth(pcbnew.FromMM(1.00))
        item.SetStart(point(*start))
        item.SetEnd(point(*end))
        board.Add(item)


for item in list(board.GetTracks()):
    if item.GetNetname() == NET_NAME and item.GetLayer() == pcbnew.F_Cu:
        board.Delete(item)

# Main protected 12 V trunk. It stays above the small protection parts and
# keeps a wide clearance from the DC-DC module's ground pads.
route((116.00, 83.00), (158.00, 83.00), (158.30, 86.50))

# Protection diode output and the TVS input share the trunk at the left.
route((112.15, 88.00), (116.00, 83.00))
route((115.85, 88.00), (116.00, 83.00))

# Local input decoupling for the converter.
route((124.53, 88.00), (124.53, 83.00))
route((130.22, 88.00), (130.22, 83.00))
route((128.00, 100.00), (123.00, 100.00), (123.00, 83.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
