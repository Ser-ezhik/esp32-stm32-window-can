"""Add paired satellite vias beside routed motor-power layer transitions."""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import pcbnew


POWER_PATTERN = re.compile(r"(?:FUSED_12V_CH[1-4]|CH[1-4]_OUT[AB])$")


def mm(position: pcbnew.VECTOR2I) -> tuple[float, float]:
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def point(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: add_universal4ch_parallel_power_vias.py INPUT OUTPUT")
    source = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    board = pcbnew.LoadBoard(str(source))
    tracks = list(board.GetTracks())
    added = 0

    for via in tracks:
        if not isinstance(via, pcbnew.PCB_VIA) or not POWER_PATTERN.fullmatch(via.GetNetname()):
            continue
        vx, vy = mm(via.GetPosition())
        direction = None
        for track in tracks:
            if isinstance(track, pcbnew.PCB_VIA) or track.GetNetCode() != via.GetNetCode():
                continue
            sx, sy = mm(track.GetStart())
            ex, ey = mm(track.GetEnd())
            if math.hypot(sx - vx, sy - vy) < 0.02:
                direction = (ex - sx, ey - sy)
                break
            if math.hypot(ex - vx, ey - vy) < 0.02:
                direction = (sx - ex, sy - ey)
                break
        if direction is None:
            continue
        length = math.hypot(*direction)
        nx, ny = -direction[1] / length, direction[0] / length
        for sign in (-1.0, 1.0):
            satellite = pcbnew.PCB_VIA(board)
            satellite.SetNet(via.GetNet())
            satellite.SetPosition(point(vx + sign * nx * 0.65, vy + sign * ny * 0.65))
            satellite.SetWidth(pcbnew.FromMM(0.60))
            satellite.SetDrill(pcbnew.FromMM(0.30))
            satellite.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            board.Add(satellite)
            added += 1

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(output), board)
    print(f"Added {added} satellite power vias")
    print(output)


if __name__ == "__main__":
    main()
