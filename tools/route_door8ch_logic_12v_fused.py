"""Connect the dual-pad logic fuse output to the protection diode."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "LOGIC_12V_FUSED"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing fused logic 12 V")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


for item in list(board.GetTracks()):
    if item.GetNetname() == NET_NAME:
        board.Delete(item)

for start, end in (
    ((101.80, 93.00), (101.80, 88.00)),
    ((101.80, 88.00), (107.85, 88.00)),
):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(pcbnew.F_Cu)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetWidth(pcbnew.FromMM(1.00))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
