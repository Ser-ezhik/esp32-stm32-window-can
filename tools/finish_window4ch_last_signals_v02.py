"""Finish the last five signal gaps on compact WINDOW-4CH."""

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


def position(reference, number):
    pad = board.FindFootprintByReference(reference).FindPadByNumber(str(number))
    p = pad.GetPosition()
    return round(pcbnew.ToMM(p.x), 4), round(pcbnew.ToMM(p.y), 4)


# Remove two validated-v0.1 tails that led toward old module positions.
obsolete = (
    ("CH2_DIAG", pcbnew.VECTOR2I_MM(47.1750, 68.0), pcbnew.VECTOR2I_MM(45.8612, 68.0)),
    ("CH3_DIAG", pcbnew.VECTOR2I_MM(77.1750, 68.0), pcbnew.VECTOR2I_MM(71.2247, 68.0)),
)
for item in list(board.GetTracks()):
    if isinstance(item, pcbnew.PCB_VIA):
        continue
    for net, first, second in obsolete:
        if item.GetNetname() == net and {
            (item.GetStart().x, item.GetStart().y), (item.GetEnd().x, item.GetEnd().y)
        } == {(first.x, first.y), (second.x, second.y)}:
            board.Delete(item)
            break


def escape(net, pad_position, star):
    router.add_track(board, net, pcbnew.F_Cu, pad_position, star, 0.20)
    router.add_via(board, net, star)


failures = []


def route(net, start, end, start_layer=None, width=0.20, end_pth=True):
    try:
        router.route_multilayer(
            board, net, start, end, width, start_layer,
            pcbnew.F_Cu, end_pth,
        )
    except RuntimeError as error:
        failures.append(str(error))
        print("DEFERRED", error)


# Join the U250 3.3 V island directly to the MASTER module rail.
route("S1_3V3", position("U250", 8), position("MOD1", 11), pcbnew.F_Cu, 0.30)

# CAP_MISO leaves U250 to the left before the router sees the dense carrier pins.
miso_star = (74.0, 108.365)
escape("CAP_MISO", position("U250", 2), miso_star)
route("CAP_MISO", miso_star, position("MOD1", 17), pcbnew.B_Cu)
route("CAP_MISO", miso_star, position("CAP1", 1), pcbnew.B_Cu)

# EEPROM pull controls use separate star points and can change layers afterward.
wp_star = (74.0, 110.5)
escape("EEPROM_WP", position("U250", 3), wp_star)
route("EEPROM_WP", wp_star, position("R261", 1), pcbnew.In2_Cu, end_pth=False)

hold_star = (86.0, 106.0)
escape("EEPROM_HOLD", position("U250", 7), hold_star)
route("EEPROM_HOLD", hold_star, position("R262", 1), pcbnew.In1_Cu, end_pth=False)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Last-signal pass deferred {len(failures)} routes")
for failure in failures:
    print(" ", failure)
