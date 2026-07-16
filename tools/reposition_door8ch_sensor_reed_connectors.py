"""Move reed terminals above the CAP1188 terminals and clear obsolete routes."""

from __future__ import annotations

import os
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
BOARD_PATH = Path(os.environ.get("BOARD_PATH", DEFAULT_BOARD))


def mm(position):
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def move(board, reference, x_mm, y_mm):
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        raise RuntimeError(f"Missing {reference}")
    footprint.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))


board = pcbnew.LoadBoard(str(BOARD_PATH))

# Six 3-pin reed terminals occupy the upper right edge.  Their pitch keeps
# adjacent terminal bodies separated while leaving the CAP1188 area clear.
reed_y = (14.0, 26.05, 38.10, 50.15, 62.20, 74.25)
for index, y_mm in enumerate(reed_y, start=1):
    move(board, f"J20{index}", 254.70, y_mm)

# All eight 2-pin capacitive-sensor terminals sit beside CAP1.  Keep each input
# resistor with its terminal so only a short field-side trace reaches the PCB.
cap_y = tuple(85.50 + 8.55 * index for index in range(8))
for index, y_mm in enumerate(cap_y, start=1):
    move(board, f"J21{index}", 254.70, y_mm)
    cap_raw_y = 95.875 + 2.54 * (index - 1)
    resistor = board.FindFootprintByReference(f"R20{index}")
    resistor.SetOrientationDegrees(0.0)
    resistor.SetPosition(pcbnew.VECTOR2I_MM(242.00, cap_raw_y))

cap_nets = {
    f"CAP_C{channel}_{suffix}"
    for channel in range(1, 9)
    for suffix in ("FIELD", "RAW")
}
reed_signal_nets = {
    f"REED_{side}_{state}"
    for side in ("A", "B")
    for state in ("OPEN", "CLOSED", "IN_PLACE")
}

for item in list(board.GetTracks()):
    net_name = item.GetNetname()
    if net_name in cap_nets or net_name in reed_signal_nets:
        board.Delete(item)
        continue

    if isinstance(item, pcbnew.PCB_VIA):
        if net_name == "S1_3V3":
            x_mm, _ = mm(item.GetPosition())
            if x_mm > 240.0:
                board.Delete(item)
        elif net_name == "S4_3V3":
            x_mm, _ = mm(item.GetPosition())
            if x_mm > 231.0:
                board.Delete(item)
        continue

    start_x, start_y = mm(item.GetStart())
    end_x, end_y = mm(item.GetEnd())

    # Remove only the old connector fanout.  The existing S1/S2 distribution
    # trunks and their anchor points are retained for the new branches.
    if net_name == "S1_3V3" and item.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
        if max(start_x, end_x) > 215.0:
            board.Delete(item)
    elif net_name == "S1_3V3" and item.GetLayer() == pcbnew.In2_Cu:
        if min(start_x, end_x) >= 241.0:
            board.Delete(item)
    elif net_name == "S2_3V3" and item.GetLayer() == pcbnew.B_Cu:
        if min(start_x, end_x) > 250.0:
            board.Delete(item)
    elif net_name == "S2_3V3" and item.GetLayer() == pcbnew.In1_Cu:
        if min(start_x, end_x) >= 251.50:
            board.Delete(item)
    elif net_name == "S4_3V3" and max(start_x, end_x) > 231.0:
        board.Delete(item)

for zone in board.Zones():
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
