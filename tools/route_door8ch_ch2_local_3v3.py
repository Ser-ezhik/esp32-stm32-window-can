"""Tie channel 2's local 3.3 V current scaler and DIAG pull-up together."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "S1_3V3"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channel 2 local 3V3")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


for item in list(board.GetTracks()):
    if item.GetNetname() != NET_NAME or item.GetLayer() != pcbnew.F_Cu:
        continue
    start = item.GetStart()
    end = item.GetEnd()
    if 35 < min(pcbnew.ToMM(start.x), pcbnew.ToMM(end.x)) and max(pcbnew.ToMM(start.x), pcbnew.ToMM(end.x)) < 70 and max(pcbnew.ToMM(start.y), pcbnew.ToMM(end.y)) < 80:
        board.Delete(item)

for start, end in zip(
    ((48.83, 68.00), (48.83, 74.00), (58.06, 74.00)),
    ((48.83, 74.00), (58.06, 74.00), (58.06, 72.95)),
):
    track = pcbnew.PCB_TRACK(board)
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(board.FindNet(NET_NAME))
    track.SetWidth(pcbnew.FromMM(0.25))
    track.SetStart(point(*start))
    track.SetEnd(point(*end))
    board.Add(track)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
