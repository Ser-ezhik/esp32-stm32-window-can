"""Route the compact protected CAN entry beside J240 on the DOOR-8CH PCB."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing the CAN entry")

board = pcbnew.LoadBoard(str(BOARD_PATH))

# Re-running this helper replaces only the entry-pocket tracks. Do not use it
# after the long CANH/CANL trunk has been added elsewhere on F.Cu.
ENTRY_NETS = {"CANH_ENTRY", "CANL_ENTRY", "CANH_BUS", "CANL_BUS"}
for item in list(board.GetTracks()):
    if item.GetLayer() == pcbnew.F_Cu and item.GetNetname() in ENTRY_NETS:
        board.Delete(item)


def net(name):
    item = board.FindNet(name)
    if item is None:
        raise RuntimeError(f"Missing net {name}")
    return item


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def segment(net_name, start, end, width_mm=0.30):
    track = pcbnew.PCB_TRACK(board)
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(net(net_name))
    track.SetWidth(pcbnew.FromMM(width_mm))
    track.SetStart(point(*start))
    track.SetEnd(point(*end))
    board.Add(track)


def route(net_name, *points):
    for start, end in zip(points, points[1:]):
        segment(net_name, start, end)


# These routes intentionally cover only the protected entry pocket. The CANH/
# CANL trunk to CAN1/CAN2 is routed later as a matched pair on an inner layer.
# Coordinates land on the actual pad centres captured from the board.
route(
    "CANH_ENTRY",
    (158.00, 152.00), (153.00, 148.00), (153.00, 141.05),
    (157.13, 141.05), (157.13, 141.16),  # J240.1 -> L240.1
)
route(
    "CANH_ENTRY",
    (153.00, 141.05), (147.00, 141.05),  # -> D240.1
)
route(
    "CANL_ENTRY",
    (161.50, 152.00), (164.00, 148.00), (164.00, 146.00),
    (157.13, 146.00), (157.13, 144.84),  # J240.2 -> L240.2
)
route(
    "CANL_ENTRY",
    (164.00, 146.00), (172.00, 146.00), (172.00, 141.05),
    (169.00, 141.05),  # -> D241.1
)
route(
    "CANH_BUS",
    (158.87, 141.16), (160.00, 140.00), (156.00, 137.00),
    (156.00, 135.00), (156.54, 135.00),  # L240.4 -> R240.1
)
route(
    "CANL_BUS",
    (158.87, 144.84), (164.00, 144.84), (164.00, 135.00),
    (159.46, 135.00),  # L240.3 -> R240.2
)

pcbnew.SaveBoard(str(BOARD_PATH), board)
