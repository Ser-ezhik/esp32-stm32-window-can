"""Route the channel 2 VNH current-sense enable strap locally."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "CH2_CS_DIS"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing CH2 CS_DIS")

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


def add_via(x_mm, y_mm):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetPosition(point(x_mm, y_mm))
    item.SetWidth(pcbnew.FromMM(0.80))
    item.SetDrill(pcbnew.FromMM(0.35))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


for item in list(board.GetTracks()):
    if item.GetNetname() == NET_NAME:
        board.Delete(item)

add_track(pcbnew.F_Cu, (44.88, 33.00), (44.00, 33.00))
add_via(44.00, 33.00)
add_track(pcbnew.In1_Cu, (44.00, 33.00), (44.00, 67.00))
add_track(pcbnew.In1_Cu, (44.00, 67.00), (51.00, 67.00))
add_via(51.00, 67.00)
add_track(pcbnew.F_Cu, (51.00, 67.00), (51.18, 68.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
