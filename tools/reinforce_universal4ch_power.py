"""Reinforce routed 4-channel motor nets with copper zones and GND planes."""

from __future__ import annotations

from collections import defaultdict
import math
import re
import sys
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT / "hardware" / "UNIVERSAL-4CH-F103RC-IC" / "routing"
    / "UNIVERSAL-4CH-F103RC-IC-routed-pass1.kicad_pcb"
)
DEFAULT_OUTPUT = (
    ROOT / "hardware" / "UNIVERSAL-4CH-F103RC-IC" / "routing"
    / "UNIVERSAL-4CH-F103RC-IC-reinforced.kicad_pcb"
)
POWER_PATTERN = re.compile(r"(?:FUSED_12V_CH[1-4]|CH[1-4]_OUT[AB])$")


def point(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def coordinates(position: pcbnew.VECTOR2I) -> tuple[float, float]:
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def add_ground_plane(board: pcbnew.BOARD, layer: int) -> None:
    zone = pcbnew.ZONE(board)
    zone.SetZoneName("GROUND_PLANE")
    zone.SetNet(board.FindNet("GND"))
    zone.SetLayer(layer)
    zone.SetLocalClearance(pcbnew.FromMM(0.30))
    zone.SetMinThickness(pcbnew.FromMM(0.25))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    outline = zone.Outline()
    outline.NewOutline()
    for xy in ((0.5, 0.5), (123.55, 0.5), (123.55, 92.55), (0.5, 92.55)):
        outline.Append(point(*xy))
    board.Add(zone)


def main() -> None:
    input_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_INPUT
    output_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_OUTPUT
    total_width = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    board = pcbnew.LoadBoard(str(input_path))
    for zone in list(board.Zones()):
        board.Delete(zone)

    add_ground_plane(board, pcbnew.F_Cu)
    add_ground_plane(board, pcbnew.B_Cu)

    groups: dict[tuple[str, int], list[tuple[tuple[float, float], ...]]] = defaultdict(list)
    reinforced_segments = 0
    for track in board.GetTracks():
        if isinstance(track, pcbnew.PCB_VIA) or not POWER_PATTERN.fullmatch(track.GetNetname()):
            continue
        x1, y1 = coordinates(track.GetStart())
        x2, y2 = coordinates(track.GetEnd())
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < 1.0:
            continue
        ux, uy = dx / length, dy / length
        nx, ny = -uy, ux
        half_width = total_width / 2.0
        extension = 0.30
        sx, sy = x1 - ux * extension, y1 - uy * extension
        ex, ey = x2 + ux * extension, y2 + uy * extension
        groups[(track.GetNetname(), track.GetLayer())].append((
            (sx + nx * half_width, sy + ny * half_width),
            (ex + nx * half_width, ey + ny * half_width),
            (ex - nx * half_width, ey - ny * half_width),
            (sx - nx * half_width, sy - ny * half_width),
        ))
        reinforced_segments += 1

    for net_name, layer in sorted(groups):
        polygons = groups[(net_name, layer)]
        zone = pcbnew.ZONE(board)
        zone.SetZoneName("POWER_REINFORCEMENT")
        zone.SetNet(board.FindNet(net_name))
        zone.SetLayer(layer)
        zone.SetLocalClearance(pcbnew.FromMM(0.30))
        zone.SetMinThickness(pcbnew.FromMM(0.25))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        outline = zone.Outline()
        for polygon in polygons:
            outline.NewOutline()
            for xy in polygon:
                outline.Append(point(*xy))
        board.Add(zone)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(output_path), board)
    print(f"Reinforced {reinforced_segments} power segments in {len(groups)} zone groups at {total_width:.1f} mm")
    print(output_path)


if __name__ == "__main__":
    main()
