"""Route the local IN_A, IN_B and PWM control chains for VNH channel 3."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {"CH3_INA", "CH3_INB", "CH3_PWM"}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channel 3 controls")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def add_track(net_name, layer, start, end):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(layer)
    item.SetNet(board.FindNet(net_name))
    item.SetWidth(pcbnew.FromMM(0.25))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


def add_via(net_name, x_mm, y_mm):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(net_name))
    item.SetPosition(point(x_mm, y_mm))
    item.SetWidth(pcbnew.FromMM(0.80))
    item.SetDrill(pcbnew.FromMM(0.35))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


def mixed_route(net_name, inner_layer, front_start, inner_points, front_end):
    add_track(net_name, pcbnew.F_Cu, front_start, inner_points[0])
    add_via(net_name, *inner_points[0])
    for start, end in zip(inner_points, inner_points[1:]):
        add_track(net_name, inner_layer, start, end)
    add_via(net_name, *inner_points[-1])
    add_track(net_name, pcbnew.F_Cu, inner_points[-1], front_end)


for item in list(board.GetTracks()):
    if item.GetNetname() in NETS:
        board.Delete(item)

mixed_route(
    "CH3_INA", pcbnew.In2_Cu, (74.88, 31.00),
    ((66.93, 31.00), (66.93, 70.00), (78.50, 70.00), (78.50, 66.00)),
    (76.83, 64.00),
)
mixed_route(
    "CH3_PWM", pcbnew.In1_Cu, (74.88, 34.00),
    ((67.675, 34.00), (67.675, 72.00), (86.50, 72.00), (86.50, 66.00)),
    (84.83, 64.00),
)
mixed_route(
    "CH3_INB", pcbnew.In2_Cu, (74.88, 37.00),
    ((73.00, 37.00), (73.00, 65.20), (82.50, 65.20)),
    (80.83, 64.00),
)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
