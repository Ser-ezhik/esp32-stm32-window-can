"""Route critical UNIVERSAL-2CH buses before the general routing pass."""

from __future__ import annotations

from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "UNIVERSAL-2CH" / "kicad" / "UNIVERSAL-2CH.kicad_pcb"
SOURCE_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"

grid.GRID = 0.25
grid.CLEARANCE = 0.32
grid.PAD_EXTRA = grid.GRID


def pos(board, reference, number):
    pad = board.FindFootprintByReference(reference).FindPadByNumber(str(number))
    point = pad.GetPosition()
    return round(pcbnew.ToMM(point.x), 4), round(pcbnew.ToMM(point.y), 4)


def path(board, net_name, layer, points, width=0.20):
    for first, second in zip(points, points[1:]):
        router.add_track(board, net_name, layer, first, second, width)


def copy_local_diag(board, source, net_name):
    for item in list(board.GetTracks()):
        if item.GetNetname() == net_name:
            board.Delete(item)
    for item in source.GetTracks():
        if item.GetNetname() != net_name:
            continue
        points = [item.GetPosition()] if isinstance(item, pcbnew.PCB_VIA) else [
            item.GetStart(), item.GetEnd()
        ]
        if max(pcbnew.ToMM(point.y) for point in points) > 73.0:
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            clone = pcbnew.PCB_VIA(board)
            clone.SetNet(board.FindNet(net_name))
            clone.SetPosition(item.GetPosition())
            clone.SetWidth(item.GetWidth(item.TopLayer()))
            clone.SetDrill(item.GetDrillValue())
            clone.SetLayerPair(item.TopLayer(), item.BottomLayer())
        else:
            clone = pcbnew.PCB_TRACK(board)
            clone.SetNet(board.FindNet(net_name))
            clone.SetLayer(item.GetLayer())
            clone.SetWidth(item.GetWidth())
            clone.SetStart(item.GetStart())
            clone.SetEnd(item.GetEnd())
        board.Add(clone)


board = pcbnew.LoadBoard(str(BOARD_PATH))
source = pcbnew.LoadBoard(str(SOURCE_PATH))

# Proven VNH DIAG fan-out plus a sparse-board route to the STM32.
for channel, module_pad, resistor in ((1, 27, "R1107"), (2, 3, "R1207")):
    net_name = f"CH{channel}_DIAG"
    copy_local_diag(board, source, net_name)
    router.route_multilayer(
        board, net_name, pos(board, "MOD1", module_pad), pos(board, resistor, 1),
        0.20, None, pcbnew.F_Cu, False,
    )
# Local EEPROM fan-out.
path(board, "EEPROM_CS", pcbnew.F_Cu, (
    pos(board, "R260", 1), (78.0, 51.825), pos(board, "U250", 1),
))
path(board, "EEPROM_WP", pcbnew.F_Cu, (
    pos(board, "R261", 1), (78.0, 56.825), pos(board, "U250", 3),
))
hold_source_via = (74.5, 62.0)
hold_target_via = (88.0, 54.0)
path(board, "EEPROM_HOLD", pcbnew.F_Cu, (
    pos(board, "R262", 1), hold_source_via,
))
path(board, "EEPROM_HOLD", pcbnew.F_Cu, (
    pos(board, "U250", 7), hold_target_via,
))
router.add_via(board, "EEPROM_HOLD", hold_source_via)
router.add_via(board, "EEPROM_HOLD", hold_target_via)
path(board, "EEPROM_HOLD", pcbnew.B_Cu, (
    hold_source_via, (70.0, 62.0), (70.0, 46.0),
    (92.0, 46.0), (92.0, 54.0), hold_target_via,
))
eeprom_cs_via = (74.5, 51.75)
router.add_via(board, "EEPROM_CS", eeprom_cs_via)
path(board, "EEPROM_CS", pcbnew.F_Cu, (eeprom_cs_via, pos(board, "R260", 1)))
grid.route(board, "EEPROM_CS", pcbnew.B_Cu, pos(board, "MOD1", 35), eeprom_cs_via, 0.20)

# SPI SOIC escapes and one dedicated layer per bus.
spi = (
    ("CAP_MOSI", 5, (87.5, 57.0), pcbnew.In1_Cu, 7, 14),
    ("CAP_SCK", 6, (87.5, 55.5), pcbnew.In2_Cu, 8, 2),
    ("CAP_MISO", 2, (79.0, 54.5), pcbnew.B_Cu, 17, 1),
)
for net_name, eeprom_pad, via_at, layer, module_pad, cap_pad in spi:
    path(board, net_name, pcbnew.F_Cu, (pos(board, "U250", eeprom_pad), via_at))
    router.add_via(board, net_name, via_at)
    grid.route(board, net_name, layer, via_at, pos(board, "MOD1", module_pad), 0.20)
    grid.route(board, net_name, layer, via_at, pos(board, "CAP1", cap_pad), 0.20)

