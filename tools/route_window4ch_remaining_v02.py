"""Try the remaining WINDOW-4CH links on a fine grid, preserving all successes."""

from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))
grid.GRID = 0.25
grid.CLEARANCE = 0.32
grid.PAD_EXTRA = 0.0


def pad(reference, number):
    return board.FindFootprintByReference(reference).FindPadByNumber(str(number))


def xy(item):
    p = item.GetPosition()
    return round(pcbnew.ToMM(p.x), 4), round(pcbnew.ToMM(p.y), 4)


def connect(net, first_ref, first_pad, second_ref, second_pad, width=0.20):
    first = pad(first_ref, first_pad)
    second = pad(second_ref, second_pad)
    first_layer = None if first.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else pcbnew.F_Cu
    second_pth = second.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
    router.route_multilayer(
        board, net, xy(first), xy(second), width, first_layer,
        pcbnew.F_Cu, second_pth,
    )


links = [
    ("CAP_MISO", "MOD1", 17, "U250", 2),
    ("CAP_MISO", "U250", 2, "CAP1", 1),
    ("S1_3V3", "U250", 8, "C250", 1, 0.30),
    ("POWER_GOOD", "U270", 1, "MOD1", 30),
    ("EEPROM_CS", "MOD1", 35, "U250", 1),
    ("EEPROM_CS", "U250", 1, "R260", 1),
    ("EEPROM_WP", "U250", 3, "R261", 1),
    ("EEPROM_HOLD", "U250", 7, "R262", 1),
    ("PGOOD_SENSE", "U270", 3, "R271", 1),
    ("PGOOD_SENSE", "R271", 1, "R270", 2),
    ("PGOOD_SENSE", "R270", 2, "C271", 1),
]
for channel, module, module_pad in ((1, "MOD1", 27), (2, "MOD1", 3),
                                    (3, "MOD2", 27), (4, "MOD2", 3)):
    links.append((f"CH{channel}_DIAG", module, module_pad, f"R{1000 + channel * 100 + 7}", 1))
    links.append((f"CH{channel}_DIAG", f"R{1000 + channel * 100 + 7}", 1, f"U{channel}", 9))
    links.append((f"CH{channel}_DIAG", f"U{channel}", 9, f"U{channel}", 5))

failures = []
for link in links:
    width = link[5] if len(link) > 5 else 0.20
    try:
        connect(*link[:5], width)
        print("Connected", link)
    except RuntimeError as error:
        failures.append((link, str(error)))
        print("DEFERRED", link, error)
    pcbnew.SaveBoard(str(BOARD_PATH), board)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Remaining pass deferred {len(failures)} links")
for link, error in failures:
    print(" ", link, error)
