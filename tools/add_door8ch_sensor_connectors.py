"""Replace preliminary sensor headers with edge-mounted field connectors."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
KICAD_FOOTPRINTS = Path(
    r"C:\Users\Ezhik\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
)

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before changing sensor connectors")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def remove(reference):
    for item in list(board.GetFootprints()):
        if item.GetReference() == reference:
            board.Delete(item)


def load(library, name):
    item = pcbnew.FootprintLoad(str(KICAD_FOOTPRINTS / library), name)
    if item is None:
        raise RuntimeError(f"Unable to load {library}/{name}")
    return item


def add_terminal(reference, value, pins, y_mm):
    name = (
        f"TerminalBlock_Phoenix_PT-1,5-{pins}-3.5-H_"
        f"1x{pins:02d}_P3.50mm_Horizontal"
    )
    item = load("TerminalBlock_Phoenix.pretty", name)
    item.SetReference(reference)
    item.SetValue(value)
    item.Reference().SetVisible(True)
    item.Value().SetVisible(False)
    item.SetPosition(pcbnew.VECTOR2I_MM(254.7, y_mm))
    item.SetOrientationDegrees(90)
    board.Add(item)


def add_resistor(reference, value, x_mm, y_mm):
    item = load("Resistor_SMD.pretty", "R_0603_1608Metric")
    item.SetReference(reference)
    item.SetValue(value)
    item.Value().SetVisible(False)
    item.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    item.SetOrientationDegrees(90)
    board.Add(item)
    return item


# Remove the two preliminary generic sockets and make this script repeatable.
for reference in ("J104", "J105", "J220"):
    remove(reference)
for number in range(201, 207):
    remove(f"J{number}")
for number in range(211, 219):
    remove(f"J{number}")
for number in range(201, 211):
    remove(f"R{number}")
# Older generator revisions accidentally passed integers to SetReference.
# Remove every resulting numeric duplicate before rebuilding the connector row.
for number in range(201, 219):
    remove(str(number))

# Relocate the CAP1188 module away from the field-connector edge. Its C1...C8
# header faces the short protected traces and the motor stages remain above it.
cap = board.FindFootprintByReference("CAP1")
if cap is None:
    raise RuntimeError("Missing CAP1 footprint")
cap.SetPosition(pcbnew.VECTOR2I_MM(220, 80))
cap.SetOrientationDegrees(0)

# The right mounting hole must clear the new lower field connectors.
hole = board.FindFootprintByReference("H4")
if hole is not None:
    hole.SetPosition(pcbnew.VECTOR2I_MM(243, 152))
hole = board.FindFootprintByReference("H2")
if hole is not None:
    hole.SetPosition(pcbnew.VECTOR2I_MM(208, 90))

# Eight independent twisted-pair entries. Pin 1 is SENSOR, pin 2 is GND.
top = 14.0
cap_centres = []
for channel in range(1, 9):
    origin_y = top + 5.775
    add_terminal(f"J{211 + channel - 1}", f"CAP_CS{channel}_GND", 2, origin_y)
    cap_centres.append(top + 4.025)
    top += 8.55  # 8.05 mm body plus 0.5 mm assembly gap.

# Six three-wire reed entries: three per leaf. Pin order is 3V3, SIGNAL, GND.
reed_names = (
    "REED_A_OPEN",
    "REED_A_CLOSED",
    "REED_A_IN_PLACE",
    "REED_B_OPEN",
    "REED_B_CLOSED",
    "REED_B_IN_PLACE",
)
for index, name in enumerate(reed_names, start=1):
    origin_y = top + 9.275
    add_terminal(f"J{200 + index}", f"{name}_3V3_SIG_GND", 3, origin_y)
    top += 12.05  # 11.55 mm body plus 0.5 mm assembly gap.

if top > 159.5:
    raise RuntimeError(f"Sensor connector column exceeds board edge: {top:.2f} mm")

# Tuning footprints for cable EMC. Initial assembly value is 1 kOhm; a 0 Ohm
# option is allowed after measurements with the final cable and electrode.
for channel, y_mm in enumerate(cap_centres, start=1):
    resistor = add_resistor(f"R{200 + channel}", "1K_CAP_INPUT", 247.0, y_mm)
    resistor.Reference().SetVisible(False)

add_resistor("R209", "10K_CAP_RESET_PULLDOWN", 215, 82)
add_resistor("R210", "10K_CAP_IRQ_PULLUP", 215, 88)

# Five-pin service header: 3V3, SWDIO, SWCLK, NRST, GND. It is intentionally
# inside the service area because no permanent field cable connects to SWD.
swd = load(
    "Connector_PinHeader_2.54mm.pretty",
    "PinHeader_1x05_P2.54mm_Vertical",
)
swd.SetReference("J220")
swd.SetValue("SWD_S1_3V3_DIO_CLK_NRST_GND")
swd.Value().SetVisible(False)
swd.SetPosition(pcbnew.VECTOR2I_MM(244, 128))
swd.SetOrientationDegrees(0)
board.Add(swd)

pcbnew.SaveBoard(str(BOARD_PATH), board)
