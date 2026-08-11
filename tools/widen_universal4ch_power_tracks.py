"""Widen every selected connector-to-driver power segment conservatively."""

from __future__ import annotations

import sys

import pcbnew

from reinforce_universal4ch_power import main_power_segments


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: widen_universal4ch_power_tracks.py INPUT OUTPUT MIN_WIDTH_MM")
    board = pcbnew.LoadBoard(sys.argv[1])
    minimum = float(sys.argv[3])
    changed = 0
    for track in main_power_segments(board):
        if pcbnew.ToMM(track.GetWidth()) < minimum:
            track.SetWidth(pcbnew.FromMM(minimum))
            changed += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[2], board)
    print(f"Widened {changed} main power segments to at least {minimum:.3f} mm")


if __name__ == "__main__":
    main()
