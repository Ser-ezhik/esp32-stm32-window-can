"""Reinforce routed 4-channel motor nets with copper zones and GND planes."""

from __future__ import annotations

import math
import heapq
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


def pad_position(board: pcbnew.BOARD, reference: str, number: str) -> pcbnew.VECTOR2I:
    footprint = board.FindFootprintByReference(reference)
    if not footprint:
        raise RuntimeError(f"Missing footprint {reference}")
    for pad in footprint.Pads():
        if pad.GetNumber() == number:
            return pad.GetPosition()
    raise RuntimeError(f"Missing pad {reference}.{number}")


def route_key(track: pcbnew.PCB_TRACK) -> tuple[int, int, int, int, int, str]:
    start = track.GetStart()
    end = track.GetEnd()
    return start.x, start.y, end.x, end.y, track.GetLayer(), track.GetNetname()


def main_power_segments(board: pcbnew.BOARD) -> list[pcbnew.PCB_TRACK]:
    """Return only connector-to-large-VNH-pad paths for the 12 power nets."""
    selected: dict[tuple[int, int, int, int, int, str], pcbnew.PCB_TRACK] = {}
    endpoints: list[tuple[str, pcbnew.VECTOR2I, pcbnew.VECTOR2I]] = []
    for channel in range(1, 5):
        endpoints.extend((
            (f"FUSED_12V_CH{channel}", pad_position(board, f"J{channel}", "1"),
             pad_position(board, f"U{channel}", "31")),
            (f"CH{channel}_OUTA", pad_position(board, f"J{channel}", "3"),
             pad_position(board, f"U{channel}", "33")),
            (f"CH{channel}_OUTB", pad_position(board, f"J{channel}", "4"),
             pad_position(board, f"U{channel}", "32")),
        ))

    for net_name, source_position, target_position in endpoints:
        adjacency: dict[tuple[int, int, int], list[tuple[tuple[int, int, int], float, object]]] = {}

        def add_edge(a: tuple[int, int, int], b: tuple[int, int, int], weight: float, item: object) -> None:
            adjacency.setdefault(a, []).append((b, weight, item))
            adjacency.setdefault(b, []).append((a, weight, item))

        for item in board.GetTracks():
            if item.GetNetname() != net_name:
                continue
            if isinstance(item, pcbnew.PCB_VIA):
                position = item.GetPosition()
                add_edge((position.x, position.y, pcbnew.F_Cu),
                         (position.x, position.y, pcbnew.B_Cu), 0.05, item)
            else:
                start = item.GetStart()
                end = item.GetEnd()
                length = math.hypot(pcbnew.ToMM(end.x - start.x), pcbnew.ToMM(end.y - start.y))
                add_edge((start.x, start.y, item.GetLayer()),
                         (end.x, end.y, item.GetLayer()), length, item)

        sources = [
            (source_position.x, source_position.y, layer)
            for layer in (pcbnew.F_Cu, pcbnew.B_Cu)
            if (source_position.x, source_position.y, layer) in adjacency
        ]
        target = (target_position.x, target_position.y, pcbnew.B_Cu)
        if not sources or target not in adjacency:
            raise RuntimeError(f"Power path endpoint missing for {net_name}")

        distances: dict[tuple[int, int, int], float] = {}
        previous: dict[tuple[int, int, int], tuple[tuple[int, int, int], object]] = {}
        queue: list[tuple[float, tuple[int, int, int]]] = []
        for source in sources:
            distances[source] = 0.0
            heapq.heappush(queue, (0.0, source))
        while queue:
            distance, node = heapq.heappop(queue)
            if distance != distances.get(node):
                continue
            if node == target:
                break
            for neighbor, weight, item in adjacency.get(node, ()):
                candidate = distance + weight
                if candidate < distances.get(neighbor, float("inf")):
                    distances[neighbor] = candidate
                    previous[neighbor] = (node, item)
                    heapq.heappush(queue, (candidate, neighbor))
        if target not in distances:
            raise RuntimeError(f"No routed connector-to-driver path for {net_name}")

        node = target
        via_count = 0
        segment_count = 0
        while node not in sources:
            node, item = previous[node]
            if isinstance(item, pcbnew.PCB_VIA):
                via_count += 1
            else:
                selected[route_key(item)] = item
                segment_count += 1
        print(f"  {net_name}: {distances[target]:.1f} mm, {segment_count} segments, {via_count} layer transitions")
    return list(selected.values())


def main() -> None:
    input_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_INPUT
    output_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_OUTPUT
    total_width = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
    board = pcbnew.LoadBoard(str(input_path))
    for zone in list(board.Zones()):
        board.Delete(zone)

    add_ground_plane(board, pcbnew.F_Cu)
    add_ground_plane(board, pcbnew.B_Cu)

    groups: dict[tuple[str, int], pcbnew.SHAPE_POLY_SET] = {}
    reinforced_segments = 0
    for track in main_power_segments(board):
        x1, y1 = coordinates(track.GetStart())
        x2, y2 = coordinates(track.GetEnd())
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < 0.05:
            continue
        ux, uy = dx / length, dy / length
        nx, ny = -uy, ux
        half_width = total_width / 2.0
        extension = 0.50
        sx, sy = x1 - ux * extension, y1 - uy * extension
        ex, ey = x2 + ux * extension, y2 + uy * extension
        polygon = (
            (sx + nx * half_width, sy + ny * half_width),
            (ex + nx * half_width, ey + ny * half_width),
            (ex - nx * half_width, ey - ny * half_width),
            (sx - nx * half_width, sy - ny * half_width),
        )

        rectangle = pcbnew.SHAPE_POLY_SET()
        rectangle.NewOutline()
        for xy in polygon:
            rectangle.Append(point(*xy))
        key = (track.GetNetname(), track.GetLayer())
        if key not in groups:
            groups[key] = rectangle
        else:
            groups[key].BooleanAdd(rectangle)
        reinforced_segments += 1

    for priority, ((net_name, layer), shape) in enumerate(sorted(groups.items()), start=10):
        shape.Simplify()
        shape.NormalizeAreaOutlines()
        zone = pcbnew.ZONE(board)
        zone.SetZoneName("POWER_REINFORCEMENT")
        zone.SetNet(board.FindNet(net_name))
        zone.SetLayer(layer)
        zone.SetAssignedPriority(priority)
        zone.SetLocalClearance(pcbnew.FromMM(0.30))
        zone.SetMinThickness(pcbnew.FromMM(0.25))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        zone.SetOutline(shape)
        board.Add(zone)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(output_path), board)
    print(f"Reinforced {reinforced_segments} power segments in {len(groups)} boolean-union zones at {total_width:.1f} mm")
    print(output_path)


if __name__ == "__main__":
    main()
