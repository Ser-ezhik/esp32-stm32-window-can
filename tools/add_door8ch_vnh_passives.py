"""Add the repeated VNH5019 passive and current-sense blocks to DOOR-8CH."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
KICAD_FP = Path(
    r"C:\Users\Ezhik\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
)

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before adding VNH passives")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def add(library, name, reference, value, x_mm, y_mm, rotation=0):
    existing = board.FindFootprintByReference(reference)
    if existing:
        existing.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
        existing.SetOrientationDegrees(rotation)
        existing.Reference().SetVisible(False)
        existing.Value().SetVisible(False)
        return
    item = pcbnew.FootprintLoad(str(KICAD_FP / library), name)
    if item is None:
        raise RuntimeError(f"Unable to load {library}/{name}")
    item.SetReference(reference)
    item.SetValue(value)
    item.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    item.SetOrientationDegrees(rotation)
    item.Reference().SetVisible(False)
    item.Value().SetVisible(False)
    board.Add(item)


RESISTOR = ("Resistor_SMD.pretty", "R_0603_1608Metric")
CERAMIC = ("Capacitor_SMD.pretty", "C_0603_1608Metric")
ELECTROLYTIC = ("Capacitor_THT.pretty", "CP_Radial_D10.0mm_P5.00mm")
CLAMP_DIODE = ("Package_TO_SOT_SMD.pretty", "SOT-23")

channel_centres = (24, 54, 84, 114, 146, 176, 206, 236)
resistor_values = (
    "100R INA_SER",
    "100R INB_SER",
    "100R PWM_SER",
    "10K INA_PULLDOWN",
    "10K INB_PULLDOWN",
    "10K PWM_PULLDOWN",
    "4K7 DIAG_PULLUP",
    "10K CS_DIS_PULLDOWN",
    "1K 1% CS_LOAD",
    "10K ADC_SERIES",
)
resistor_positions = (
    (-8, 64),
    (-4, 64),
    (0, 64),
    (4, 64),
    (8, 64),
    (12, 64),
    (-6, 68),
    (-2, 68),
    (2, 68),
    (6, 68),
)

for channel, center_x in enumerate(channel_centres, start=1):
    reference_base = 1000 + channel * 100
    for index, (value, (dx, y_mm)) in enumerate(
        zip(resistor_values, resistor_positions), start=1
    ):
        add(*RESISTOR, f"R{reference_base + index}", value, center_x + dx, y_mm)

    bulk_x, bulk_y = center_x - 8, 76
    if channel in (1, 2):
        bulk_y = 74
    elif channel == 7:
        bulk_x, bulk_y = 191, 74
    elif channel == 8:
        bulk_x, bulk_y = 218, 70

    add(
        *ELECTROLYTIC,
        f"C{reference_base + 1}",
        "470uF 35V LOW_ESR",
        bulk_x,
        bulk_y,
    )
    small_x = 214 if channel == 7 else (244 if channel == 8 else center_x + 10)
    ceramic_y = 78 if channel == 7 else (74 if channel == 8 else 68)
    add(
        *CERAMIC,
        f"C{reference_base + 2}",
        "100nF 50V X7R VCC",
        small_x,
        ceramic_y,
    )
    filter_x, filter_y = small_x, ceramic_y + 4
    if channel == 7:
        filter_x, filter_y = 208, 82
    add(
        *CERAMIC,
        f"C{reference_base + 3}",
        "100nF ADC_FILTER",
        filter_x,
        filter_y,
    )
    add(
        *CLAMP_DIODE,
        f"D{reference_base + 1}",
        "BAT54S ADC_CLAMP",
        210 if channel == 7 else (240 if channel == 8 else center_x + 5),
        78 if channel == 7 else (76 if channel == 8 else 72),
    )

pcbnew.SaveBoard(str(BOARD_PATH), board)
