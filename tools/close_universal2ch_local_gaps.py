"""Close the final compact-board local pad gaps with straight traces."""

from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "hardware" / "UNIVERSAL-2CH" / "kicad" / "UNIVERSAL-2CH.kicad_pcb"
board = pcbnew.LoadBoard(str(PCB))
grid.GRID = 0.25
grid.CLEARANCE = 0.30
grid.PAD_EXTRA = 0.50
grid.EDGE = 0.75


def pad(reference, number):
    return board.FindFootprintByReference(reference).FindPadByNumber(str(number))


def xy(item):
    point = item.GetPosition()
    return round(pcbnew.ToMM(point.x), 4), round(pcbnew.ToMM(point.y), 4)


def path(net_name, points, width=0.20):
    for first, second in zip(points, points[1:]):
        router.add_track(board, net_name, pcbnew.F_Cu, first, second, width)


def layer_path(net_name, layer, points, width=0.20):
    for first, second in zip(points, points[1:]):
        router.add_track(board, net_name, layer, first, second, width)


def via(net_name, point, diameter=0.70, drill=0.35):
    router.add_via(board, net_name, point, diameter, drill)


# EEPROM supply: pad 8 exits to the upper-right, away from HOLD and SCK.
path(
    "S1_3V3",
    (xy(pad("U250", 8)), (46.0, 78.095), xy(pad("C250", 1))),
    0.35,
)
router.route_multilayer(
    board,
    "S1_3V3",
    xy(pad("D1101", 2)),
    xy(pad("D1201", 2)),
    0.35,
    pcbnew.F_Cu,
    pcbnew.F_Cu,
    False,
)

# SOT23-6 power-good monitor fan-out. These short traces remain below the body
# and leave between adjacent pads without crossing their solder-mask openings.
path(
    "POWER_GOOD",
    (
        xy(pad("R272", 2)), (72.5, 84.0), (73.45, 83.05),
        xy(pad("U270", 1)), xy(pad("U270", 6)),
    ),
)

logic_a = (67.5, 80.0)
logic_b = (79.0, 84.0)
path("LOGIC_12V_FUSED", (xy(pad("R270", 1)), logic_a), 0.80)
via("LOGIC_12V_FUSED", logic_a, 1.00, 0.45)
via("LOGIC_12V_FUSED", logic_b, 1.00, 0.45)
layer_path("LOGIC_12V_FUSED", pcbnew.In1_Cu, (logic_a, logic_b), 0.80)
path(
    "LOGIC_12V_FUSED",
    (logic_b, xy(pad("U270", 5)), xy(pad("C270", 1))),
    0.80,
)

sense_a = (72.0, 80.0)
sense_b = (73.0, 85.5)
path("PGOOD_SENSE", (xy(pad("C271", 1)), sense_a))
via("PGOOD_SENSE", sense_a)
via("PGOOD_SENSE", sense_b)
layer_path("PGOOD_SENSE", pcbnew.In2_Cu, (sense_a, sense_b))
path("PGOOD_SENSE", (sense_b, (74.8625, 85.5), xy(pad("U270", 3))))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(PCB), board)
print("Closed compact local gaps")
