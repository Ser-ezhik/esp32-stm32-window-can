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

WIDTH = 120.0
HEIGHT = 135.0


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
    "J201": (115.0, 14.0, 90),
    "J202": (115.0, 26.0, 90),
    "J203": (115.0, 38.0, 90),

    # Right-edge capacitive field connections, adjacent to CAP1188.
    "J211": (115.0, 84.0, 90),
    "J212": (115.0, 96.0, 90),
    "J213": (115.0, 108.0, 90),
    "R201": (86.0, 102.0, 270),
    "R202": (86.0, 108.0, 270),
    "R203": (86.0, 114.0, 270),
    "CAP1": (90.0, 92.0, 0),
    "R209": (87.0, 91.0, 90),
    "R210": (87.0, 96.0, 90),

    # Protected 12 V input and conversion along the left edge.
    "J230": (5.0, 82.0, 0),
    "F230": (14.0, 82.0, 0),
    "D230": (39.0, 83.0, 0),
    "D231": (47.0, 83.0, 0),
    "C231": (55.0, 83.0, 0),
    "C232": (60.0, 83.0, 0),
    "C230": (48.0, 96.0, 0),
    "DC1": (68.0, 98.0, 90),
    "C234": (89.0, 77.0, 0),
    "C235": (94.0, 77.0, 0),
    "C233": (110.0, 72.0, 0),
    "C237": (96.0, 75.0, 0),
    "C236": (91.0, 89.0, 0),
    "U230": (95.0, 83.0, 0),
    "C239": (101.0, 75.0, 0),
    "C238": (105.0, 89.0, 0),

    # Power-fail monitor and carrier EEPROM.
    "R270": (62.0, 100.0, 270),
    "C271": (65.0, 102.0, 270),
    "R271": (62.0, 106.0, 270),
    "R272": (76.0, 104.0, 90),
    "U270": (70.0, 108.0, 0),
    "C270": (77.0, 110.0, 270),
    "U250": (83.0, 55.0, 0),
    "C250": (90.0, 55.0, 0),
    "R260": (76.0, 51.0, 90),
    "R261": (76.0, 56.0, 90),
    "R262": (76.0, 61.0, 90),
    "R3011": (12.0, 101.0, 0),

    # Bottom service row; USB and all field connectors remain accessible.
    "MOD1": (23.0, 129.9, 180),
    "C280": (41.0, 116.0, 90),
    "D280": (43.0, 130.0, 270),
    "CAN1": (58.0, 118.0, 0),
    "R240": (74.0, 116.0, 0),
    "D240": (74.0, 123.0, 90),
    "L240": (79.0, 118.0, 0),
    "D241": (86.0, 123.0, 90),
    "J240": (76.0, 130.0, 0),
    "J220": (104.0, 58.0, 90),

    # Board mounting holes; VNH heatsink holes remain unchanged.
    "H1": (5.0, 5.0, 0),
    "H2": (104.0, 5.0, 0),
    "H3": (30.0, 119.0, 0),
    "H4": (115.0, 122.0, 0),
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
    ("UNIVERSAL-2CH", (58.0, 75.5), 1.5),
    ("2x VNH5019 / STM32 / CAN / CAP1188", (58.0, 73.0), 0.9),
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
