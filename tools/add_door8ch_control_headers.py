"""Add verified 2.54 mm control-module sockets to the DOOR-8CH board."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
FOOTPRINTS = Path(r"C:\Users\Ezhik\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints")
board = pcbnew.LoadBoard(str(BOARD_PATH))


def add(library, name, reference, value, x_mm, y_mm):
    if board.FindFootprintByReference(reference):
        return
    footprint = pcbnew.FootprintLoad(str(FOOTPRINTS / library), name)
    if footprint is None:
        raise RuntimeError(f"Unable to load {library}/{name}")
    footprint.SetReference(reference)
    footprint.SetValue(value)
    footprint.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    board.Add(footprint)


# The pictured SN65HVD230 boards expose one vertical six-pin, 2.54 mm header.
add(
    "Connector_PinSocket_2.54mm.pretty",
    "PinSocket_1x06_P2.54mm_Vertical",
    "J101",
    "SN65HVD230_MASTER_CAN",
    18,
    112,
)
add(
    "Connector_PinSocket_2.54mm.pretty",
    "PinSocket_1x06_P2.54mm_Vertical",
    "J102",
    "SN65HVD230_ESP_CAN_OPTION",
    38,
    112,
)

# The photographed 433 MHz CC1101 uses a 2x4, 2.54 mm connector.
add(
    "Connector_PinSocket_2.54mm.pretty",
    "PinSocket_2x04_P2.54mm_Vertical",
    "J103",
    "CC1101_433MHZ",
    58,
    112,
)

# Cabinet field I/O and programming headers. Electrical net assignment comes
# from the schematic; their positions keep them on the quiet, low-voltage edge.
add(
    "Connector_PinSocket_2.54mm.pretty",
    "PinSocket_1x05_P2.54mm_Vertical",
    "J104",
    "REEDS_3V3_GND",
    78,
    112,
)
add(
    "Connector_PinSocket_2.54mm.pretty",
    "PinSocket_1x06_P2.54mm_Vertical",
    "J105",
    "SWD_S1",
    92,
    112,
)

pcbnew.SaveBoard(str(BOARD_PATH), board)
