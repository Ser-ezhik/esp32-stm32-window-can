"""Reroute the three DIAG trunks that failed fine-grid DRC."""

from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))
grid.GRID = 0.50
grid.CLEARANCE = 0.35
grid.PAD_EXTRA = 0.50


def position(reference, number):
    pad = board.FindFootprintByReference(reference).FindPadByNumber(str(number))
    p = pad.GetPosition()
    return round(pcbnew.ToMM(p.x), 4), round(pcbnew.ToMM(p.y), 4)


nets = {"CH1_DIAG", "CH3_DIAG", "CH4_DIAG"}
for item in list(board.GetTracks()):
    if item.GetNetname() in nets:
        board.Delete(item)

for channel, module, module_pad in ((1, "MOD1", 27), (3, "MOD2", 27), (4, "MOD2", 3)):
    net = f"CH{channel}_DIAG"
    resistor = f"R{1000 + channel * 100 + 7}"
    router.route_multilayer(
        board, net, position(module, module_pad), position(resistor, 1),
        0.20, None, pcbnew.F_Cu, False,
    )
    pcbnew.SaveBoard(str(BOARD_PATH), board)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Rerouted DIAG trunks 1, 3 and 4")
