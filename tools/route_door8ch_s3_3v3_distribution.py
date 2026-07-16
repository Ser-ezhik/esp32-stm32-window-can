"""Join channel 5/6 local 3.3 V nodes and feed STM32 slot S3."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "S3_3V3"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing S3 3V3 distribution")

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


owned_segments = {
    frozenset({(150.062, 72.950), (150.062, 75.000)}),
    frozenset({(150.062, 75.000), (152.000, 78.000)}),
    frozenset({(180.062, 72.950), (180.062, 78.000)}),
    frozenset({(183.825, 120.000), (183.825, 122.000)}),
    frozenset({(183.825, 120.000), (183.825, 117.000)}),
    frozenset({(183.825, 117.000), (180.000, 117.000)}),
}
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
    if segment in owned_segments:
        board.Delete(item)

# Join both local channel rails above the long control/telemetry corridors.
add_track(pcbnew.F_Cu, (150.0625, 72.95), (150.0625, 75.00))
add_track(pcbnew.F_Cu, (150.0625, 75.00), (152.00, 78.00))
add_via((152.00, 78.00))

add_track(pcbnew.F_Cu, (180.0625, 72.95), (180.0625, 78.00))
add_via((180.0625, 78.00))

add_track(pcbnew.In2_Cu, (152.00, 78.00), (180.0625, 78.00))
add_track(pcbnew.In2_Cu, (164.00, 78.00), (164.00, 128.00))
add_track(pcbnew.In2_Cu, (164.00, 128.00), (188.00, 128.00))
add_track(pcbnew.In2_Cu, (188.00, 128.00), (188.00, 153.00))
add_track(pcbnew.In2_Cu, (188.00, 153.00), (192.62, 153.00))

# R3031 is approached vertically so the adjacent slot-ID resistor is clear.
add_track(pcbnew.F_Cu, (183.825, 120.00), (183.825, 117.00))
add_track(pcbnew.F_Cu, (183.825, 117.00), (180.00, 117.00))
add_via((180.00, 117.00))
add_track(pcbnew.B_Cu, (180.00, 117.00), (164.00, 117.00))
add_via((164.00, 117.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
