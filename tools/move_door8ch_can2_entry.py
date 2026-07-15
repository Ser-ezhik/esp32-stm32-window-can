"""Move the CAN trunk entry next to CAN2 and shift MOD3 away from that area."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before moving the CAN entry")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def place(reference, x_mm, y_mm, rotation=None):
    item = board.FindFootprintByReference(reference)
    if item is None:
        raise RuntimeError(f"Missing footprint {reference}")
    item.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    if rotation is not None:
        item.SetOrientationDegrees(rotation)


# MOD3 is shifted right to open a low-voltage CAN-entry pocket beside CAN2.
place("MOD3", 195.16, 153, 180)
place("R3031", 183, 120)
place("R3032", 187, 120)

pcbnew.SaveBoard(str(BOARD_PATH), board)
