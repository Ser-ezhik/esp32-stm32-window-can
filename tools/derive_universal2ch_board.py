"""Create the compact UNIVERSAL-2CH PCB from the validated WINDOW-4CH board."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "hardware" / "WINDOW-4CH" / "kicad"
TARGET_DIR = ROOT / "hardware" / "UNIVERSAL-2CH" / "kicad"
SOURCE_BOARD = SOURCE_DIR / "WINDOW-4CH.kicad_pcb"
TARGET_BOARD = TARGET_DIR / "UNIVERSAL-2CH.kicad_pcb"
LOCK_PATH = TARGET_DIR / "~UNIVERSAL-2CH.kicad_pcb.lck"

WIDTH = 106.0
HEIGHT = 112.0


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I_MM(x, y)


if LOCK_PATH.exists():
    raise SystemExit("Close UNIVERSAL-2CH in KiCad before rebuilding the board")

TARGET_DIR.mkdir(parents=True, exist_ok=True)
for extension in (".kicad_pro", ".kicad_prl"):
    source = SOURCE_DIR / f"WINDOW-4CH{extension}"
    target = TARGET_DIR / f"UNIVERSAL-2CH{extension}"
    if source.exists() and not target.exists():
        shutil.copy2(source, target)

board = pcbnew.LoadBoard(str(SOURCE_BOARD))

remove_reference = re.compile(
    r"^(?:"
    r"J[34]|U[34]|MOD2|"
    r"HS[34][AB]|"
    r"[RCD]13\d+|[RCD]14\d+|"
    r"R3012|R302[12]|R25[01]|"
    r"J214|R204"
    r")$"
)

for footprint in list(board.GetFootprints()):
    if remove_reference.match(footprint.GetReference()):
        board.Delete(footprint)

# Pins not used by the universal two-channel hardware are explicit no-connects.
# Clearing their inherited one-pad nets also makes the generated schematic
# express that intent instead of showing dead UART/CAP1188 labels.
unused_pads = {
    "MOD1": {"4", "9", "14", "19", "28", "37"},
    "CAP1": {"21", "22", "23", "24", "25"},
}
for reference, numbers in unused_pads.items():
    footprint = board.FindFootprintByReference(reference)
    for pad in footprint.Pads():
        if pad.GetNumber() in numbers:
            pad.SetNetCode(0)

# Preserve only the already validated local copper around VNH channels 1 and 2.
retained_nets = {
    "CH1_OUTA", "CH1_OUTB", "CH2_OUTA", "CH2_OUTB",
    "FUSED_12V_CH1", "FUSED_12V_CH2",
}
for channel in (1, 2):
    retained_nets.update({
        f"CH{channel}_INA", f"CH{channel}_INB", f"CH{channel}_PWM",
        f"CH{channel}_CS_DIS", f"CH{channel}_CS_RAW",
    })

for item in list(board.GetTracks()):
    if item.GetNetname() not in retained_nets:
        board.Delete(item)

for zone in list(board.Zones()):
    board.Delete(zone)

# Free text and old dimensions belong to WINDOW-4CH and are regenerated below.
for drawing in list(board.GetDrawings()):
    board.Delete(drawing)

placements = {
    # Right-edge position sensors.
    "J201": (99.5, 9.0, 90),
    "J202": (99.5, 22.0, 90),
    "J203": (99.5, 35.0, 90),

    # Right-edge capacitive field connections, adjacent to CAP1188.
    "J211": (99.5, 72.0, 90),
    "J212": (99.5, 84.0, 90),
    "J213": (5.5, 45.0, 90),
    "R201": (89.0, 72.0, 270),
    "R202": (89.0, 82.0, 270),
    "R203": (89.0, 86.0, 270),
    "CAP1": (55.0, 109.0, 90),
    "R209": (42.0, 88.0, 0),
    "R210": (53.0, 75.0, 0),

    # Protected 12 V input and conversion in the free upper-right quadrant.
    "J230": (82.0, 5.0, 0),
    "F230": (70.0, 12.0, 0),
    "D230": (72.0, 25.0, 0),
    "D231": (80.0, 25.0, 0),
    "C231": (86.0, 25.0, 0),
    "C232": (86.0, 31.0, 0),
    "C230": (76.0, 35.0, 0),
    "DC1": (66.0, 45.0, 0),
    "C234": (72.0, 65.0, 0),
    "C235": (77.0, 65.0, 0),
    "C233": (92.0, 45.0, 0),
    "C237": (82.0, 65.0, 0),
    "C236": (68.0, 68.0, 0),
    "U230": (78.0, 72.0, 0),
    "C239": (86.0, 66.0, 0),
    "C238": (84.0, 78.0, 0),

    # Power-fail monitor and carrier EEPROM.
    "R270": (70.0, 80.0, 0),
    "C271": (74.0, 80.0, 0),
    "R271": (78.0, 80.0, 0),
    "R272": (70.0, 84.0, 0),
    "U270": (76.0, 84.0, 0),
    "C270": (82.0, 84.0, 0),
    "U250": (42.0, 80.0, 0),
    "C250": (49.0, 77.0, 0),
    "R260": (35.0, 76.0, 90),
    "R261": (35.0, 81.0, 90),
    "R262": (36.5, 86.0, 90),
    "R3011": (8.0, 84.0, 0),

    # Dense lower service row; field wiring remains accessible at the edges.
    "MOD1": (7.5, 109.0, 90),
    "C280": (62.0, 84.0, 90),
    "D280": (42.0, 84.0, 0),
    "CAN1": (36.5, 94.5, 0),
    "R240": (15.0, 76.0, 0),
    "D240": (20.0, 78.0, 90),
    "L240": (24.0, 76.0, 0),
    "D241": (29.0, 78.0, 90),
    "J240": (5.5, 76.0, 90),
    "J220": (18.0, 84.0, 90),

    # Board mounting holes; VNH heatsink holes remain unchanged.
    "H1": (5.0, 5.0, 0),
    "H2": (102.0, 58.0, 0),
    "H3": (50.0, 86.0, 0),
    "H4": (102.0, 106.0, 0),
}

for reference, (x, y, angle) in placements.items():
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        raise RuntimeError(f"Missing retained footprint {reference}")
    footprint.SetPosition(pt(x, y))
    footprint.SetOrientationDegrees(angle)

outline = pcbnew.PCB_SHAPE(board)
outline.SetShape(pcbnew.SHAPE_T_RECT)
outline.SetLayer(pcbnew.Edge_Cuts)
outline.SetStart(pt(0.0, 0.0))
outline.SetEnd(pt(WIDTH, HEIGHT))
outline.SetWidth(pcbnew.FromMM(0.05))
board.Add(outline)

gnd = board.FindNet("GND")
for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
    zone = pcbnew.ZONE(board)
    zone.SetNet(gnd)
    zone.SetLayer(layer)
    zone.SetLocalClearance(pcbnew.FromMM(0.30))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    polygon = zone.Outline()
    polygon.NewOutline()
    for x, y in ((0.5, 0.5), (WIDTH - 0.5, 0.5),
                 (WIDTH - 0.5, HEIGHT - 0.5), (0.5, HEIGHT - 0.5)):
        polygon.Append(pt(x, y))
    board.Add(zone)

for text_value, position, size in (
    ("UNIVERSAL-2CH", (48.0, 75.0), 1.3),
    ("2x VNH5019 / STM32 / CAN / CAP1188", (48.0, 72.8), 0.75),
):
    text = pcbnew.PCB_TEXT(board)
    text.SetText(text_value)
    text.SetPosition(pt(*position))
    text.SetLayer(pcbnew.F_SilkS)
    text.SetTextHeight(pcbnew.FromMM(size))
    text.SetTextWidth(pcbnew.FromMM(size))
    text.SetTextThickness(pcbnew.FromMM(0.15))
    board.Add(text)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(TARGET_BOARD), board)
print(
    f"Created {TARGET_BOARD.relative_to(ROOT)}: "
    f"{len(board.GetFootprints())} footprints, {WIDTH:.0f} x {HEIGHT:.0f} mm"
)
