"""Route the CAP1188 connections after moving the edge terminals."""

from __future__ import annotations

import os
from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid_router


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
BOARD_PATH = Path(os.environ.get("BOARD_PATH", DEFAULT_BOARD))


def mm(position):
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def pad_position(board, reference, number):
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        raise RuntimeError(f"Missing {reference}")
    pad = footprint.FindPadByNumber(str(number))
    if pad is None:
        raise RuntimeError(f"Missing {reference}.{number}")
    return mm(pad.GetPosition())


board = pcbnew.LoadBoard(str(BOARD_PATH))

# CAP1188 raw inputs are intentionally short and parallel.  The resistors are
# aligned to the CAP1 pads, so these links do not enter the power-driver area.
for channel in range(1, 9):
    net_name = f"CAP_C{channel}_RAW"
    cap_pad = pad_position(board, "CAP1", 17 + channel)
    resistor_pad = pad_position(board, f"R20{channel}", 1)
    grid_router.add_track(board, net_name, pcbnew.F_Cu, cap_pad, resistor_pad, 0.20)

# Route the field side along the right edge, around J220 and every preceding
# sensor channel.  A finer grid is useful around the small 0603 pads.
grid_router.GRID = 0.25
grid_router.CLEARANCE = 0.20
for channel in range(1, 9):
    net_name = f"CAP_C{channel}_FIELD"
    start = pad_position(board, f"R20{channel}", 2)
    end = pad_position(board, f"J21{channel}", 1)
    grid_router.route(board, net_name, pcbnew.F_Cu, start, end, 0.20)

for zone in board.Zones():
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
