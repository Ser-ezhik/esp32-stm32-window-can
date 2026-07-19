"""Route residual compact-board nets on assigned copper layers."""

from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))
grid.GRID = 0.25
grid.CLEARANCE = 0.30
failures = []


def pos(reference, number):
    pad = board.FindFootprintByReference(reference).FindPadByNumber(str(number))
    p = pad.GetPosition()
    return round(pcbnew.ToMM(p.x), 4), round(pcbnew.ToMM(p.y), 4)


def front(net, *points, width=0.20):
    for start, end in zip(points, points[1:]):
        router.add_track(board, net, pcbnew.F_Cu, start, end, width)


def escape(net, pad_position, via_position, width=0.20):
    front(net, pad_position, via_position, width=width)
    router.add_via(board, net, via_position)


def layer_route(net, layer, start, end, width=0.20):
    try:
        grid.route(board, net, layer, start, end, width)
    except RuntimeError as error:
        failures.append(str(error))
        print("DEFERRED", error)


rebuild = {
    "LOGIC_12V_FUSED", "PGOOD_SENSE", "POWER_GOOD",
    "EEPROM_CS", "EEPROM_WP", "EEPROM_HOLD",
    "CAP_MOSI", "CAP_SCK", "CAP_MISO",
}
for item in list(board.GetTracks()):
    if item.GetNetname() in rebuild:
        board.Delete(item)

# 12 V monitor: broad feed on In2, narrow local fan-out at U270.
logic_root = (32.8, 87.0)
logic_via = (108.0, 93.175)
escape("LOGIC_12V_FUSED", pos("R270", 1), logic_via, 0.30)
layer_route("LOGIC_12V_FUSED", pcbnew.In2_Cu, logic_root, logic_via, 0.50)
router.route_multilayer(
    board, "LOGIC_12V_FUSED", logic_root, pos("D230", 1), 0.50,
    None, pcbnew.F_Cu, False,
)
front("LOGIC_12V_FUSED", pos("R270", 1), (104.0, 93.175), pos("C270", 1), width=0.25)
front("LOGIC_12V_FUSED", pos("C270", 1), pos("U270", 5), width=0.20)

# Power-good comparator signals use two separate internal layers.
front("PGOOD_SENSE", pos("R270", 2), pos("R271", 1), pos("C271", 1))
pgood_sense_u = (97.5, 99.95)
pgood_sense_rc = (111.0, 95.225)
escape("PGOOD_SENSE", pos("U270", 3), pgood_sense_u)
escape("PGOOD_SENSE", pos("C271", 1), pgood_sense_rc)
layer_route("PGOOD_SENSE", pcbnew.In1_Cu, pgood_sense_u, pgood_sense_rc)

front("POWER_GOOD", pos("U270", 1), pos("U270", 6))
front("POWER_GOOD", pos("U270", 1), pos("R272", 2))
power_good_via = (97.5, 98.05)
escape("POWER_GOOD", pos("U270", 1), power_good_via)
layer_route("POWER_GOOD", pcbnew.In2_Cu, power_good_via, pos("MOD1", 30))

# EEPROM control fan-out.
cs_u = (76.0, 107.095)
cs_r = (87.0, 112.0)
escape("EEPROM_CS", pos("U250", 1), cs_u)
escape("EEPROM_CS", pos("R260", 1), cs_r)
layer_route("EEPROM_CS", pcbnew.In2_Cu, cs_u, pos("MOD1", 35))
layer_route("EEPROM_CS", pcbnew.In2_Cu, cs_u, cs_r)

wp_u = (75.0, 109.635)
wp_r = (91.0, 116.0)
escape("EEPROM_WP", pos("U250", 3), wp_u)
escape("EEPROM_WP", pos("R261", 1), wp_r)
layer_route("EEPROM_WP", pcbnew.B_Cu, wp_u, wp_r)

hold_u = (86.0, 108.365)
hold_r = (95.0, 118.0)
escape("EEPROM_HOLD", pos("U250", 7), hold_u)
escape("EEPROM_HOLD", pos("R262", 1), hold_r)
layer_route("EEPROM_HOLD", pcbnew.In1_Cu, hold_u, hold_r)

# CAP1188 SPI signals each receive one dedicated layer. The U250 escape via is
# the star point joining MASTER, EEPROM carrier and CAP1188 module.
spi = (
    ("CAP_MOSI", 5, (86.0, 110.905), pcbnew.B_Cu, ("MOD1", 7), ("CAP1", 14)),
    ("CAP_SCK", 6, (86.0, 109.635), pcbnew.In1_Cu, ("MOD1", 8), ("CAP1", 2)),
    ("CAP_MISO", 2, (76.0, 108.365), pcbnew.In2_Cu, ("MOD1", 17), ("CAP1", 1)),
)
for net, u_pad, star, layer, first_target, second_target in spi:
    escape(net, pos("U250", u_pad), star)
    layer_route(net, layer, star, pos(*first_target))
    layer_route(net, layer, star, pos(*second_target))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Routed residual U250/U270 nets on assigned layers")
for failure in failures:
    print(" ", failure)
