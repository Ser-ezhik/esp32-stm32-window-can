"""Route all non-ground connections on the compact UNIVERSAL-2CH board."""

from __future__ import annotations

import math
from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "UNIVERSAL-2CH" / "kicad" / "UNIVERSAL-2CH.kicad_pcb"
LOCK_PATH = BOARD_PATH.with_name("~UNIVERSAL-2CH.kicad_pcb.lck")

if LOCK_PATH.exists():
    raise SystemExit("Close UNIVERSAL-2CH in KiCad before routing the board")

grid.GRID = 0.50
grid.CLEARANCE = 0.32
grid.PAD_EXTRA = grid.GRID
grid.EDGE = 1.00


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
    if net_name in {"S1_3V3", "LOGIC_3V3"}:
        return 0.35
    if net_name in {"CANH_ENTRY", "CANL_ENTRY", "CANH_BUS", "CANL_BUS"}:
        return 0.30
    return 0.20


def mst_edges(pads):
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
    first_layer = pad_layer(first)
    second_layer = pad_layer(second)
    router.route_multilayer(
        board,
        net_name,
        xy(first.GetPosition()),
        xy(second.GetPosition()),
        width,
        first_layer,
        second_layer if second_layer is not None else pcbnew.F_Cu,
        second.GetAttribute() == pcbnew.PAD_ATTRIB_PTH,
    )


def priority(net_name):
    if net_width(net_name) >= 0.60:
        return 0
    if net_name in {"S1_3V3", "LOGIC_3V3"}:
        return 1
    if net_name.startswith("CH"):
        return 2
    if "CAN" in net_name:
        return 3
    if net_name.startswith(("CAP_", "EEPROM_")):
        return 4
    if net_name.startswith("REED_"):
        return 5
    return 3


board = pcbnew.LoadBoard(str(BOARD_PATH))

pads_by_net = {}
for footprint in board.GetFootprints():
    for pad in footprint.Pads():
        net_name = pad.GetNetname()
        if net_name and net_name != "GND":
            pads_by_net.setdefault(net_name, []).append(pad)

retained = {
    "CH1_OUTA", "CH1_OUTB", "CH2_OUTA", "CH2_OUTB",
    "FUSED_12V_CH1", "FUSED_12V_CH2",
    "CH1_DIAG", "CH2_DIAG",
    "CAP_MOSI", "CAP_MISO", "CAP_SCK", "CAP_CS",
    "EEPROM_CS", "EEPROM_WP", "EEPROM_HOLD",
    "POWER_GOOD", "PGOOD_SENSE",
    "S1_SWDIO", "REED_A_IN_PLACE",
    "CAP_IRQ", "CAP_RESET",
    "CH1_INB_MCU", "S1_NRST",
}
for channel in (1, 2):
    retained.update({
        f"CH{channel}_INA", f"CH{channel}_INB", f"CH{channel}_PWM",
        f"CH{channel}_CS_DIS", f"CH{channel}_CS_RAW",
    })

jobs = []
for net_name, pads in pads_by_net.items():
    if net_name in retained or len(pads) < 2:
        continue
    span = max(
        math.hypot(
            xy(first.GetPosition())[0] - xy(second.GetPosition())[0],
            xy(first.GetPosition())[1] - xy(second.GetPosition())[1],
        )
        for first in pads
        for second in pads
    )
    jobs.append((priority(net_name), -net_width(net_name), -span, net_name, pads))

failures = []
for _, _, _, net_name, pads in sorted(jobs):
    width = net_width(net_name)
    print(f"Routing {net_name}: {len(pads)} pads at {width:.2f} mm")
    for first, second in mst_edges(pads):
        try:
            route_edge(board, net_name, first, second, width)
        except RuntimeError as error:
            failures.append((net_name, xy(first.GetPosition()), xy(second.GetPosition()), str(error)))
            print("  DEFERRED:", error)
    pcbnew.SaveBoard(str(BOARD_PATH), board)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)

print(f"Initial UNIVERSAL-2CH routing complete; deferred {len(failures)} edges")
for net_name, start, end, error in failures:
    print(f"  {net_name}: {start} -> {end}: {error}")
