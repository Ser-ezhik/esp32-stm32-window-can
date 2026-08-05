"""Create the compact UNIVERSAL-4CH-F103RC-IC placement board.

This script intentionally creates placement only. Copper tracks and zones are
removed so the arrangement can be reviewed before routing starts.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SOURCE_2CH = ROOT / "hardware" / "UNIVERSAL-2CH-F103-IC" / "kicad"
SOURCE_4CH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
PROJECT = ROOT / "hardware" / "UNIVERSAL-4CH-F103RC-IC"
KICAD_DIR = PROJECT / "kicad"
BOARD_PATH = KICAD_DIR / "UNIVERSAL-4CH-F103RC-IC.kicad_pcb"
PROJECT_PATH = KICAD_DIR / "UNIVERSAL-4CH-F103RC-IC.kicad_pro"

KICAD_ROOT = Path(pcbnew.__file__).resolve().parents[3]
QFP_LIBRARY = KICAD_ROOT / "share" / "kicad" / "footprints" / "Package_QFP.pretty"

BOARD_WIDTH_MM = 136.0
BOARD_HEIGHT_MM = 105.0


def point(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def ensure_net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM | None:
    if not name:
        return None
    existing = board.FindNet(name)
    if existing:
        return existing
    net = pcbnew.NETINFO_ITEM(board, name)
    board.Add(net)
    return net


def clone_footprint(
    board: pcbnew.BOARD,
    source: pcbnew.BOARD,
    source_ref: str,
    target_ref: str | None = None,
) -> pcbnew.FOOTPRINT:
    original = source.FindFootprintByReference(source_ref)
    if original is None:
        raise RuntimeError(f"Missing source footprint {source_ref}")
    pad_nets = {pad.GetNumber(): pad.GetNetname() for pad in original.Pads()}
    clone = pcbnew.Cast_to_FOOTPRINT(original.Duplicate(False))
    if clone is None:
        raise RuntimeError(f"Could not duplicate {source_ref}")
    clone.SetReference(target_ref or source_ref)
    board.Add(clone)
    for pad in clone.Pads():
        net_name = pad_nets.get(pad.GetNumber(), "")
        if net_name:
            pad.SetNet(ensure_net(board, net_name))
        else:
            pad.SetNetCode(0)
    return clone


def move(
    board: pcbnew.BOARD,
    reference: str,
    x_mm: float,
    y_mm: float,
    rotation_deg: float = 0.0,
    bottom: bool | None = None,
) -> pcbnew.FOOTPRINT:
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        raise RuntimeError(f"Missing footprint {reference}")
    footprint.SetPosition(point(x_mm, y_mm))
    footprint.SetOrientationDegrees(rotation_deg)
    if bottom is not None and footprint.IsFlipped() != bottom:
        footprint.Flip(footprint.GetPosition(), False)
        footprint.SetOrientationDegrees(rotation_deg)
    return footprint


def set_pad_nets(footprint: pcbnew.FOOTPRINT, board: pcbnew.BOARD, mapping: dict[int, str]) -> None:
    for pad in footprint.Pads():
        number = int(pad.GetNumber()) if pad.GetNumber().isdigit() else -1
        net_name = mapping.get(number, "")
        if net_name:
            pad.SetNet(ensure_net(board, net_name))
        else:
            pad.SetNetCode(0)


KICAD_DIR.mkdir(parents=True, exist_ok=True)
base_board_path = SOURCE_2CH / "UNIVERSAL-2CH-F103-IC.kicad_pcb"
base_project_path = SOURCE_2CH / "UNIVERSAL-2CH-F103-IC.kicad_pro"
board = pcbnew.LoadBoard(str(base_board_path))
source_4ch = pcbnew.LoadBoard(str(SOURCE_4CH))

# Placement release: no inherited copper, zones or board-level artwork.
for item in list(board.GetTracks()):
    board.Delete(item)
for zone in list(board.Zones()):
    board.Delete(zone)
for drawing in list(board.GetDrawings()):
    board.Delete(drawing)

# Add the two extra power channels and the third reed connector.
extra_channel_refs = [
    "J3", "U3", "C1301", "C1302", "C1303", "D1301",
    "HS3A", "HS3B", *[f"R13{i:02d}" for i in range(1, 11)],
    "J4", "U4", "C1401", "C1402", "C1403", "D1401",
    "HS4A", "HS4B", *[f"R14{i:02d}" for i in range(1, 11)],
    "J203",
]
for reference in extra_channel_refs:
    clone_footprint(board, source_4ch, reference)

# Replace the LQFP48 controller with STM32F103RCT6 in LQFP64.
old_mcu = board.FindFootprintByReference("U300")
board.Delete(old_mcu)
mcu = pcbnew.PCB_IO_KICAD_SEXPR().FootprintLoad(
    str(QFP_LIBRARY), "LQFP-64_10x10mm_P0.5mm", True
)
if mcu is None:
    raise RuntimeError(f"Could not load LQFP64 footprint from {QFP_LIBRARY}")
mcu.SetReference("U300")
mcu.SetValue("STM32F103RCT6")
board.Add(mcu)

# One additional VDD bypass capacitor and a dedicated BOOT1 pulldown.
c3009 = clone_footprint(board, board, "C3006", "C3009")
c3009.SetValue("100n VDD")
r3003 = clone_footprint(board, board, "R3002", "R3003")
r3003.SetValue("10k BOOT1")
set_pad_nets(r3003, board, {1: "MCU_BOOT1", 2: "GND"})

# F103RC LQFP64 pin assignment. PB8/PB9 use the CAN remap, leaving all four
# TIM1 PWM channels on PA8..PA11.
mcu_nets = {
    1: "S1_3V3", 2: "", 3: "", 4: "",
    5: "MCU_HSE_IN", 6: "MCU_HSE_OUT", 7: "S1_NRST",
    8: "REED_A_OPEN", 9: "REED_A_CLOSED", 10: "REED_A_IN_PLACE",
    11: "POWER_GOOD", 12: "GND", 13: "S1_3V3",
    14: "CH1_CURRENT_ADC", 15: "CH2_CURRENT_ADC",
    16: "CH3_CURRENT_ADC", 17: "CH4_CURRENT_ADC",
    18: "GND", 19: "S1_3V3",
    20: "CAP_CS", 21: "CAP_SCK", 22: "CAP_MISO", 23: "CAP_MOSI",
    24: "EEPROM_CS", 25: "CAP_IRQ",
    26: "CH1_INA_MCU", 27: "CH1_INB_MCU", 28: "MCU_BOOT1",
    29: "CH2_INA_MCU", 30: "CH2_INB_MCU",
    31: "GND", 32: "S1_3V3",
    33: "CH3_INA_MCU", 34: "CH3_INB_MCU",
    35: "CH4_INA_MCU", 36: "CH4_INB_MCU",
    37: "CH1_DIAG", 38: "CH2_DIAG", 39: "CH3_DIAG", 40: "CH4_DIAG",
    41: "CH1_PWM_MCU", 42: "CH2_PWM_MCU",
    43: "CH3_PWM_MCU", 44: "CH4_PWM_MCU",
    45: "", 46: "S1_SWDIO", 47: "GND", 48: "S1_3V3",
    49: "S1_SWCLK", 50: "", 51: "CAP_RESET", 52: "", 53: "", 54: "",
    55: "", 56: "", 57: "", 58: "", 59: "",
    60: "MCU_BOOT0", 61: "S1_CAN_RX", 62: "S1_CAN_TX",
    63: "GND", 64: "S1_3V3",
}
set_pad_nets(mcu, board, mcu_nets)

# Four identical power lanes. SMD parts are on the bottom; connectors,
# electrolytics and heatsink holes are on the top.
channel_x = {1: 18.0, 2: 49.0, 3: 80.0, 4: 111.0}
for channel, center_x in channel_x.items():
    prefix = 10 + channel
    move(board, f"J{channel}", center_x - 2.0, 7.0, 0, False)
    move(board, f"U{channel}", center_x, 30.0, 0, True)
    move(board, f"HS{channel}A", center_x - 12.0, 30.0, 0, False)
    move(board, f"HS{channel}B", center_x + 12.0, 30.0, 0, False)
    move(board, f"C{prefix}01", center_x - 2.5, 56.0, 0, False)
    move(board, f"C{prefix}02", center_x - 9.5, 40.5, 0, True)
    move(board, f"C{prefix}03", center_x + 9.5, 51.5, 0, True)
    move(board, f"D{prefix}01", center_x + 9.5, 47.5, 0, True)
    for index in range(1, 7):
        move(board, f"R{prefix}{index:02d}", center_x - 10.0 + (index - 1) * 3.8, 43.0, 0, True)
    for index in range(7, 11):
        move(board, f"R{prefix}{index:02d}", center_x - 6.0 + (index - 7) * 3.8, 47.5, 0, True)

# Board mounting holes.
for reference, xy in {
    "H1": (4.5, 4.5), "H2": (131.5, 18.0),
    "H3": (4.5, 100.5), "H4": (131.5, 100.5),
}.items():
    move(board, reference, *xy, 0, False)

# Top-side modules, large capacitors and service connectors.
top_placements = {
    "F230": (7.0, 65.0, 0.0),
    "DC1": (14.0, 72.0, 0.0),
    "CAN1": (40.0, 72.0, 0.0),
    "C230": (60.5, 88.0, 90.0),
    "C233": (75.0, 74.0, 0.0),
    "C280": (79.0, 91.0, 90.0),
    "J220": (91.0, 72.0, 90.0),
    "J230": (11.0, 99.5, 0.0),
    "J240": (38.0, 99.5, 0.0),
    "J201": (87.0, 99.5, 0.0),
    "J202": (100.0, 99.5, 0.0),
    "J203": (113.0, 99.5, 0.0),
    "J211": (132.0, 70.0, -90.0),
    "J212": (132.0, 80.0, -90.0),
    "J213": (132.0, 90.0, -90.0),
}
for reference, (x_mm, y_mm, rotation) in top_placements.items():
    move(board, reference, x_mm, y_mm, rotation, False)

# Dense bottom-side control section.
bottom_placements = {
    "U300": (67.0, 72.0, 0.0),
    "Y300": (54.0, 69.0, 0.0),
    "C3001": (50.0, 66.0, 0.0), "C3002": (50.0, 72.0, 0.0),
    "R3001": (56.0, 77.0, 0.0), "C3003": (56.0, 81.0, 0.0),
    "R3002": (58.0, 85.0, 0.0), "R3003": (62.0, 85.0, 0.0),
    "C3004": (61.0, 63.0, 0.0), "C3005": (65.0, 63.0, 0.0),
    "C3006": (69.0, 63.0, 0.0), "C3009": (73.0, 63.0, 0.0),
    "C3007": (57.0, 63.0, 0.0), "C3008": (53.0, 63.0, 0.0),
    "U250": (84.0, 72.0, 0.0), "C250": (84.0, 77.0, 0.0),
    "R260": (81.0, 81.0, 0.0), "R261": (85.0, 81.0, 0.0),
    "R262": (89.0, 81.0, 0.0),
    "CAP1": (112.0, 72.0, 0.0), "C340": (108.0, 67.0, 0.0),
    "C341": (112.0, 67.0, 0.0), "R209": (108.0, 78.0, 0.0),
    "R210": (112.0, 78.0, 0.0),
    "R201": (123.0, 70.0, 90.0), "R202": (123.0, 80.0, 90.0),
    "R203": (123.0, 90.0, 90.0),
    "D230": (9.0, 91.0, 0.0), "D231": (18.0, 94.0, 180.0),
    "C231": (10.0, 86.0, 0.0), "C232": (18.0, 82.0, 0.0),
    "U230": (27.0, 91.0, 180.0),
    "C234": (23.0, 85.0, 0.0), "C235": (27.0, 85.0, 0.0),
    "C236": (29.0, 81.5, 0.0), "C237": (37.0, 80.5, 0.0),
    "C238": (34.0, 91.0, 0.0), "C239": (38.0, 91.0, 0.0),
    "R2301": (34.0, 97.0, 0.0),
    "L240": (43.0, 94.0, 0.0), "D240": (48.0, 94.0, 90.0),
    "D241": (51.0, 94.0, 90.0), "R240": (46.0, 89.0, 0.0),
    "U270": (63.0, 93.0, 90.0), "R270": (59.0, 93.0, 0.0),
    "R271": (59.0, 97.0, 0.0), "R272": (66.0, 97.0, 0.0),
    "C270": (67.0, 91.0, 0.0), "C271": (70.0, 96.0, 0.0),
    "D280": (73.0, 81.0, 0.0), "J280B": (82.0, 84.0, 0.0),
}
for reference, (x_mm, y_mm, rotation) in bottom_placements.items():
    move(board, reference, x_mm, y_mm, rotation, True)

# New rectangular outline.
outline = pcbnew.PCB_SHAPE(board)
outline.SetShape(pcbnew.SHAPE_T_RECT)
outline.SetLayer(pcbnew.Edge_Cuts)
outline.SetStart(point(0.0, 0.0))
outline.SetEnd(point(BOARD_WIDTH_MM, BOARD_HEIGHT_MM))
outline.SetWidth(pcbnew.FromMM(0.05))
board.Add(outline)

title = pcbnew.PCB_TEXT(board)
title.SetText("UNIVERSAL 4CH  STM32F103RC")
title.SetPosition(point(95.0, 64.0))
title.SetLayer(pcbnew.F_SilkS)
title.SetTextSize(point(1.2, 1.2))
title.SetTextThickness(pcbnew.FromMM(0.20))
board.Add(title)

board.SetFileName(str(BOARD_PATH))
pcbnew.SaveBoard(str(BOARD_PATH), board)
shutil.copy2(base_project_path, PROJECT_PATH)

print(f"Created {BOARD_PATH}")
print(f"Board: {BOARD_WIDTH_MM:.1f} x {BOARD_HEIGHT_MM:.1f} mm")
print(f"Footprints: {len(board.GetFootprints())}; tracks: {len(board.GetTracks())}; zones: {len(board.Zones())}")
