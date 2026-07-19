"""Finish only the residual WINDOW-4CH v0.2 connections reported by DRC."""

from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))

grid.GRID = 0.25
grid.CLEARANCE = 0.30


def xy(position):
    return round(pcbnew.ToMM(position.x), 4), round(pcbnew.ToMM(position.y), 4)


def pad(reference, number):
    result = board.FindFootprintByReference(reference).FindPadByNumber(str(number))
    if result is None:
        raise RuntimeError(f"Missing {reference}.{number}")
    return result


def connect(net_name, first_ref, first_pad, second_ref, second_pad, width=0.20):
    first = pad(first_ref, first_pad)
    second = pad(second_ref, second_pad)
    start_layer = None if first.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else pcbnew.F_Cu
    end_pth = second.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
    router.route_multilayer(
        board, net_name, xy(first.GetPosition()), xy(second.GetPosition()), width,
        start_layer, pcbnew.F_Cu, end_pth,
    )


def add_path(net_name, layer, points, width=0.20):
    for first, second in zip(points, points[1:]):
        router.add_track(board, net_name, layer, first, second, width)


# VNH5019 DIAG has two package pins. Escape to the left of each package, join
# both pins, then meet the already-routed pull-up/MCU branch at Rxx07.
for channel, x, resistor_x in (
    (1, 14.875, 17.175),
    (2, 44.875, 47.175),
    (3, 74.875, 77.175),
    (4, 104.875, 107.175),
):
    net = f"CH{channel}_DIAG"
    escape_x = x - 2.5
    upper_via = (escape_x, 38.0)
    lower_via = (escape_x, 66.0)
    add_path(net, pcbnew.F_Cu, ((x, 32.0), (escape_x, 32.0), (escape_x, 36.0), (x, 36.0)))
    add_path(net, pcbnew.F_Cu, ((escape_x, 36.0), upper_via))
    router.add_via(board, net, upper_via)
    router.add_via(board, net, lower_via)
    add_path(net, pcbnew.In1_Cu, (upper_via, lower_via))
    add_path(net, pcbnew.F_Cu, (lower_via, (resistor_x, 66.0), (resistor_x, 68.0)))

# Residual MCU and SPI/EEPROM links. A 0.25 mm search grid is used only here
# so dense U250 and module-header escapes do not inherit the coarse 0.5 mm snap.
links = (
    ("CH1_PWM_MCU", "MOD1", 22, "R1103", 1),
    ("CAP_MOSI", "MOD1", 7, "U250", 5),
    ("CAP_MOSI", "U250", 5, "CAP1", 14),
    ("CAP_SCK", "MOD1", 8, "U250", 6),
    ("CAP_SCK", "U250", 6, "CAP1", 2),
    ("CAP_MISO", "MOD1", 17, "U250", 2),
    ("CAP_MISO", "U250", 2, "CAP1", 1),
    ("EEPROM_CS", "MOD1", 35, "U250", 1),
    ("EEPROM_CS", "U250", 1, "R260", 1),
    ("EEPROM_WP", "U250", 3, "R261", 1),
    ("EEPROM_HOLD", "U250", 7, "R262", 1),
    ("S1_3V3", "U250", 8, "C250", 1),
    ("POWER_GOOD", "U270", 1, "U270", 6),
    ("POWER_GOOD", "U270", 1, "R272", 2),
    ("PGOOD_SENSE", "U270", 3, "R271", 2),
    ("LOGIC_12V_FUSED", "U270", 5, "C270", 1),
    ("LOGIC_12V_FUSED", "U270", 5, "R270", 1),
)

deferred = []
for link in links:
    try:
        connect(*link, 0.30 if link[0] == "S1_3V3" else (0.80 if link[0] == "LOGIC_12V_FUSED" else 0.20))
        print("Connected", link)
    except RuntimeError as error:
        deferred.append((link, str(error)))
        print("DEFERRED", link, error)
    pcbnew.SaveBoard(str(BOARD_PATH), board)

# Stitch all isolated GND islands across all four copper layers.
layers = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
blocked = [grid.build_blocked(board, "GND", layer, 0.80) for layer in layers]
stitches = 0
for y in range(78, 146, 8):
    for x in range(8, 151, 8):
        key = grid.grid_key((x, y))
        if all(key not in layer_blocked for layer_blocked in blocked):
            router.add_via(board, "GND", (x, y), 0.80, 0.40)
            stitches += 1

# Move the two crowded assembly references without moving their components.
board.FindFootprintByReference("C280").Reference().SetPosition(pcbnew.VECTOR2I_MM(111.0, 128.0))
board.FindFootprintByReference("D280").Reference().SetPosition(pcbnew.VECTOR2I_MM(118.0, 146.0))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Added {stitches} GND stitches; deferred {len(deferred)} residual links")
for link, error in deferred:
    print(" ", link, error)