grid.route(board, "CAP_CS", pcbnew.In1_Cu, pos(board, "MOD1", 18), pos(board, "CAP1", 15), 0.20)

# This input shares the narrow socket corridor with CAP_MISO, so route it only
# after the complete SPI bus has escaped that area.
router.route_multilayer(
    board, "CH1_INB_MCU", pos(board, "MOD1", 12), pos(board, "R1102", 1),
    0.20, None, pcbnew.F_Cu, False,
)

# Route the EEPROM 3.3 V branch through two escapes so it cannot cross HOLD.
s1_source_via = (74.5, 54.5)
s1_target_via = (98.0, 42.0)
path(board, "S1_3V3", pcbnew.F_Cu, (pos(board, "R261", 2), s1_source_via), 0.35)
router.add_via(board, "S1_3V3", s1_source_via)
router.add_via(board, "S1_3V3", s1_target_via)
path(board, "S1_3V3", pcbnew.In2_Cu, (
    s1_source_via, (66.0, 54.5), (66.0, 40.0),
    (98.0, 40.0), s1_target_via,
), 0.35)
path(board, "S1_3V3", pcbnew.F_Cu, (
    s1_target_via, (84.0, 42.0), (84.0, 50.0), pos(board, "U250", 8),
), 0.35)
path(board, "S1_3V3", pcbnew.F_Cu, (
    (84.0, 50.0), (89.225, 50.0), pos(board, "C250", 1),
), 0.35)

# Monitor fan-out and long POWER_GOOD line.
path(board, "POWER_GOOD", pcbnew.F_Cu, (
    pos(board, "U270", 1), pos(board, "U270", 6), pos(board, "R272", 2),
))
power_good_via = (67.5, 107.0)
path(board, "POWER_GOOD", pcbnew.F_Cu, (pos(board, "U270", 1), power_good_via))
router.add_via(board, "POWER_GOOD", power_good_via)
grid.route(board, "POWER_GOOD", pcbnew.In2_Cu, power_good_via, pos(board, "MOD1", 30), 0.20)
path(board, "PGOOD_SENSE", pcbnew.F_Cu, (
    pos(board, "R271", 1), (64.0, 105.175), (66.0, 110.0),
    (68.8625, 110.0), pos(board, "U270", 3),
))
path(board, "LOGIC_12V_FUSED", pcbnew.F_Cu, (
    pos(board, "U270", 5), pos(board, "C270", 1),
), 0.30)
logic_source_via = (60.0, 98.0)
logic_target_via = (73.0, 108.0)
path(board, "LOGIC_12V_FUSED", pcbnew.F_Cu, (
    pos(board, "R270", 1), logic_source_via,
), 0.30)
path(board, "LOGIC_12V_FUSED", pcbnew.F_Cu, (
    pos(board, "U270", 5), logic_target_via,
), 0.30)
router.add_via(board, "LOGIC_12V_FUSED", logic_source_via)
router.add_via(board, "LOGIC_12V_FUSED", logic_target_via)
grid.route(
    board, "LOGIC_12V_FUSED", pcbnew.In1_Cu,
    logic_source_via, logic_target_via, 0.30,
)

grid.route(board, "CAP_IRQ", pcbnew.F_Cu, pos(board, "MOD1", 13), pos(board, "R210", 1), 0.20)
cap_reset_via = (84.0, 91.5)
path(board, "CAP_RESET", pcbnew.F_Cu, (pos(board, "R209", 1), cap_reset_via))
router.add_via(board, "CAP_RESET", cap_reset_via)
grid.route(board, "CAP_RESET", pcbnew.B_Cu, pos(board, "MOD1", 29), cap_reset_via, 0.20)
grid.route(board, "CAP_RESET", pcbnew.F_Cu, pos(board, "R209", 1), pos(board, "CAP1", 16), 0.20)

# These two long service lines are routed while the board is still sparse.
grid.PAD_EXTRA = grid.GRID * 2
grid.route(board, "S1_SWDIO", pcbnew.B_Cu, pos(board, "MOD1", 34), pos(board, "J220", 2), 0.20)
grid.route(board, "S1_NRST", pcbnew.F_Cu, pos(board, "MOD1", 16), pos(board, "J220", 4), 0.20)
grid.route(
    board, "REED_A_IN_PLACE", pcbnew.In2_Cu,
    pos(board, "MOD1", 38), pos(board, "J203", 2), 0.20,
)

pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Pre-routed critical UNIVERSAL-2CH buses")
