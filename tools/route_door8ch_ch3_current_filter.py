"""Complete the local channel 3 current-sense filter and ADC divider node."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "CH3_CURRENT_ADC"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channel 3 current filter")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


for item in list(board.GetTracks()):
    if item.GetNetname() != NET_NAME or item.GetLayer() != pcbnew.F_Cu:
        continue
    pos = item.GetPosition()
    if 88 < pcbnew.ToMM(pos.x) < 94 and 67 < pcbnew.ToMM(pos.y) < 73:
        board.Delete(item)


def add(start, end):
    track = pcbnew.PCB_TRACK(board)
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(board.FindNet(NET_NAME))
    track.SetWidth(pcbnew.FromMM(0.25))
    track.SetStart(point(*start))
    track.SetEnd(point(*end))
    board.Add(track)


add((89.94, 72.00), (93.23, 72.00))
add((90.83, 68.00), (89.94, 72.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
