"""Route the local IN_A, IN_B and PWM control chains for VNH channel 4."""

from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {"CH4_INA", "CH4_INB", "CH4_PWM"}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channel 4 controls")

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


def route(net_name, layer, start, points, end):
    add_track(net_name, pcbnew.F_Cu, start, points[0])
    add_via(net_name, *points[0])
    for a, b in zip(points, points[1:]):
        add_track(net_name, layer, a, b)
    add_via(net_name, *points[-1])
    add_track(net_name, pcbnew.F_Cu, points[-1], end)


for item in list(board.GetTracks()):
    if item.GetNetname() in NETS:
        board.Delete(item)

route("CH4_INA", pcbnew.In2_Cu, (104.88, 31.00), ((96.93, 31.00), (96.93, 70.00), (108.50, 70.00), (108.50, 66.00)), (106.83, 64.00))
route("CH4_PWM", pcbnew.In1_Cu, (104.88, 34.00), ((97.675, 34.00), (97.675, 72.00), (116.50, 72.00), (116.50, 66.00)), (114.83, 64.00))
route("CH4_INB", pcbnew.In2_Cu, (104.88, 37.00), ((103.00, 37.00), (103.00, 65.20), (112.50, 65.20)), (110.83, 64.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
