"""Route the local IN_A, IN_B and PWM chains for VNH channel 2."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {"CH2_INA", "CH2_INB", "CH2_PWM"}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channel 2 controls")

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
    "CH2_INA", pcbnew.In2_Cu, (44.88, 31.00),
    ((37.10, 31.00), (37.10, 70.00), (48.50, 70.00), (48.50, 66.00)),
    (46.83, 64.00),
)
# The PWM changes lanes on In1.Cu to pass around the channel 2 bulk capacitor.
add_track("CH2_PWM", pcbnew.F_Cu, (44.88, 34.00), (38.00, 34.00))
add_via("CH2_PWM", 38.00, 34.00)
for start, end in zip(
    ((38.00, 34.00), (38.00, 50.00), (36.50, 50.00), (36.50, 72.00), (56.50, 72.00)),
    ((38.00, 50.00), (36.50, 50.00), (36.50, 72.00), (56.50, 72.00), (56.50, 66.00)),
):
    add_track("CH2_PWM", pcbnew.In1_Cu, start, end)
add_via("CH2_PWM", 56.50, 66.00)
add_track("CH2_PWM", pcbnew.F_Cu, (56.50, 66.00), (54.83, 64.00))
mixed_route(
    "CH2_INB", pcbnew.In2_Cu, (44.88, 37.00),
    ((43.00, 37.00), (43.00, 65.20), (52.50, 65.20)),
    (50.83, 64.00),
)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
