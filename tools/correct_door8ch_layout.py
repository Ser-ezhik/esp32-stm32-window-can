"""Correct the DOOR-8CH mechanical placement after module-photo review.

Refuses to run while KiCad has the board open, preventing an editor save from
silently overwriting the corrected placement.
"""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
STM_LIBRARY = PROJECT / "DOOR-8CH.pretty"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before applying the correction")

# Load each new module before touching the board. This avoids a KiCad 10 SWIG
# loader issue after removing footprints from a loaded board.
stm_modules = [
    pcbnew.FootprintLoad(str(STM_LIBRARY), "STM32F103C8T6_Mini_CH340_4x10")
    for _ in range(4)
]
hole_modules = [
    pcbnew.FootprintLoad(str(STM_LIBRARY), "MountingHole_M3_2_NPTH")
    for _ in range(4)
]
if any(module is None for module in (*stm_modules, *hole_modules)):
    raise SystemExit("Unable to load the project STM32 module footprint")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def footprint(reference):
    item = board.FindFootprintByReference(reference)
    if item is None:
        raise RuntimeError(f"Missing footprint {reference}")
    return item


def place(reference, x_mm, y_mm, rotation=0):
    item = footprint(reference)
    item.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    item.SetOrientationDegrees(rotation)


# Remove the incorrect split 1x15 representation. The replacement is one
# indivisible 40-pin footprint: four 1x10 rows in the photographed geometry.
for slot in range(1, 5):
    for suffix in ("A", "B"):
        old = board.FindFootprintByReference(f"JSTM{slot}{suffix}")
        if old is not None:
            board.Delete(old)
    old_module = board.FindFootprintByReference(f"MOD{slot}")
    if old_module is not None:
        board.Delete(old_module)

for slot, (module, center_x) in enumerate(
    zip(stm_modules, (45, 105, 165, 225)), start=1
):
    module.SetReference(f"MOD{slot}")
    module.SetValue(f"STM32F103C8T6_MINI_SLOT_S{slot}")
    # Rotation 180 places USB-C toward the lower service edge. The footprint
    # origin is pad 1, so these coordinates centre the 22.86 mm-wide module.
    module.SetPosition(pcbnew.VECTOR2I_MM(center_x + 10.16, 153))
    module.SetOrientationDegrees(180)
    board.Add(module)

for reference in ("H1", "H2", "H3", "H4"):
    old_hole = board.FindFootprintByReference(reference)
    if old_hole is not None:
        board.Delete(old_hole)

for reference, module, (x_mm, y_mm) in zip(
    ("H1", "H2", "H3", "H4"),
    hole_modules,
    ((8, 75), (230, 75), (8, 152), (252, 152)),
):
    module.SetReference(reference)
    module.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    module.Reference().SetVisible(False)
    board.Add(module)

# Every motor-power and actuator connector is now edge-mounted. Input/output
# terminals are paired per channel, making cabinet wiring readable at a glance.
channel_centres = (24, 54, 84, 114, 146, 176, 206, 236)
for channel, center_x in enumerate(channel_centres, start=1):
    place(f"J{channel}", center_x - 9.04, 8, 0)
    place(f"J{channel + 8}", center_x + 3.96, 8, 0)
    place(f"U{channel}", center_x, 35, 0)
    place(f"HS{channel}A", center_x, 22, 0)
    place(f"HS{channel}B", center_x, 48, 0)

# Quiet-side control connectors also face board edges. J101-J103 are absent
# after generic headers have been replaced by complete module footprints.
for reference, x_mm, y_mm, rotation in (
    ("J101", 7, 100, 270),
    ("J102", 7, 120, 270),
    ("J103", 7, 140, 270),
    ("J104", 253, 100, 90),
    ("J105", 253, 120, 90),
):
    if board.FindFootprintByReference(reference) is not None:
        place(reference, x_mm, y_mm, rotation)

# Remove obsolete board-level placement boxes/text. Footprint silk, references,
# the board outline and all component geometry are retained.
for drawing in list(board.GetDrawings()):
    if drawing.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
        board.Delete(drawing)

# Dense power-stage references are documented in the schematic and assembly
# drawing. Hiding them here prevents silkscreen text from crossing VNH bodies.
for item in board.GetFootprints():
    reference = item.GetReference()
    if reference.startswith("HS") or reference in ("H1", "H2", "H3", "H4"):
        item.Reference().SetVisible(False)

pcbnew.SaveBoard(str(BOARD_PATH), board)
