"""Restore only widened power tracks named by a KiCad DRC report."""

from __future__ import annotations

import re
import sys

import pcbnew

from reinforce_universal4ch_power import main_power_segments


TRACK_RE = re.compile(
    r"@\(([0-9.]+) mm, ([0-9.]+) mm\): Track \[([^]]+)] on ([FB]\.Cu)"
)


def xy(position):
    return round(pcbnew.ToMM(position.x), 4), round(pcbnew.ToMM(position.y), 4)


def main():
    if len(sys.argv) != 5:
        raise SystemExit("usage: reduce_reported_universal4ch_power_tracks.py INPUT REPORT OUTPUT BASELINE")
    board = pcbnew.LoadBoard(sys.argv[1])
    baseline = pcbnew.LoadBoard(sys.argv[4])
    baseline_widths = {}
    for track in main_power_segments(baseline):
        baseline_widths[(track.GetNetname(), pcbnew.LayerName(track.GetLayer()), xy(track.GetStart()), xy(track.GetEnd()))] = track.GetWidth()
    report = open(sys.argv[2], encoding="utf-8", errors="replace").read()
    report = report.split("[silk_overlap]", 1)[0]
    reported = {
        (net, layer, (round(float(x), 4), round(float(y), 4)))
        for x, y, net, layer in TRACK_RE.findall(report)
    }
    changed = 0
    for track in main_power_segments(board):
        net = track.GetNetname()
        layer = pcbnew.LayerName(track.GetLayer())
        if (net, layer, xy(track.GetStart())) in reported or (net, layer, xy(track.GetEnd())) in reported:
            key = (net, layer, xy(track.GetStart()), xy(track.GetEnd()))
            reverse = (net, layer, xy(track.GetEnd()), xy(track.GetStart()))
            track.SetWidth(baseline_widths.get(key, baseline_widths.get(reverse, pcbnew.FromMM(0.2))))
            changed += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[3], board)
    print(f"Restored {changed} clearance-limited power segments")


if __name__ == "__main__":
    main()
