"""Route the DOOR-8CH power monitor and S1 hold-up supply."""

from __future__ import annotations

import os
import heapq
import math
from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid_router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = Path(os.environ.get(
    "BOARD_PATH", ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
))


def point(position):
    return pcbnew.VECTOR2I_MM(*position)


def xy(position):
    return round(pcbnew.ToMM(position.x), 4), round(pcbnew.ToMM(position.y), 4)


def pad_position(board, reference, number):
    footprint = board.FindFootprintByReference(reference)
    pad = next(pad for pad in footprint.Pads() if pad.GetNumber() == str(number))
    return xy(pad.GetPosition())


def add_track(board, net_name, layer, start, end, width=0.25):
    if start != end:
        grid_router.add_track(board, net_name, layer, start, end, width)


def add_path(board, net_name, layer, positions, width=0.25):
    for start, end in zip(positions, positions[1:]):
        add_track(board, net_name, layer, start, end, width)


def add_via(board, net_name, position, diameter=0.65, drill=0.30):
    target = point(position)
    for item in board.GetTracks():
        if (isinstance(item, pcbnew.PCB_VIA) and item.GetNetname() == net_name and
                item.GetPosition() == target):
            return
    via = pcbnew.PCB_VIA(board)
    via.SetNet(board.FindNet(net_name))
    via.SetPosition(point(position))
    via.SetWidth(pcbnew.FromMM(diameter))
    via.SetDrill(pcbnew.FromMM(drill))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(via)


def route_any(board, net_name, start, end, width, layers):
    errors = []
    for layer in layers:
        try:
            grid_router.route(board, net_name, layer, start, end, width)
            return layer
        except RuntimeError as error:
            errors.append(str(error))
    raise RuntimeError("; ".join(errors))


