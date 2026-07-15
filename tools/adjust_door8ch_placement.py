"""Apply a reviewed mechanical adjustment to the DOOR-8CH placement board."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))

# The two mounting holes for each top-side heatsink are placed above and below
# its VNH. This preserves their 26 mm centre spacing while keeping 30 mm
# adjacent channel pitches clear.
for channel, x_mm in enumerate((24, 54, 84, 114, 146, 176, 206, 236), start=1):
    board.FindFootprintByReference(f"HS{channel}A").SetPosition(
        pcbnew.VECTOR2I_MM(x_mm, 35)
    )
    board.FindFootprintByReference(f"HS{channel}B").SetPosition(
        pcbnew.VECTOR2I_MM(x_mm, 61)
    )

pcbnew.SaveBoard(str(BOARD_PATH), board)
