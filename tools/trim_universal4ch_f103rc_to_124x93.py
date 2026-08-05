"""Trim the approved compact 4CH placement to a 124 x 93 mm outline."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = (
    ROOT
    / "hardware"
    / "UNIVERSAL-4CH-F103RC-IC"
    / "kicad"
    / "UNIVERSAL-4CH-F103RC-IC.kicad_pcb"
)


def vector(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


board = pcbnew.LoadBoard(str(BOARD_PATH))
edge_box = board.GetBoardEdgesBoundingBox()
current_width = pcbnew.ToMM(edge_box.GetWidth())

# Repair the rejected trial where only the two outer heatsink holes were moved.
# This branch makes the script safe to run on that intermediate file and then
# becomes a no-op once the correct 124 x 93 mm geometry is present.
if current_width < 125.0:
    u1_x = pcbnew.ToMM(board.FindFootprintByReference("U1").GetPosition().x)
    hs1_x = pcbnew.ToMM(board.FindFootprintByReference("HS1A").GetPosition().x)
    if abs((u1_x - hs1_x) - 10.5) < 0.1:
        board.FindFootprintByReference("HS1A").Move(vector(-1.5, 0.0))
        board.FindFootprintByReference("HS4B").Move(vector(1.5, 0.0))
        correction = vector(-0.055, 0.0)
        for footprint in board.GetFootprints():
            footprint.Move(correction)
        for drawing in board.GetDrawings():
            if drawing.GetLayer() != pcbnew.Edge_Cuts:
                drawing.Move(correction)
        pcbnew.SaveBoard(str(BOARD_PATH), board)
        print(f"Repaired and trimmed {BOARD_PATH}")
        print("Board: 124.0 x 93.0 mm")
    else:
        print("Board is already trimmed to 124.0 x 93.0 mm")
    raise SystemExit(0)

# The actuator connectors and the reed/CAN connectors remain aligned along
# their respective board edges while gaining useful assembly clearance.
for reference in ("J1", "J2", "J3", "J4"):
    board.FindFootprintByReference(reference).Move(vector(0.0, 1.5))

for reference in ("J230", "J240", "J201", "J202", "J203"):
    board.FindFootprintByReference(reference).Move(vector(0.0, -1.5))

# Rebase the whole placement to a conventional 0,0 board origin.
rebase = vector(-1.055, -1.5)
for footprint in board.GetFootprints():
    footprint.Move(rebase)

for drawing in list(board.GetDrawings()):
    if drawing.GetLayer() == pcbnew.Edge_Cuts:
        board.Delete(drawing)
    else:
        drawing.Move(rebase)

outline = pcbnew.PCB_SHAPE(board)
outline.SetShape(pcbnew.SHAPE_T_RECT)
outline.SetLayer(pcbnew.Edge_Cuts)
outline.SetStart(vector(0.0, 0.0))
outline.SetEnd(vector(124.0, 93.0))
outline.SetWidth(pcbnew.FromMM(0.05))
board.Add(outline)

pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Trimmed {BOARD_PATH}")
print("Board: 124.0 x 93.0 mm")
