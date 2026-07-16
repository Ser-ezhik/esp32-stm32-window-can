"""Route the CANH/CANL trunk from L240 to CAN1 and CAN2 on In1.Cu."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing the CAN trunk")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def net(name):
    item = board.FindNet(name)
    if item is None:
        raise RuntimeError(f"Missing net {name}")
    return item


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def track(net_name, layer, start, end, width_mm=0.30):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(layer)
    item.SetNet(net(net_name))
    item.SetWidth(pcbnew.FromMM(width_mm))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


def via(net_name, x_mm, y_mm, inner_layer=pcbnew.In1_Cu):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(net(net_name))
    item.SetPosition(point(x_mm, y_mm))
    item.SetWidth(pcbnew.FromMM(0.80))
    item.SetDrill(pcbnew.FromMM(0.35))
    item.SetLayerPair(pcbnew.F_Cu, inner_layer)
    board.Add(item)


def route(net_name, layer, *points):
    for start, end in zip(points, points[1:]):
        track(net_name, layer, start, end)


# Clear the two bus nets. The CAN entry pocket uses separate *_ENTRY nets and
# is left intact; rebuilding the bus pocket prevents a hidden crossing there.
for item in list(board.GetTracks()):
    if item.GetNetname() in {"CANH_BUS", "CANL_BUS"} and not isinstance(item, pcbnew.PCB_VIA):
        board.Delete(item)
    elif isinstance(item, pcbnew.PCB_VIA) and item.GetNetname() in {"CANH_BUS", "CANL_BUS"}:
        board.Delete(item)

# L240 output pins are SMD on F.Cu. The two short paths fan out above the
# entry nets, then meet the optional termination and change layer.
route("CANH_BUS", pcbnew.F_Cu, (158.87, 141.16), (160.00, 140.00), (156.00, 137.00), (156.00, 135.00), (156.54, 135.00))
route("CANL_BUS", pcbnew.F_Cu, (158.87, 144.84), (162.00, 143.00), (162.00, 135.00), (159.46, 135.00))
via("CANH_BUS", 160.00, 140.00)
via("CANL_BUS", 162.00, 143.00, pcbnew.In2_Cu)

# In1 trunk and two short branches. CAN2/CAN1 pins are through-hole and touch
# the inner layer directly. The two routes stay paired on their shared spine.
route(
    "CANH_BUS", pcbnew.In1_Cu,
    (160.00, 140.00), (148.00, 140.00), (148.00, 110.00), (68.00, 110.00), (68.00, 153.86),
    (64.27, 153.86),
)
route("CANH_BUS", pcbnew.In1_Cu, (148.00, 110.00), (128.00, 110.00))
route("CANH_BUS", pcbnew.In1_Cu, (128.00, 110.00), (128.00, 153.86), (124.27, 153.86))
route(
    "CANL_BUS", pcbnew.In2_Cu,
    (162.00, 143.00), (155.00, 143.00), (155.00, 112.00), (70.00, 112.00), (70.00, 156.40),
    (64.27, 156.40),
)
route("CANL_BUS", pcbnew.In2_Cu, (150.00, 112.00), (140.00, 112.00), (140.00, 156.40), (124.27, 156.40))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
