"""Reroute signals that overlapped restored validated DIAG copper."""

import math
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

NETS = {
    "S2_3V3", "CAP_MOSI", "CH3_INA_MCU", "CH4_INA_MCU",
    "REED_A_OPEN", "REED_A_CLOSED", "CH2_PWM_MCU",
}


def xy(pad):
    p = pad.GetPosition()
    return round(pcbnew.ToMM(p.x), 4), round(pcbnew.ToMM(p.y), 4)


def layer(pad):
    return None if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else pcbnew.F_Cu


for item in list(board.GetTracks()):
    if item.GetNetname() in NETS:
        board.Delete(item)

for net in NETS:
    pads = [pad for footprint in board.GetFootprints() for pad in footprint.Pads()
            if pad.GetNetname() == net]
    connected = {0}
    remaining = set(range(1, len(pads)))
    while remaining:
        _, source, target = min(
            (math.dist(xy(pads[a]), xy(pads[b])), a, b)
            for a in connected for b in remaining
        )
        first, second = pads[source], pads[target]
        router.route_multilayer(
            board, net, xy(first), xy(second),
            0.30 if net == "S2_3V3" else 0.20,
            layer(first), pcbnew.F_Cu,
            second.GetAttribute() == pcbnew.PAD_ATTRIB_PTH,
        )
        connected.add(target)
        remaining.remove(target)
    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print("Rerouted", net)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Completed post-DIAG reroute")
