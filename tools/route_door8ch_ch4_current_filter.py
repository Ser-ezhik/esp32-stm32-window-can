"""Complete the local channel 4 current-sense filter and ADC divider node."""

from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "CH4_CURRENT_ADC"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channel 4 current filter")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def add(start, end):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(pcbnew.F_Cu)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetWidth(pcbnew.FromMM(0.25))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


for item in list(board.GetTracks()):
    if item.GetNetname() == NET_NAME and item.GetLayer() == pcbnew.F_Cu:
        pos = item.GetPosition()
        if 118 < pcbnew.ToMM(pos.x) < 124 and 67 < pcbnew.ToMM(pos.y) < 73:
            board.Delete(item)

add((119.94, 72.00), (123.23, 72.00))
add((120.83, 68.00), (119.94, 72.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
