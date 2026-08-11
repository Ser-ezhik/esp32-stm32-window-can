"""Expand CH1 OUTA to nine vias and CH2 OUTA to six vias."""

from __future__ import annotations

import sys

import pcbnew


CH1_ADDITIONS = (
    (14.50, 30.50),
    (15.25, 30.50),
    (16.00, 30.50),
    (14.50, 31.50),
    (15.25, 31.50),
)
CH2_ADDITIONS = ((52.50, 25.75), (52.50, 26.55))


def add_track(board, net, layer, start, end):
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(net)
    track.SetLayer(layer)
    track.SetStart(pcbnew.VECTOR2I_MM(*start))
    track.SetEnd(pcbnew.VECTOR2I_MM(*end))
    track.SetWidth(pcbnew.FromMM(0.60))
    board.Add(track)


def add_via(board, net, position):
    via = pcbnew.PCB_VIA(board)
    via.SetNet(net)
    via.SetPosition(pcbnew.VECTOR2I_MM(*position))
    via.SetWidth(pcbnew.FromMM(0.80))
    via.SetDrill(pcbnew.FromMM(0.40))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(via)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: expand_universal4ch_ch1_ch2_via_banks.py INPUT OUTPUT")
    board = pcbnew.LoadBoard(sys.argv[1])
    ch1 = board.FindNet("CH1_OUTA")
    ch2 = board.FindNet("CH2_OUTA")
    for position in CH1_ADDITIONS:
        add_via(board, ch1, position)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        add_track(board, ch2, layer, CH2_ADDITIONS[0], CH2_ADDITIONS[1])
    for position in CH2_ADDITIONS:
        add_via(board, ch2, position)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[2], board)


if __name__ == "__main__":
    main()
