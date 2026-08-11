"""Add a compact redundant via group at the CH2 OUTA layer transition."""

from __future__ import annotations

import sys

import pcbnew


POSITIONS = (
    (53.250, 25.550),
    (53.850, 26.150),
    (54.450, 26.750),
)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: add_universal4ch_ch2_outa_vias.py INPUT OUTPUT")
    board = pcbnew.LoadBoard(sys.argv[1])
    net = board.FindNet("CH2_OUTA")
    for position in POSITIONS:
        via = pcbnew.PCB_VIA(board)
        via.SetNet(net)
        via.SetPosition(pcbnew.VECTOR2I_MM(*position))
        via.SetWidth(pcbnew.FromMM(0.60))
        via.SetDrill(pcbnew.FromMM(0.30))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        board.Add(via)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[2], board)


if __name__ == "__main__":
    main()
