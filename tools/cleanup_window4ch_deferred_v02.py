"""Remove incomplete residual branches while preserving successful SPI routes."""

from pathlib import Path

import pcbnew

import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))

remove_nets = {
    "EEPROM_CS", "EEPROM_WP", "EEPROM_HOLD", "CAP_MISO",
    "PGOOD_SENSE", "POWER_GOOD",
}
for item in list(board.GetTracks()):
    if item.GetNetname() in remove_nets:
        board.Delete(item)


def position(reference, number):
    pad = board.FindFootprintByReference(reference).FindPadByNumber(str(number))
    p = pad.GetPosition()
    return round(pcbnew.ToMM(p.x), 4), round(pcbnew.ToMM(p.y), 4)


# Keep the comparator's local open-drain tie; only its long MCU branch remains.
router.add_track(board, "POWER_GOOD", pcbnew.F_Cu, position("U270", 1), position("U270", 6), 0.20)
router.add_track(board, "POWER_GOOD", pcbnew.F_Cu, position("U270", 1), position("R272", 2), 0.20)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Removed deferred residual branches")
