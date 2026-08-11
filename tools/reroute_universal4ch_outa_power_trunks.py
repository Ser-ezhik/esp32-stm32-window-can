"""Add short CH3/CH4 OUTA trunks with redundant power-layer transitions."""

from __future__ import annotations

import sys

import pcbnew


ROUTES = {
    "CH3_OUTA": {
        "bottom_entry": ((77.605, 8.000), (79.000, 9.395), (79.000, 14.800)),
        "entry_vias": ((79.000, 14.000), (79.000, 14.800), (79.000, 15.600)),
        "front": ((79.000, 14.800), (80.575, 16.375), (80.575, 25.800)),
        "exit_vias": ((79.675, 25.800), (80.575, 25.800), (81.475, 25.800)),
        "target": (80.575, 28.665),
    },
    "CH4_OUTA": {
        "bottom_entry": ((111.105, 8.000), (113.000, 9.895), (113.000, 14.300)),
        "entry_vias": ((113.000, 13.500), (113.000, 14.300), (113.000, 15.100)),
        "front": ((113.000, 14.300), (111.575, 15.725), (111.575, 26.300)),
        "exit_vias": ((110.675, 26.300), (111.575, 26.300), (112.475, 26.300)),
        "target": (111.575, 28.665),
    },
}


def add_track(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    layer: int,
    start: tuple[float, float],
    end: tuple[float, float],
    width_mm: float = 0.50,
) -> None:
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(net)
    track.SetLayer(layer)
    track.SetStart(pcbnew.VECTOR2I_MM(*start))
    track.SetEnd(pcbnew.VECTOR2I_MM(*end))
    track.SetWidth(pcbnew.FromMM(width_mm))
    board.Add(track)


def add_via_array(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    points: tuple[tuple[float, float], ...],
) -> None:
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        for start, end in zip(points, points[1:]):
            add_track(board, net, layer, start, end)

    for x_mm, y_mm in points:
        via = pcbnew.PCB_VIA(board)
        via.SetNet(net)
        via.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
        via.SetWidth(pcbnew.FromMM(0.80))
        via.SetDrill(pcbnew.FromMM(0.40))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        board.Add(via)


def add_route(board: pcbnew.BOARD, net_name: str, route: dict) -> None:
    net = board.FindNet(net_name)
    for start, end in zip(route["bottom_entry"], route["bottom_entry"][1:]):
        add_track(board, net, pcbnew.B_Cu, start, end)
    add_via_array(board, net, route["entry_vias"])

    for start, end in zip(route["front"], route["front"][1:]):
        add_track(board, net, pcbnew.F_Cu, start, end)
    add_via_array(board, net, route["exit_vias"])
    add_track(board, net, pcbnew.B_Cu, route["exit_vias"][1], route["target"])


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: reroute_universal4ch_outa_power_trunks.py INPUT OUTPUT")

    board = pcbnew.LoadBoard(sys.argv[1])
    for net_name, route in ROUTES.items():
        add_route(board, net_name, route)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[2], board)
    print("Added CH3_OUTA and CH4_OUTA trunks with dual 3-via transitions")


if __name__ == "__main__":
    main()
