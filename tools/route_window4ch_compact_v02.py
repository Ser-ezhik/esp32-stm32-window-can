"""Autoroute all low-voltage nets after the WINDOW-4CH v0.2 repack."""

from __future__ import annotations

import math
from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
LOCK_PATH = BOARD_PATH.with_name("~WINDOW-4CH.kicad_pcb.lck")

if LOCK_PATH.exists():
    raise SystemExit("Close WINDOW-4CH in KiCad before routing the board")

grid.GRID = 0.50
grid.CLEARANCE = 0.35


def xy(position):
    return round(pcbnew.ToMM(position.x), 4), round(pcbnew.ToMM(position.y), 4)


def pad_layer(pad):
    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
        return None
    if pad.IsOnLayer(pcbnew.F_Cu):
        return pcbnew.F_Cu
    return pcbnew.B_Cu


def net_width(net_name):
    if net_name in {"LOGIC_12V_IN", "LOGIC_12V_PROTECTED", "LOGIC_12V_FUSED"}:
        return 0.80
    if net_name in {"LOGIC_5V", "S1_5V_HOLD"}:
        return 0.60
    if net_name.endswith("3V3") or net_name in {"CANH_BUS", "CANL_BUS", "CANH_ENTRY", "CANL_ENTRY"}:
        return 0.30
    return 0.20


def mst_edges(pads):
    """Return short deterministic pad-to-pad edges for one electrical net."""
    connected = {0}
    remaining = set(range(1, len(pads)))
    edges = []
    while remaining:
        best = None
        for source in connected:
            sx, sy = xy(pads[source].GetPosition())
            for target in remaining:
                tx, ty = xy(pads[target].GetPosition())
                candidate = (math.hypot(tx - sx, ty - sy), source, target)
                if best is None or candidate < best:
                    best = candidate
        _, source, target = best
        edges.append((pads[source], pads[target]))
        connected.add(target)
        remaining.remove(target)
    return edges


def route_edge(board, net_name, first, second, width):
    start = xy(first.GetPosition())
    end = xy(second.GetPosition())
    first_layer = pad_layer(first)
    second_layer = pad_layer(second)
    router.route_multilayer(
        board,
        net_name,
        start,
        end,
        width,
        first_layer,
        second_layer if second_layer is not None else pcbnew.F_Cu,
        second.GetAttribute() == pcbnew.PAD_ATTRIB_PTH,
    )


board = pcbnew.LoadBoard(str(BOARD_PATH))

pads_by_net = {}
for footprint in board.GetFootprints():
    for pad in footprint.Pads():
        name = pad.GetNetname()
        if name and name != "GND":
            pads_by_net.setdefault(name, []).append(pad)

# These nets retained their complete high-current or local VNH copper.
retained = {
    "CH1_OUTA", "CH1_OUTB", "CH2_OUTA", "CH2_OUTB",
    "CH3_OUTA", "CH3_OUTB", "CH4_OUTA", "CH4_OUTB",
    "FUSED_12V_CH1", "FUSED_12V_CH2", "FUSED_12V_CH3", "FUSED_12V_CH4",
}
for channel in range(1, 5):
    retained.update({
        f"CH{channel}_INA", f"CH{channel}_INB", f"CH{channel}_PWM",
        f"CH{channel}_CS_DIS", f"CH{channel}_CS_RAW",
    })

def route_priority(net_name):
    if net_width(net_name) > 0.30:
        return 0
    if net_name.startswith("CH"):
        return 1
    if "UART" in net_name or "CAN" in net_name:
        return 2
    if net_name.startswith("S1_") or net_name.startswith("S2_"):
        return 3
    if net_name.startswith("CAP_"):
        return 4
    if net_name.startswith("REED_"):
        return 5
    return 3


jobs = []
for net_name, pads in pads_by_net.items():
    if net_name in retained or len(pads) < 2:
        continue
    width = net_width(net_name)
    span = max(
        (math.hypot(xy(a.GetPosition())[0] - xy(b.GetPosition())[0],
                    xy(a.GetPosition())[1] - xy(b.GetPosition())[1])
         for a in pads for b in pads),
        default=0,
    )
    jobs.append((route_priority(net_name), -width, -span, net_name, pads))

failures = []
for _, _, _, net_name, pads in sorted(jobs):
    width = net_width(net_name)
    print(f"Routing {net_name}: {len(pads)} pads, {width:.2f} mm")
    for first, second in mst_edges(pads):
        try:
            route_edge(board, net_name, first, second, width)
        except RuntimeError as error:
            failures.append(str(error))
            print(f"DEFERRED: {error}")
    pcbnew.SaveBoard(str(BOARD_PATH), board)

# Ground planes provide the return network; stitching keeps all four pours tied.
for x in range(10, 151, 15):
    for y in range(80, 146, 15):
        key = grid.grid_key((x, y))
        blocked = [grid.build_blocked(board, "GND", layer, 0.80)
                   for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)]
        if all(key not in layer_blocked for layer_blocked in blocked):
            router.add_via(board, "GND", (x, y), 0.80, 0.40)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Completed compact WINDOW-4CH low-voltage routing; deferred {len(failures)} edges")
for failure in failures:
    print(f"  {failure}")
