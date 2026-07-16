"""Route the local STM32-1 to CAN1 TX/RX connection on B.Cu."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing CAN1 logic")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def route(net_name, *points):
    for item in list(board.GetTracks()):
        if item.GetNetname() == net_name and item.GetLayer() == pcbnew.B_Cu:
            board.Delete(item)

    for start, end in zip(points, points[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetLayer(pcbnew.B_Cu)
        track.SetNet(board.FindNet(net_name))
        track.SetWidth(pcbnew.FromMM(0.25))
        track.SetStart(point(*start))
        track.SetEnd(point(*end))
        board.Add(track)


# Both endpoints are through-hole headers, so B.Cu is a clean local layer.
route(
    "S1_CAN_TX",
    (37.38, 145.38), (42.00, 150.00), (42.00, 158.00),
    (60.00, 158.00), (60.00, 148.78), (64.27, 148.78),
)
route(
    "S1_CAN_RX",
    (34.84, 147.92), (30.00, 152.50), (30.00, 159.00),
    (73.00, 159.00), (73.00, 151.32), (64.27, 151.32),
)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