def route_multilayer(board, net_name, start, end, width=0.20, start_layer=None,
                     end_layer=pcbnew.F_Cu, end_through_hole=False):
    layers = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
    blocked = [grid_router.build_blocked(board, net_name, layer, width) for layer in layers]
    via_blocked = [grid_router.build_blocked(board, net_name, layer, 0.65) for layer in layers]
    source = grid_router.grid_key(start)
    target = grid_router.grid_key(end)
    for layer_blocked in blocked:
        for center in (source, target):
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    layer_blocked.discard((center[0] + dx, center[1] + dy))

    min_key = round(grid_router.EDGE / grid_router.GRID)
    max_x = round((260.0 - grid_router.EDGE) / grid_router.GRID)
    max_y = round((160.0 - grid_router.EDGE) / grid_router.GRID)
    moves = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    queue = []
    cost = {}
    parent = {}
    initial_layers = range(len(layers)) if start_layer is None else (layers.index(start_layer),)
    for layer_index in initial_layers:
        state = (source[0], source[1], layer_index)
        cost[state] = 0.0
        heapq.heappush(queue, (math.hypot(target[0] - source[0], target[1] - source[1]), 0.0, state))

    final = None
    while queue:
        _, current_cost, state = heapq.heappop(queue)
        if current_cost != cost.get(state):
            continue
        x, y, layer_index = state
        if (x, y) == target:
            if end_through_hole or layers[layer_index] == end_layer:
                final = state
                break
        for dx, dy in moves:
            neighbor = (x + dx, y + dy, layer_index)
            if not (min_key <= neighbor[0] <= max_x and min_key <= neighbor[1] <= max_y):
                continue
            if (neighbor[0], neighbor[1]) in blocked[layer_index]:
                continue
            next_cost = current_cost + (math.sqrt(2.0) if dx and dy else 1.0)
            if next_cost < cost.get(neighbor, float("inf")):
                cost[neighbor] = next_cost
                parent[neighbor] = state
                heuristic = math.hypot(target[0] - neighbor[0], target[1] - neighbor[1])
                heapq.heappush(queue, (next_cost + heuristic, next_cost, neighbor))
        for next_layer in range(len(layers)):
            if ((x, y) in (source, target) or next_layer == layer_index
                    or any((x, y) in layer_blocked for layer_blocked in via_blocked)):
                continue
            neighbor = (x, y, next_layer)
            next_cost = current_cost + 8.0 + abs(next_layer - layer_index)
            if next_cost < cost.get(neighbor, float("inf")):
                cost[neighbor] = next_cost
                parent[neighbor] = state
                heuristic = math.hypot(target[0] - x, target[1] - y)
                heapq.heappush(queue, (next_cost + heuristic, next_cost, neighbor))

    if final is None:
        raise RuntimeError(f"No multilayer path for {net_name} from {start} to {end}")

    states = [final]
    while states[-1] in parent:
        states.append(parent[states[-1]])
    states.reverse()

    segment = [(states[0][0], states[0][1])]
    current_layer = states[0][2]
    for previous, state in zip(states, states[1:]):
        key = (state[0], state[1])
        if state[2] != current_layer:
            positions = [grid_router.grid_point(item) for item in segment]
            compact = [positions[0]]
            for index in range(1, len(positions) - 1):
                a, b, c = positions[index - 1], positions[index], positions[index + 1]
                if (round(b[0] - a[0], 4), round(b[1] - a[1], 4)) != (round(c[0] - b[0], 4), round(c[1] - b[1], 4)):
                    compact.append(b)
            compact.append(positions[-1])
            add_path(board, net_name, layers[current_layer], compact, width)
            via_position = grid_router.grid_point((state[0], state[1]))
            if via_position not in (start, end):
                add_via(board, net_name, via_position)
            current_layer = state[2]
            segment = [key]
        else:
            segment.append(key)
    positions = [grid_router.grid_point(item) for item in segment]
    compact = [positions[0]]
    for index in range(1, len(positions) - 1):
        a, b, c = positions[index - 1], positions[index], positions[index + 1]
        if (round(b[0] - a[0], 4), round(b[1] - a[1], 4)) != (round(c[0] - b[0], 4), round(c[1] - b[1], 4)):
            compact.append(b)
    compact.append(positions[-1])
    add_path(board, net_name, layers[current_layer], compact, width)

    source_grid = grid_router.grid_point(source)
    target_grid = grid_router.grid_point(target)
    initial_layer = layers[states[0][2]]
    final_layer = layers[states[-1][2]]
    if source_grid != start:
        add_track(board, net_name, initial_layer, start, source_grid, width)
    if target_grid != end:
        if end_through_hole:
            add_track(board, net_name, final_layer, target_grid, end, width)
        else:
            if final_layer != end_layer:
                add_via(board, net_name, target_grid)
            add_track(board, net_name, end_layer, target_grid, end, width)
    print(net_name, "multilayer", start, "->", end, "states", len(states))


