"""Route the last long DOOR-8CH connections around existing copper."""

from __future__ import annotations

import heapq
import math
import os
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
BOARD_PATH = Path(os.environ.get("BOARD_PATH", DEFAULT_BOARD))
GRID = 0.5
EDGE = 0.75
CLEARANCE = 0.30


def mm(position):
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def point(position):
    return pcbnew.VECTOR2I_MM(*position)


def segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def grid_key(position):
    return round(position[0] / GRID), round(position[1] / GRID)


def grid_point(key):
    return key[0] * GRID, key[1] * GRID


def mark_circle(blocked, x, y, radius):
    ix0, iy0 = grid_key((x - radius, y - radius))
    ix1, iy1 = grid_key((x + radius, y + radius))
    for ix in range(ix0 - 1, ix1 + 2):
        for iy in range(iy0 - 1, iy1 + 2):
            px, py = grid_point((ix, iy))
            if math.hypot(px - x, py - y) <= radius:
                blocked.add((ix, iy))


def mark_segment(blocked, start, end, radius):
    ax, ay = start
    bx, by = end
    ix0, iy0 = grid_key((min(ax, bx) - radius, min(ay, by) - radius))
    ix1, iy1 = grid_key((max(ax, bx) + radius, max(ay, by) + radius))
    for ix in range(ix0 - 1, ix1 + 2):
        for iy in range(iy0 - 1, iy1 + 2):
            px, py = grid_point((ix, iy))
            if segment_distance(px, py, ax, ay, bx, by) <= radius:
                blocked.add((ix, iy))


def build_blocked(board, net_name, layer, width):
    blocked = set()
    margin = CLEARANCE + width / 2

    for item in board.GetTracks():
        if item.GetNetname() == net_name:
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            x, y = mm(item.GetPosition())
            mark_circle(blocked, x, y, pcbnew.ToMM(item.GetWidth(item.TopLayer())) / 2 + margin)
        elif item.GetLayer() == layer:
            mark_segment(
                blocked,
                mm(item.GetStart()),
                mm(item.GetEnd()),
                pcbnew.ToMM(item.GetWidth()) / 2 + margin,
            )

    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetname() == net_name or not pad.IsOnLayer(layer):
                continue
            center = mm(pad.GetPosition())
            size = pad.GetSize()
            radius = max(pcbnew.ToMM(size.x), pcbnew.ToMM(size.y)) / 2 + margin
            mark_circle(blocked, *center, radius)

    return blocked


def find_path(board, net_name, layer, start, end, width):
    blocked = build_blocked(board, net_name, layer, width)
    source, target = grid_key(start), grid_key(end)
    blocked.discard(source)
    blocked.discard(target)

    min_x = round(EDGE / GRID)
    min_y = round(EDGE / GRID)
    max_x = round((260.0 - EDGE) / GRID)
    max_y = round((160.0 - EDGE) / GRID)
    moves = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    queue = [(0.0, 0.0, source, None)]
    cost = {(source, None): 0.0}
    parent = {}
    final_state = None

    while queue:
        _, current_cost, current, direction = heapq.heappop(queue)
        state = (current, direction)
        if current_cost != cost.get(state):
            continue
        if current == target:
            final_state = state
            break
        for move in moves:
            neighbor = current[0] + move[0], current[1] + move[1]
            if not (min_x <= neighbor[0] <= max_x and min_y <= neighbor[1] <= max_y):
                continue
            if neighbor in blocked and neighbor != target:
                continue
            step = math.sqrt(2.0) if move[0] and move[1] else 1.0
            bend = 0.18 if direction is not None and direction != move else 0.0
            next_cost = current_cost + step + bend
            next_state = (neighbor, move)
            if next_cost >= cost.get(next_state, float("inf")):
                continue
            cost[next_state] = next_cost
            parent[next_state] = state
            heuristic = math.hypot(target[0] - neighbor[0], target[1] - neighbor[1])
            heapq.heappush(queue, (next_cost + heuristic, next_cost, neighbor, move))

    if final_state is None:
        raise RuntimeError(f"No path for {net_name} from {start} to {end}")

    keys = []
    state = final_state
    while state in parent:
        keys.append(state[0])
        state = parent[state]
    keys.append(source)
    keys.reverse()

    path = [start]
    previous_direction = None
    for first, second in zip(keys, keys[1:]):
        direction = second[0] - first[0], second[1] - first[1]
        if previous_direction is not None and direction != previous_direction:
            path.append(grid_point(first))
        previous_direction = direction
    path.extend((grid_point(target), end))

    compact = []
    for item in path:
        if not compact or math.hypot(item[0] - compact[-1][0], item[1] - compact[-1][1]) > 0.01:
            compact.append(item)
    return compact


def add_track(board, net_name, layer, start, end, width):
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(board.FindNet(net_name))
    track.SetLayer(layer)
    track.SetWidth(pcbnew.FromMM(width))
    track.SetStart(point(start))
    track.SetEnd(point(end))
    board.Add(track)


def route(board, net_name, layer, start, end, width=0.20):
    path = find_path(board, net_name, layer, start, end, width)
    for first, second in zip(path, path[1:]):
        add_track(board, net_name, layer, first, second, width)
    print(net_name, board.GetLayerName(layer), start, "->", end, len(path), "points")


def main():
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    route(board, "S2_3V3", pcbnew.In1_Cu, (109.395, 120.231), (112.620, 153.000), 0.30)
    route(board, "S2_3V3", pcbnew.In1_Cu, (112.620, 153.000), (254.700, 151.925), 0.30)
    route(board, "S2_3V3", pcbnew.In1_Cu, (254.700, 151.925), (254.700, 139.875), 0.30)
    route(board, "S2_3V3", pcbnew.In1_Cu, (254.700, 139.875), (254.700, 127.825), 0.30)
    route(board, "S1_3V3", pcbnew.In2_Cu, (52.241, 74.783), (248.938, 87.817), 0.30)
    route(board, "CH7_DIAG", pcbnew.In1_Cu, (198.914, 66.023), (217.380, 137.760), 0.20)

    # CH5 has an SMD source, so add a short top-layer escape and a through via.
    via_position = (137.175, 66.000)
    via = pcbnew.PCB_VIA(board)
    via.SetNet(board.FindNet("CH5_INA_MCU"))
    via.SetPosition(point(via_position))
    via.SetWidth(pcbnew.FromMM(0.65))
    via.SetDrill(pcbnew.FromMM(0.30))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(via)
    add_track(board, "CH5_INA_MCU", pcbnew.F_Cu, (137.175, 64.000), via_position, 0.20)
    route(board, "CH5_INA_MCU", pcbnew.In1_Cu, via_position, (195.160, 150.460), 0.20)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD_PATH), board)


if __name__ == "__main__":
    main()
