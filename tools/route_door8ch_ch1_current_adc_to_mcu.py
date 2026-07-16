"""Route the filtered current measurement of channel 1 to STM32 slot S1."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "CH1_CURRENT_ADC"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing CH1 ADC input")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def add_track(layer, start, end):
    track = pcbnew.PCB_TRACK(board)
    track.SetLayer(layer)
    track.SetNet(board.FindNet(NET_NAME))
    track.SetWidth(pcbnew.FromMM(0.25))
    track.SetStart(point(*start))
    track.SetEnd(point(*end))
    board.Add(track)


def add_via(x_mm, y_mm):
    via = pcbnew.PCB_VIA(board)
    via.SetNet(board.FindNet(NET_NAME))
    via.SetPosition(point(x_mm, y_mm))
    via.SetWidth(pcbnew.FromMM(0.80))
    via.SetDrill(pcbnew.FromMM(0.35))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(via)


for item in list(board.GetTracks()):
    if item.GetNetname() != NET_NAME:
        continue
    pos = item.GetPosition()
    if 31 < pcbnew.ToMM(pos.x) < 54 and 69 < pcbnew.ToMM(pos.y) < 131:
        board.Delete(item)

add_track(pcbnew.F_Cu, (30.83, 68.00), (32.00, 70.00))
add_via(32.00, 70.00)
add_track(pcbnew.In2_Cu, (32.00, 70.00), (32.00, 127.00))
add_track(pcbnew.In2_Cu, (32.00, 127.00), (52.62, 127.00))
add_via(52.62, 127.00)
add_track(pcbnew.F_Cu, (52.62, 127.00), (52.62, 130.14))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
