"""Add the DOOR-8CH power-fail monitor and S1 hold-up supply components."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = Path(os.environ.get(
    "BOARD_PATH", ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
))
FP_ROOT = Path(sys.executable).resolve().parents[1] / "share" / "kicad" / "footprints"


def point(x, y):
    return pcbnew.VECTOR2I_MM(x, y)


def ensure_net(board, name):
    net = board.FindNet(name)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
    return net


def load_footprint(library, name):
    footprint = pcbnew.FootprintLoad(str(FP_ROOT / f"{library}.pretty"), name)
    if footprint is None:
        raise RuntimeError(f"Cannot load {library}:{name}")
    return footprint


def add_component(board, reference, value, library, footprint_name, x, y, rotation=0, bottom=False):
    if board.FindFootprintByReference(reference) is not None:
        raise RuntimeError(f"{reference} already exists")
    footprint = load_footprint(library, footprint_name)
    footprint.SetReference(reference)
    footprint.SetValue(value)
    footprint.SetPosition(point(x, y))
    board.Add(footprint)
    if bottom:
        footprint.Flip(footprint.GetPosition(), False)
    footprint.SetOrientationDegrees(rotation)
    return footprint


def set_pad_nets(board, footprint, assignments):
    for pad in footprint.Pads():
        number = str(pad.GetNumber())
        if number in assignments:
            pad.SetNet(ensure_net(board, assignments[number]))


def same_position(position, x, y, tolerance=0.01):
    return abs(pcbnew.ToMM(position.x) - x) < tolerance and abs(pcbnew.ToMM(position.y) - y) < tolerance


def main():
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    power_good = ensure_net(board, "POWER_GOOD")
    ensure_net(board, "PGOOD_SENSE")
    s1_hold = ensure_net(board, "S1_5V_HOLD")

    u270 = add_component(board, "U270", "TLV6700DDCR_POWER_MONITOR", "Package_TO_SOT_SMD", "SOT-23-6", 195.0, 116.0)
    set_pad_nets(board, u270, {
        "1": "POWER_GOOD", "2": "GND", "3": "PGOOD_SENSE",
        "4": "GND", "5": "LOGIC_12V_FUSED", "6": "POWER_GOOD",
    })

    components = (
        ("R270", "226K_1%_PGOOD_TOP", 200.0, 111.0, {"1": "LOGIC_12V_FUSED", "2": "PGOOD_SENSE"}),
        ("R271", "10K_1%_PGOOD_BOTTOM", 200.0, 114.0, {"1": "PGOOD_SENSE", "2": "GND"}),
        ("R272", "10K_PGOOD_PULLUP", 190.0, 116.0, {"1": "S1_3V3", "2": "POWER_GOOD"}),
    )
    for reference, value, x, y, nets in components:
        rotation = 270 if reference in ("R270", "R271") else 90
        footprint = add_component(board, reference, value, "Resistor_SMD", "R_0603_1608Metric", x, y, rotation)
        set_pad_nets(board, footprint, nets)

    capacitors = (
        ("C270", "100NF_25V_PGOOD_VDD", 198.0, 116.0, {"1": "LOGIC_12V_FUSED", "2": "GND"}),
        ("C271", "100NF_PGOOD_FILTER", 203.0, 113.0, {"1": "PGOOD_SENSE", "2": "GND"}),
    )
    for reference, value, x, y, nets in capacitors:
        rotation = 270
        footprint = add_component(board, reference, value, "Capacitor_SMD", "C_0603_1608Metric", x, y, rotation)
        set_pad_nets(board, footprint, nets)

    d280 = add_component(board, "D280", "SS34_S1_HOLDUP_ISOLATION", "Diode_SMD", "D_SMA", 25.0, 156.0, 270, bottom=True)
    set_pad_nets(board, d280, {"1": "S1_5V_HOLD", "2": "LOGIC_5V"})

    c280 = add_component(board, "C280", "4700UF_10V_LOW_ESR_S1_HOLDUP", "Capacitor_THT", "CP_Radial_D12.5mm_P5.00mm", 25.0, 144.0, 90)
    set_pad_nets(board, c280, {"1": "S1_5V_HOLD", "2": "GND"})

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print("Added U270 power monitor and D280/C280 S1 hold-up supply")


if __name__ == "__main__":
    main()
