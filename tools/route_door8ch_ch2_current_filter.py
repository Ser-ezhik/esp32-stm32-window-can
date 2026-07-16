"""Route the channel 2 current-sense filter node locally."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "CH2_CURRENT_ADC"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channel 2 current filter")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


for item in list(board.GetTracks()):
    if item.GetNetname() == NET_NAME:
        board.Delete(item)

track = pcbnew.PCB_TRACK(board)
track.SetLayer(pcbnew.F_Cu)
track.SetNet(board.FindNet(NET_NAME))
track.SetWidth(pcbnew.FromMM(0.25))
track.SetStart(point(59.94, 72.00))
track.SetEnd(point(63.23, 72.00))
board.Add(track)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