def main():
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    # S1 hold-up path: common 5 V -> SS34 -> 4700 uF -> MOD1 5 V.
    logic5_via = (23.0, 158.0)
    add_via(board, "LOGIC_5V", logic5_via, 0.80, 0.35)
    add_track(board, "LOGIC_5V", pcbnew.B_Cu, pad_position(board, "D280", 2), logic5_via, 0.80)
    add_track(board, "S1_5V_HOLD", pcbnew.B_Cu, pad_position(board, "D280", 1), pad_position(board, "C280", 1), 0.80)
    route_multilayer(board, "S1_5V_HOLD", pad_position(board, "C280", 1), pad_position(board, "MOD1", 21), 0.50)

    # Local TLV6700 divider, filter and open-drain output wiring.
    add_path(board, "LOGIC_12V_FUSED", pcbnew.F_Cu,
             (pad_position(board, "R270", 1), (198.0, 110.175), pad_position(board, "C270", 1)), 0.25)
    add_track(board, "LOGIC_12V_FUSED", pcbnew.F_Cu, pad_position(board, "C270", 1), pad_position(board, "U270", 5), 0.25)

    add_track(board, "PGOOD_SENSE", pcbnew.F_Cu, pad_position(board, "R270", 2), pad_position(board, "R271", 1), 0.20)
    add_track(board, "PGOOD_SENSE", pcbnew.F_Cu, pad_position(board, "R271", 1), pad_position(board, "C271", 1), 0.20)
    sense_source_via = (206.0, 110.5)
    sense_target_via = (197.5, 122.5)
    add_via(board, "PGOOD_SENSE", sense_source_via)
    add_via(board, "PGOOD_SENSE", sense_target_via)
    add_track(board, "PGOOD_SENSE", pcbnew.F_Cu, pad_position(board, "C271", 1), sense_source_via, 0.20)
    add_path(board, "PGOOD_SENSE", pcbnew.F_Cu,
             (sense_target_via, (194.0, 122.5), pad_position(board, "U270", 3)), 0.20)
    route_multilayer(board, "PGOOD_SENSE", sense_source_via, sense_target_via, 0.20)

    add_track(board, "POWER_GOOD", pcbnew.F_Cu, pad_position(board, "U270", 1), pad_position(board, "U270", 6), 0.20)
    add_track(board, "POWER_GOOD", pcbnew.F_Cu, pad_position(board, "U270", 1), pad_position(board, "R272", 2), 0.20)

    # Protected 12 V reaches the monitor over an inner layer.
    source12_via = (101.8, 95.0)
    monitor12_via = (188.0, 110.5)
    add_via(board, "LOGIC_12V_FUSED", source12_via)
    add_via(board, "LOGIC_12V_FUSED", monitor12_via)
    add_track(board, "LOGIC_12V_FUSED", pcbnew.F_Cu, (101.8, 93.0), source12_via, 0.25)
    add_track(board, "LOGIC_12V_FUSED", pcbnew.F_Cu, monitor12_via, pad_position(board, "R270", 1), 0.25)
    route_any(board, "LOGIC_12V_FUSED", source12_via, monitor12_via, 0.25, (pcbnew.In2_Cu, pcbnew.In1_Cu))

    # POWER_GOOD is pulled up only by S1 and delivered to PC13.
    pgood_via = (185.0, 112.0)
    add_path(board, "POWER_GOOD", pcbnew.F_Cu,
             (pad_position(board, "R272", 2), (188.0, 112.0), pgood_via), 0.20)
    route_multilayer(board, "POWER_GOOD", pgood_via, pad_position(board, "MOD1", 30), 0.20, pcbnew.F_Cu)

    # Retained EEPROM supply and PGOOD pull-up join the S1 local 3.3 V rail.
    eeprom_via = (89.5, 134.5)
    s1_via = (49.1216, 116.9546)
    pullup_via = (190.0, 120.0)
    nearby_s1_via = (217.0, 87.175)
    for position in (eeprom_via, pullup_via):
        add_via(board, "S1_3V3", position)
    add_track(board, "S1_3V3", pcbnew.F_Cu, eeprom_via, (88.7785, 134.2815), 0.30)
    route_multilayer(board, "S1_3V3", s1_via, eeprom_via, 0.30)
    add_track(board, "S1_3V3", pcbnew.F_Cu, pad_position(board, "R272", 1), pullup_via, 0.25)
    route_multilayer(board, "S1_3V3", pullup_via, nearby_s1_via, 0.25)

    # Move the new references away from component outlines.
    board.FindFootprintByReference("U270").Reference().SetPosition(point((195.0, 109.0)))
    board.FindFootprintByReference("D280").Reference().SetPosition(point((20.0, 156.0)))
    board.FindFootprintByReference("RF1").Reference().SetPosition(point((8.0, 112.0)))
    # The monitor passives are packed tightly beside U270. Keep their values on
    # the assembly drawing and suppress only the crowded board references.
    for reference in ("R270", "R271", "R272", "C270", "C271"):
        board.FindFootprintByReference(reference).Reference().SetVisible(False)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print("Routed POWER_GOOD and the S1 hold-up supply")


if __name__ == "__main__":
    main()
