"""Replace generic headers with complete module footprints verified by photos."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
LIBRARY = PROJECT / "DOOR-8CH.pretty"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before replacing module headers")


def load(name):
    item = pcbnew.FootprintLoad(str(LIBRARY), name)
    if item is None:
        raise RuntimeError(f"Unable to load {name}")
    return item


modules = {
    "CAN1": load("SN65HVD230_Module_14.5x16.1mm_1x06"),
    "CAN2": load("SN65HVD230_Module_14.5x16.1mm_1x06"),
    "RF1": load("CC1101_433MHz_Module_28x15mm_2x04"),
    "CAP1": load("CAP1188_Adafruit1602_Module_2x13"),
    "ESP1": load("ESP32-S3-DevKitC"),
}

board = pcbnew.LoadBoard(str(BOARD_PATH))

for reference in ("J101", "J102", "J103", *modules.keys()):
    old = board.FindFootprintByReference(reference)
    if old is not None:
        board.Delete(old)


def add(reference, value, x_mm, y_mm, rotation=0):
    item = modules[reference]
    item.SetReference(reference)
    item.SetValue(value)
    item.Value().SetVisible(False)
    item.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    item.SetOrientationDegrees(rotation)
    board.Add(item)


add("CAN1", "SN65HVD230_MASTER_CAN", 63, 142)
add("CAN2", "SN65HVD230_ESP_CAN_OPTION", 123, 142)

# Rotate the CC1101 so the spring-antenna end faces the left board edge while
# the 2x4 socket remains accessible from the board interior.
add("RF1", "CC1101_433MHZ", 31, 130, 180)

# CAP1188 touch-channel pins sit beside the right board edge. Its four module
# holes and both 13-pin rows follow the official Adafruit 1602 coordinates.
add("CAP1", "CAP1188_SPI", 239, 70)

# The supplied ESP32 photo matches the official 44-pin S3-DevKitC layout.
# Rotation 90 degrees places both USB connectors at the left board edge and
# keeps the full module body inside the board.
add("ESP1", "ESP32_S3_DEVKITC_DOUBLE_DOOR_ONLY", 8, 105, 90)

# Remaining field/programming headers stay on the right board edge.
for reference, y_mm in (("J104", 120), ("J105", 140)):
    item = board.FindFootprintByReference(reference)
    item.SetPosition(pcbnew.VECTOR2I_MM(253, y_mm))
    item.SetOrientationDegrees(270)

pcbnew.SaveBoard(str(BOARD_PATH), board)
