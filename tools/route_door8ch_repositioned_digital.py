"""Route reed and low-voltage supply gaps after the connector swap."""

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
    pad = footprint.FindPadByNumber(str(number)) if footprint else None
    if pad is None:
        raise RuntimeError(f"Missing {reference}.{number}")
    return mm(pad.GetPosition())


def add_via(board, net_name, position):
    via = pcbnew.PCB_VIA(board)
    via.SetNet(board.FindNet(net_name))
    via.SetPosition(pcbnew.VECTOR2I_MM(*position))
    via.SetWidth(pcbnew.FromMM(0.65))
    via.SetDrill(pcbnew.FromMM(0.30))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(via)


def route_any(board, net_name, start, end, width, layers):
    failures = []
    for layer in layers:
        try:
            path = grid_router.find_path(board, net_name, layer, start, end, width)
        except RuntimeError as error:
            failures.append(board.GetLayerName(layer))
            continue
        for first, second in zip(path, path[1:]):
            grid_router.add_track(board, net_name, layer, first, second, width)
        print(net_name, board.GetLayerName(layer), start, "->", end, len(path), "points")
        return
    raise RuntimeError(f"No route for {net_name} on {', '.join(failures)}")


board = pcbnew.LoadBoard(str(BOARD_PATH))
grid_router.GRID = 0.50
grid_router.CLEARANCE = 0.35

reed_routes = (
    ("REED_A_OPEN", "J201", "MOD1", 6),
    ("REED_A_CLOSED", "J202", "MOD1", 5),
    ("REED_A_IN_PLACE", "J203", "MOD1", 38),
    ("REED_B_OPEN", "J204", "MOD2", 6),
    ("REED_B_CLOSED", "J205", "MOD2", 5),
    ("REED_B_IN_PLACE", "J206", "MOD2", 38),
)
signal_layers = (pcbnew.In2_Cu, pcbnew.In1_Cu, pcbnew.B_Cu)
for net_name, connector, module, module_pad in reed_routes:
    layers = signal_layers
    if net_name in {"REED_A_CLOSED", "REED_A_IN_PLACE", "REED_B_IN_PLACE"}:
        layers = (pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu)
        grid_router.CLEARANCE = 0.50
    else:
        grid_router.CLEARANCE = 0.35
    route_any(
        board,
        net_name,
        pad_position(board, connector, 2),
        pad_position(board, module, module_pad),
        0.20,
        layers,
    )

grid_router.CLEARANCE = 0.35
supply_layers = (pcbnew.In2_Cu, pcbnew.In1_Cu, pcbnew.B_Cu)
s1_anchor = (241.50, 71.00)
s1_transfer = (239.00, 74.00)
route_any(board, "S1_3V3", s1_anchor, s1_transfer, 0.30, (pcbnew.In2_Cu,))
add_via(board, "S1_3V3", s1_transfer)
route_any(board, "S1_3V3", s1_transfer, pad_position(board, "J203", 1), 0.30, (pcbnew.In1_Cu, pcbnew.B_Cu))
route_any(board, "S1_3V3", pad_position(board, "J203", 1), pad_position(board, "J202", 1), 0.30, supply_layers)
route_any(board, "S1_3V3", pad_position(board, "J202", 1), pad_position(board, "J201", 1), 0.30, supply_layers)

r210_pad = pad_position(board, "R210", 2)
r210_via = (217.00, r210_pad[1])
add_via(board, "S1_3V3", r210_via)
grid_router.add_track(board, "S1_3V3", pcbnew.F_Cu, r210_pad, r210_via, 0.30)
grid_router.CLEARANCE = 0.50
route_any(board, "S1_3V3", r210_via, s1_transfer, 0.30, (pcbnew.In1_Cu, pcbnew.B_Cu))
grid_router.CLEARANCE = 0.35
j220_supply = pad_position(board, "J220", 1)
route_any(board, "S1_3V3", j220_supply, s1_transfer, 0.30, (pcbnew.In1_Cu, pcbnew.B_Cu))

add_via(board, "S2_3V3", (252.00, 154.50))
route_any(board, "S2_3V3", (252.00, 154.50), pad_position(board, "J206", 1), 0.30, supply_layers)
route_any(board, "S2_3V3", pad_position(board, "J206", 1), pad_position(board, "J205", 1), 0.30, supply_layers)
route_any(board, "S2_3V3", pad_position(board, "J205", 1), pad_position(board, "J204", 1), 0.30, supply_layers)

s4_upper = (230.825, 75.00)
add_via(board, "S4_3V3", s4_upper)
route_any(board, "S4_3V3", s4_upper, (228.00, 121.50), 0.30, (pcbnew.B_Cu, pcbnew.In2_Cu, pcbnew.In1_Cu))
route_any(board, "S4_3V3", (228.00, 121.50), (198.00, 121.50), 0.30, (pcbnew.B_Cu, pcbnew.In2_Cu))
route_any(board, "S4_3V3", (228.00, 153.00), pad_position(board, "MOD4", 11), 0.30, (pcbnew.B_Cu, pcbnew.In2_Cu))
route_any(board, "S4_3V3", s4_upper, pad_position(board, "D1801", 2), 0.30, (pcbnew.F_Cu,))

for zone in board.Zones():
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
