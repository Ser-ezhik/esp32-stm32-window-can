"""Move CAP1188 VIN from 5 V to the board 3.3 V rail."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
LOCK_PATH = BOARD_PATH.parent / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before changing CAP1188 power")

board = pcbnew.LoadBoard(str(BOARD_PATH))
cap = board.FindFootprintByReference("CAP1")
for pad in cap.Pads():
    if pad.GetNumber() == "3":
        pad.SetNet(board.FindNet("LOGIC_3V3"))
        break
else:
    raise RuntimeError("CAP1.3 was not found")

pcbnew.SaveBoard(str(BOARD_PATH), board)
