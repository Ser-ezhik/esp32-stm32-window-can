"""Add the selected board-mounted MP1584 module and its protected logic input."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
PROJECT_LIBRARY = PROJECT / "DOOR-8CH.pretty"
KICAD_FOOTPRINTS = Path(
    r"C:\Users\Ezhik\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
)

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before changing the power module")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def remove(reference):
    item = board.FindFootprintByReference(reference)
    if item is not None:
        board.Delete(item)


def load(library, name):
    item = pcbnew.FootprintLoad(str(library), name)
    if item is None:
        raise RuntimeError(f"Unable to load {library}/{name}")
    return item


def add(reference, value, library, name, x_mm, y_mm, rotation=0):
    remove(reference)
    item = load(library, name)
    item.SetReference(reference)
    item.SetValue(value)
    item.Value().SetVisible(False)
    item.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    item.SetOrientationDegrees(rotation)
    board.Add(item)
    return item


# Dedicated protected 12 V logic entry at the left board edge.
add(
    "J230", "LOGIC_12V_GND", KICAD_FOOTPRINTS / "TerminalBlock_Phoenix.pretty",
    "TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal", 5, 60, 90,
)

# Serviceable 1 A branch fuse and protection parts before the buck module.
add(
    "F230", "1A_SLOW_5X20", KICAD_FOOTPRINTS / "Fuse.pretty",
    "Fuseholder_Clip-5x20mm_Bel_FC-203-22_Lateral_P17.80x5.00mm_D1.17mm_Horizontal",
    17, 67,
)
add(
    "D230", "SS54_REVERSE_POLARITY", KICAD_FOOTPRINTS / "Diode_SMD.pretty",
    "D_SMB", 42, 67,
)
add(
    "D231", "SMBJ16A_TVS", KICAD_FOOTPRINTS / "Diode_SMD.pretty",
    "D_SMB", 54, 67,
)
add(
    "C230", "470UF_50V", KICAD_FOOTPRINTS / "Capacitor_THT.pretty",
    "CP_Radial_D10.0mm_P5.00mm", 68, 68,
)
add(
    "C231", "1UF_50V", KICAD_FOOTPRINTS / "Capacitor_SMD.pretty",
    "C_1206_3216Metric", 81, 66,
)
add(
    "C232", "100NF_50V", KICAD_FOOTPRINTS / "Capacitor_SMD.pretty",
    "C_0603_1608Metric", 87, 66,
)

# Socketed/soldered module in the quiet central zone. Oversized carrier pads
# tolerate small vendor differences, but the purchased batch must be checked
# against the nominal 22.3 x 17 mm body before Gerber release.
add(
    "DC1", "MP1584_FIXED_5V", PROJECT_LIBRARY,
    "MP1584_Fixed5V_Module_22.3x17mm", 100, 65,
)
add(
    "C233", "220UF_10V", KICAD_FOOTPRINTS / "Capacitor_THT.pretty",
    "CP_Radial_D8.0mm_P3.50mm", 128, 68,
)
add(
    "C234", "10UF_10V", KICAD_FOOTPRINTS / "Capacitor_SMD.pretty",
    "C_1206_3216Metric", 140, 66,
)
add(
    "C235", "100NF_16V", KICAD_FOOTPRINTS / "Capacitor_SMD.pretty",
    "C_0603_1608Metric", 146, 66,
)

pcbnew.SaveBoard(str(BOARD_PATH), board)

