"""Route the local IN_A, IN_B and PWM control chains for VNH channel 1."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {"CH1_INA", "CH1_INB", "CH1_PWM"}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channel 1 controls")

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


def clear_routes():
    for item in list(board.GetTracks()):
        if item.GetNetname() in NETS:
            board.Delete(item)


def mixed_route(net_name, inner_layer, front_start, back_points, front_end):
    add_track(net_name, pcbnew.F_Cu, front_start, back_points[0])
    add_via(net_name, *back_points[0])
    for start, end in zip(back_points, back_points[1:]):
        add_track(net_name, inner_layer, start, end)
    add_via(net_name, *back_points[-1])
    add_track(net_name, pcbnew.F_Cu, back_points[-1], front_end)


clear_routes()

# The three short low-current chains use separate routing layers where needed:
# this keeps them clear of the B.Cu CAN and 12 V backbone without adding vias
# in the dense VNH pin field.
mixed_route(
    "CH1_INA", pcbnew.In2_Cu, (14.88, 31.00),
    ((6.90, 31.00), (6.90, 70.00), (18.50, 70.00), (18.50, 66.00)),
    (16.83, 64.00),
)
mixed_route(
    "CH1_PWM", pcbnew.In1_Cu, (14.88, 34.00),
    ((7.65, 34.00), (7.65, 72.00), (26.50, 72.00), (26.50, 66.00)),
    (24.83, 64.00),
)
mixed_route(
    "CH1_INB", pcbnew.In2_Cu, (14.88, 37.00),
    ((13.00, 37.00), (13.00, 65.20), (22.50, 65.20)),
    (20.83, 64.00),
)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
