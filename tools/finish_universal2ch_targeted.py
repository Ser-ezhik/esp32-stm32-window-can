"""Finish the final routed gaps and clean known local DRC items."""

from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "UNIVERSAL-2CH" / "kicad" / "UNIVERSAL-2CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))

grid.GRID = 0.25
grid.CLEARANCE = 0.30
grid.PAD_EXTRA = grid.GRID


def xy(item):
    p = item if isinstance(item, pcbnew.VECTOR2I) else item.GetPosition()
    return round(pcbnew.ToMM(p.x), 4), round(pcbnew.ToMM(p.y), 4)


def pad(reference, number):
    return board.FindFootprintByReference(reference).FindPadByNumber(str(number))


def connect(net_name, first_ref, first_pad, second_ref, second_pad, width=0.20):
    first = pad(first_ref, first_pad)
    second = pad(second_ref, second_pad)
    first_layer = None if first.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else pcbnew.F_Cu
    second_layer = pcbnew.F_Cu if second.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    router.route_multilayer(
        board, net_name, xy(first), xy(second), width, first_layer,
        second_layer, second.GetAttribute() == pcbnew.PAD_ATTRIB_PTH,
    )


def path(net_name, layer, points, width=0.20):
    for first, second in zip(points, points[1:]):
        router.add_track(board, net_name, layer, first, second, width)


links = (
    ("CH2_PWM_MCU", "MOD1", 32, "R1203", 1),
    ("CH2_INB_MCU", "MOD1", 36, "R1202", 1),
    ("S1_CAN_RX", "MOD1", 33, "CAN1", 4),
)

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

# Complete the PGOOD divider/filter locally.
path("PGOOD_SENSE", pcbnew.F_Cu, (
    xy(pad("R270", 2)), xy(pad("C271", 1)),
    (67.0, 101.225), (67.0, 104.0), xy(pad("R271", 1)),
))

# Remove the harmless source-board DIAG tail.
for item in list(board.GetTracks()):
    if isinstance(item, pcbnew.PCB_VIA):
        continue
    if item.GetNetname() == "CH1_DIAG":
        ends = {xy(item.GetStart()), xy(item.GetEnd())}
        if (17.0, 69.0) in ends:
            board.Delete(item)
            continue

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Targeted finish complete; deferred {len(failures)} links")
