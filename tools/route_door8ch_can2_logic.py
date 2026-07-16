"""Route ESP32 CAN GPIOs to the nearby CAN2 transceiver on B.Cu."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing CAN2 logic")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def track(net_name, layer, start, end):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(layer)
    item.SetNet(board.FindNet(net_name))
    item.SetWidth(pcbnew.FromMM(0.25))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


def via(net_name, x_mm, y_mm):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(net_name))
    item.SetPosition(point(x_mm, y_mm))
    item.SetWidth(pcbnew.FromMM(0.80))
    item.SetDrill(pcbnew.FromMM(0.35))
    item.SetLayerPair(pcbnew.B_Cu, pcbnew.F_Cu)
    board.Add(item)


def route(net_name, *points):
    for item in list(board.GetTracks()):
        if item.GetNetname() == net_name and (
            item.GetLayer() == pcbnew.B_Cu or isinstance(item, pcbnew.PCB_VIA)
        ):
            board.Delete(item)

    for start, end in zip(points, points[1:]):
        track(net_name, pcbnew.B_Cu, start, end)


# The two horizontal lanes above the module headers are free of PTH pads.
route(
    "ESP_CAN_TX_GPIO39",
    (28.32, 82.14), (28.32, 78.00), (20.00, 78.00), (20.00, 64.00), (145.00, 64.00),
    (145.00, 148.78),
)

# The last TX segment crosses the RX route only on the top layer.
via("ESP_CAN_TX_GPIO39", 145.00, 148.78)
track("ESP_CAN_TX_GPIO39", pcbnew.F_Cu, (145.00, 148.78), (124.27, 148.78))
route(
    "ESP_CAN_RX_GPIO38",
    (30.86, 82.14), (35.00, 78.00), (35.00, 72.00), (137.00, 72.00),
    (137.00, 151.32), (124.27, 151.32),
)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
