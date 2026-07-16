"""Apply a reviewed mechanical adjustment to the DOOR-8CH placement board."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))

# The VNH stages sit close to the edge-mounted motor terminals. Their two
# top-side heatsink holes remain at 26 mm centres while keeping room below the
# drivers for the local 470 uF supply capacitors.
for channel, x_mm in enumerate((24, 54, 84, 114, 146, 176, 206, 234), start=1):
    board.FindFootprintByReference(f"U{channel}").SetPosition(
        pcbnew.VECTOR2I_MM(x_mm, 35)
    )
    board.FindFootprintByReference(f"HS{channel}A").SetPosition(
        pcbnew.VECTOR2I_MM(x_mm, 22)
    )
    board.FindFootprintByReference(f"HS{channel}B").SetPosition(
        pcbnew.VECTOR2I_MM(x_mm, 48)
    )

pcbnew.SaveBoard(str(BOARD_PATH), board)
