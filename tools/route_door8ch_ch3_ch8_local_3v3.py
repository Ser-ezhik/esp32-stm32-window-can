"""Tie each channel 3-8 local 3.3 V scaler and protection diode together."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {"S2_3V3", "S3_3V3", "S4_3V3"}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channels 3-8 local 3V3")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def add(net_name, start, end):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(pcbnew.F_Cu)
    item.SetNet(board.FindNet(net_name))
    item.SetWidth(pcbnew.FromMM(0.25))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


def add_via(net_name, position):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(net_name))
    item.SetPosition(point(*position))
    item.SetWidth(pcbnew.FromMM(0.80))
    item.SetDrill(pcbnew.FromMM(0.35))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


def pad_position(reference, pad_number):
    footprint = board.FindFootprintByReference(reference)
    pad = next(pad for pad in footprint.Pads() if pad.GetNumber() == str(pad_number))
    position = pad.GetPosition()
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


for item in list(board.GetTracks()):
    if item.GetNetname() in {"CH5_DIAG", "CH6_DIAG"} and item.GetLayer() == pcbnew.F_Cu:
        position = item.GetPosition()
        if 135 < pcbnew.ToMM(position.x) < 185 and 67 < pcbnew.ToMM(position.y) < 77:
            board.Delete(item)
        continue
    if item.GetNetname() not in NETS:
        continue
    position = item.GetPosition()
    if 70 < pcbnew.ToMM(position.x) < 245 and pcbnew.ToMM(position.y) < 85:
        board.Delete(item)

for channel, slot in ((3, 2), (4, 2), (5, 3), (6, 3)):
    source = pad_position(f"R{1000 + channel * 100 + 7}", 2)
    target = pad_position(f"D{1000 + channel * 100 + 1}", 2)
    route_y = 76.00 if channel >= 5 else 74.00
    net_name = f"S{slot}_3V3"
    if channel >= 5:
        add(net_name, source, target)
    else:
        add(net_name, source, (source[0], route_y))
        add(net_name, (source[0], route_y), (target[0], route_y))
        add(net_name, (target[0], route_y), target)

for net_name, points in (
    ("S4_3V3", ((200.825, 68.00), (200.825, 76.00), (207.00, 76.00), (207.00, 79.00), (209.0625, 78.95))),
    ("S4_3V3", ((230.825, 68.00), (230.825, 75.00), (237.00, 75.00), (237.00, 77.00), (239.0625, 76.95))),
):
    for start, end in zip(points, points[1:]):
        add(net_name, start, end)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
