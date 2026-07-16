"""Join channel 7/8 local 3.3 V nodes and feed STM32 slot S4."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "S4_3V3"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing S4 3V3 distribution")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def add_track(layer, start, end):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(layer)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetWidth(pcbnew.FromMM(0.40))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


def add_via(position):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetPosition(point(*position))
    item.SetWidth(pcbnew.FromMM(0.90))
    item.SetDrill(pcbnew.FromMM(0.40))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


for item in list(board.GetTracks()):
    if item.GetNetname() != NET_NAME:
        continue
    if isinstance(item, pcbnew.PCB_VIA) or item.GetLayer() != pcbnew.F_Cu:
        board.Delete(item)
        continue
    start = item.GetStart()
    end = item.GetEnd()
    segment = frozenset({
        (round(pcbnew.ToMM(start.x), 3), round(pcbnew.ToMM(start.y), 3)),
        (round(pcbnew.ToMM(end.x), 3), round(pcbnew.ToMM(end.y), 3)),
    })
    owned_segments = {
        frozenset({(207.000, 79.000), (207.000, 86.000)}),
        frozenset({(237.000, 77.000), (237.000, 82.000)}),
        frozenset({(200.825, 76.000), (198.000, 82.000)}),
        frozenset({(198.000, 82.000), (198.000, 100.000)}),
        frozenset({(237.000, 77.000), (244.000, 82.000)}),
        frozenset({(244.000, 82.000), (244.000, 100.000)}),
        frozenset({(198.000, 82.000), (198.000, 108.000)}),
        frozenset({(237.000, 77.000), (250.000, 84.000)}),
        frozenset({(250.000, 84.000), (250.000, 108.000)}),
        frozenset({(198.000, 82.000), (198.000, 116.000)}),
        frozenset({(250.000, 84.000), (250.000, 116.000)}),
        frozenset({(198.000, 82.000), (198.000, 121.500)}),
        frozenset({(250.000, 84.000), (250.000, 121.500)}),
    }
    if segment in owned_segments:
        board.Delete(item)

# Extend from vertices already owned by the local CH7/CH8 3.3 V helper,
# staying outside the CAP1188 module before joining on B.Cu below it.
add_track(pcbnew.F_Cu, (200.825, 76.00), (198.00, 82.00))
add_via((198.00, 82.00))
add_track(pcbnew.B_Cu, (198.00, 82.00), (198.00, 121.50))

add_track(pcbnew.F_Cu, (237.00, 77.00), (250.00, 84.00))
add_track(pcbnew.F_Cu, (250.00, 84.00), (250.00, 121.50))
add_via((250.00, 121.50))

add_track(pcbnew.B_Cu, (198.00, 121.50), (250.00, 121.50))
add_track(pcbnew.B_Cu, (228.00, 121.50), (228.00, 153.00))
add_track(pcbnew.B_Cu, (228.00, 153.00), (232.62, 153.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
