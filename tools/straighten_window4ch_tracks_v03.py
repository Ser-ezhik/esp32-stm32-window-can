"""Replace autorouter stair steps with equivalent straight PCB segments."""

from __future__ import annotations

import math
import os
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
BOARD_PATH = Path(os.environ.get("BOARD_PATH", DEFAULT_BOARD))
EPSILON = pcbnew.FromMM(float(os.environ.get("STRAIGHTEN_EPSILON_MM", "0.19")))
MAX_WIDTH = pcbnew.FromMM(0.80)
EXCLUDED_NETS = {
    "CAP_MISO",
    "CH1_CS_RAW",
    "CH1_INA",
    "CH2_PWM",
    "CH3_CS_RAW",
    "CH3_INB",
    "CH4_DIAG",
    "CH4_PWM",
    "S1_UART1_RX",
}
EXCLUDED_NETS.update(
    item.strip()
    for item in os.environ.get("STRAIGHTEN_EXCLUDED_NETS", "").split(",")
    if item.strip()
)


def key(position: pcbnew.VECTOR2I) -> tuple[int, int]:
    return position.x, position.y


def distance_to_line(point, start, end) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    return abs(dy * px - dx * py + bx * ay - by * ax) / math.hypot(dx, dy)


def simplify(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if len(points) <= 2:
        return points
    start, end = points[0], points[-1]
    distances = [distance_to_line(point, start, end) for point in points[1:-1]]
    maximum = max(distances, default=0.0)
    if maximum <= EPSILON:
        return [start, end]
    split = distances.index(maximum) + 1
    return simplify(points[:split + 1])[:-1] + simplify(points[split:])


board = pcbnew.LoadBoard(str(BOARD_PATH))
groups = defaultdict(list)
via_nodes = defaultdict(set)
pad_nodes = defaultdict(set)
for footprint in board.GetFootprints():
    for pad in footprint.Pads():
        if pad.GetNetCode():
            pad_nodes[pad.GetNetCode()].add(key(pad.GetPosition()))
for track in board.GetTracks():
    if isinstance(track, pcbnew.PCB_VIA):
        via_nodes[track.GetNetCode()].add(key(track.GetPosition()))
        continue
    if (track.GetWidth() > MAX_WIDTH or track.GetNetname() in EXCLUDED_NETS):
        continue
    groups[(track.GetNetCode(), track.GetLayer(), track.GetWidth())].append(track)

removed = []
replacements = []
chains_changed = 0

for (net_code, layer, width), tracks in groups.items():
    edges = []
    adjacency = defaultdict(list)
    for track in tracks:
        first, second = key(track.GetStart()), key(track.GetEnd())
        edge_id = len(edges)
        edges.append((first, second, track))
        adjacency[first].append(edge_id)
        adjacency[second].append(edge_id)

    visited = set()
    starts = [
        node for node, incident in adjacency.items()
        if (
            len(incident) != 2
            or node in via_nodes[net_code]
            or node in pad_nodes[net_code]
        )
    ]
    for start in starts:
        for first_edge in adjacency[start]:
            if first_edge in visited:
                continue
            chain_edges = []
            points = [start]
            node = start
            edge_id = first_edge
            while edge_id not in visited:
                visited.add(edge_id)
                chain_edges.append(edge_id)
                a, b, _ = edges[edge_id]
                node = b if node == a else a
                points.append(node)
                if (
                    len(adjacency[node]) != 2
                    or node in via_nodes[net_code]
                    or node in pad_nodes[net_code]
                ):
                    break
                candidates = [item for item in adjacency[node] if item not in visited]
                if not candidates:
                    break
                edge_id = candidates[0]

            reduced = simplify(points)
            if len(reduced) >= len(points):
                continue
            chains_changed += 1
            removed.extend(edges[item][2] for item in chain_edges)
            net = board.FindNet(net_code)
            for first, second in zip(reduced, reduced[1:]):
                replacements.append((net, layer, width, first, second))

for track in removed:
    board.Delete(track)
for net, layer, width, first, second in replacements:
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(net)
    track.SetLayer(layer)
    track.SetWidth(width)
    track.SetStart(pcbnew.VECTOR2I(*first))
    track.SetEnd(pcbnew.VECTOR2I(*second))
    board.Add(track)

# The direct CAP_MOSI chord would graze the S1_SWCLK via.  Keep this as two
# clean straight sections with a deliberate left-side clearance waypoint.
cap_start = (pcbnew.VECTOR2I_MM(34.0, 114.0).x, pcbnew.VECTOR2I_MM(34.0, 114.0).y)
cap_end = (pcbnew.VECTOR2I_MM(33.75, 120.0).x, pcbnew.VECTOR2I_MM(33.75, 120.0).y)
for track in list(board.GetTracks()):
    if (isinstance(track, pcbnew.PCB_VIA) or track.GetNetname() != "CAP_MOSI" or
            track.GetLayer() != pcbnew.B_Cu):
        continue
    if {key(track.GetStart()), key(track.GetEnd())} != {cap_start, cap_end}:
        continue
    net = board.FindNet(track.GetNetCode())
    width = track.GetWidth()
    board.Delete(track)
    points = [cap_start, key(pcbnew.VECTOR2I_MM(33.5, 116.5)), cap_end]
    for first, second in zip(points, points[1:]):
        piece = pcbnew.PCB_TRACK(board)
        piece.SetNet(net)
        piece.SetLayer(pcbnew.B_Cu)
        piece.SetWidth(width)
        piece.SetStart(pcbnew.VECTOR2I(*first))
        piece.SetEnd(pcbnew.VECTOR2I(*second))
        board.Add(piece)
    break

# Keep CH4_CS_RAW clear of the grounded R1406 pad.  The previous diagonal
# passed the pad by only 0.180 mm; a short vertical leg provides full margin.
cs_start = key(pcbnew.VECTOR2I_MM(126.0, 64.3756))
cs_end = key(pcbnew.VECTOR2I_MM(126.313, 62.8615))
for track in list(board.GetTracks()):
    if (isinstance(track, pcbnew.PCB_VIA) or
            track.GetNetname() != "CH4_CS_RAW" or
            track.GetLayer() != pcbnew.F_Cu or
            {key(track.GetStart()), key(track.GetEnd())} != {cs_start, cs_end}):
        continue
    net = board.FindNet(track.GetNetCode())
    width = track.GetWidth()
    board.Delete(track)
    points = [cs_start, key(pcbnew.VECTOR2I_MM(126.0, 62.8615)), cs_end]
    for first, second in zip(points, points[1:]):
        piece = pcbnew.PCB_TRACK(board)
        piece.SetNet(net)
        piece.SetLayer(pcbnew.F_Cu)
        piece.SetWidth(width)
        piece.SetStart(pcbnew.VECTOR2I(*first))
        piece.SetEnd(pcbnew.VECTOR2I(*second))
        board.Add(piece)
    break

# Replace the long S1 UART RX staircase while keeping a deliberate corridor
# above the CAP_MISO via at (72.0, 108.25).
uart_rx_tracks = [
    track for track in board.GetTracks()
    if (not isinstance(track, pcbnew.PCB_VIA) and
        track.GetNetname() == "S1_UART1_RX" and
        track.GetLayer() == pcbnew.In2_Cu)
]
if uart_rx_tracks:
    net = board.FindNet(uart_rx_tracks[0].GetNetCode())
    width = uart_rx_tracks[0].GetWidth()
    for track in uart_rx_tracks:
        board.Delete(track)
    points = [
        key(pcbnew.VECTOR2I_MM(52.5, 121.0)),
        key(pcbnew.VECTOR2I_MM(61.0, 121.0)),
        key(pcbnew.VECTOR2I_MM(71.5, 110.5)),
        key(pcbnew.VECTOR2I_MM(71.5, 109.5)),
        key(pcbnew.VECTOR2I_MM(73.5, 109.5)),
        key(pcbnew.VECTOR2I_MM(78.0, 104.5)),
    ]
    for first, second in zip(points, points[1:]):
        piece = pcbnew.PCB_TRACK(board)
        piece.SetNet(net)
        piece.SetLayer(pcbnew.In2_Cu)
        piece.SetWidth(width)
        piece.SetStart(pcbnew.VECTOR2I(*first))
        piece.SetEnd(pcbnew.VECTOR2I(*second))
        board.Add(piece)

# KiCad expects a segment boundary at T junctions.  Simplification can make a
# short branch meet the middle of a new straight segment, so split that segment
# at every same-net endpoint lying exactly on it.
split_count = 0
track_groups = defaultdict(list)
for track in board.GetTracks():
    if (not isinstance(track, pcbnew.PCB_VIA) and
            track.GetNetname() not in EXCLUDED_NETS):
        track_groups[(track.GetNetCode(), track.GetLayer())].append(track)

for tracks in track_groups.values():
    endpoints = {
        key(position)
        for track in tracks
        for position in (track.GetStart(), track.GetEnd())
    }
    for track in list(tracks):
        first, second = key(track.GetStart()), key(track.GetEnd())
        ax, ay = first
        bx, by = second
        dx, dy = bx - ax, by - ay
        interior = []
        for point in endpoints:
            if point == first or point == second:
                continue
            px, py = point
            if not (min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)):
                continue
            if dx * (py - ay) != dy * (px - ax):
                continue
            parameter = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
            if 0.0 < parameter < 1.0:
                interior.append((parameter, point))
        if not interior:
            continue
        net = board.FindNet(track.GetNetCode())
        layer = track.GetLayer()
        width = track.GetWidth()
        board.Delete(track)
        ordered = [first] + [point for _, point in sorted(interior)] + [second]
        for start, end in zip(ordered, ordered[1:]):
            piece = pcbnew.PCB_TRACK(board)
            piece.SetNet(net)
            piece.SetLayer(layer)
            piece.SetWidth(width)
            piece.SetStart(pcbnew.VECTOR2I(*start))
            piece.SetEnd(pcbnew.VECTOR2I(*end))
            board.Add(piece)
        split_count += len(interior)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(
    f"Straightened {chains_changed} chains: "
    f"{len(removed)} tracks -> {len(replacements)} straight segments; "
    f"split {split_count} T junctions"
)
