"""Reinforce the CH4 OUTB spur with a four-via transition bank."""

from __future__ import annotations

import sys

import pcbnew


Y = 10.7221
X_POINTS = (105.0262, 105.8262, 106.6262)
SECOND_ROW = (105.8262, 11.5221)


def add_track(board, net, layer):
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(net)
    track.SetLayer(layer)
    track.SetStart(pcbnew.VECTOR2I_MM(X_POINTS[0], Y))
    track.SetEnd(pcbnew.VECTOR2I_MM(X_POINTS[-1], Y))
    track.SetWidth(pcbnew.FromMM(0.60))
    board.Add(track)
    branch = pcbnew.PCB_TRACK(board)
    branch.SetNet(net)
    branch.SetLayer(layer)
    branch.SetStart(pcbnew.VECTOR2I_MM(X_POINTS[1], Y))
    branch.SetEnd(pcbnew.VECTOR2I_MM(*SECOND_ROW))
    branch.SetWidth(pcbnew.FromMM(0.60))
    board.Add(branch)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: reinforce_universal4ch_ch4_outb_transition.py INPUT OUTPUT")
    board = pcbnew.LoadBoard(sys.argv[1])
    net = board.FindNet("CH4_OUTB")
    add_track(board, net, pcbnew.F_Cu)
    add_track(board, net, pcbnew.B_Cu)
    for x, y in ((X_POINTS[1], Y), (X_POINTS[2], Y), SECOND_ROW):
        via = pcbnew.PCB_VIA(board)
        via.SetNet(net)
        via.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        via.SetWidth(pcbnew.FromMM(0.80))
        via.SetDrill(pcbnew.FromMM(0.40))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        board.Add(via)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[2], board)


if __name__ == "__main__":
    main()
