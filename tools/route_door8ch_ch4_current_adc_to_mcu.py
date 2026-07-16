"""Route filtered channel 4 current measurement to STM32 slot S2."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "CH4_CURRENT_ADC"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing CH4 ADC input")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def add_track(layer, start, end):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(layer)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetWidth(pcbnew.FromMM(0.25))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


def add_via(position):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetPosition(point(*position))
    item.SetWidth(pcbnew.FromMM(0.80))
    item.SetDrill(pcbnew.FromMM(0.35))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


for item in list(board.GetTracks()):
    if item.GetNetname() != NET_NAME:
        continue
    if isinstance(item, pcbnew.PCB_VIA) or item.GetLayer() != pcbnew.F_Cu:
        board.Delete(item)
        continue
    position = item.GetPosition()
    if pcbnew.ToMM(position.y) > 73:
        board.Delete(item)

add_track(pcbnew.F_Cu, (120.825, 68.00), (124.00, 70.00))
add_via((124.00, 70.00))
add_track(pcbnew.In1_Cu, (124.00, 70.00), (124.00, 105.00))
add_via((124.00, 105.00))
add_track(pcbnew.F_Cu, (124.00, 105.00), (128.00, 120.00))
add_track(pcbnew.F_Cu, (128.00, 120.00), (130.00, 126.00))
add_track(pcbnew.F_Cu, (130.00, 126.00), (115.16, 126.00))
add_track(pcbnew.F_Cu, (115.16, 126.00), (115.16, 130.14))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
