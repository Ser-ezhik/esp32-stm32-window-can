"""Remove only newly added satellite vias that are named in a KiCad DRC report."""

from __future__ import annotations

import re
import sys

import pcbnew


def key(position: pcbnew.VECTOR2I) -> tuple[int, int]:
    return round(pcbnew.ToMM(position.x) * 1000), round(pcbnew.ToMM(position.y) * 1000)


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: prune.py ORIGINAL SATELLITE_BOARD DRC_REPORT OUTPUT")
    original = pcbnew.LoadBoard(sys.argv[1])
    board = pcbnew.LoadBoard(sys.argv[2])
    report = open(sys.argv[3], encoding="utf-8", errors="replace").read()
    original_vias = {
        key(item.GetPosition())
        for item in original.GetTracks()
        if isinstance(item, pcbnew.PCB_VIA)
    }
    bad = {
        (round(float(x) * 1000), round(float(y) * 1000))
        for x, y in re.findall(
            r"@\(([-\d.]+) mm,\s*([-\d.]+) mm\): Via", report
        )
    }
    removed = 0
    for item in list(board.GetTracks()):
        if not isinstance(item, pcbnew.PCB_VIA):
            continue
        position = key(item.GetPosition())
        is_reported = any(
            abs(position[0] - bad_position[0]) <= 1
            and abs(position[1] - bad_position[1]) <= 1
            for bad_position in bad
        )
        if position not in original_vias and is_reported:
            board.Delete(item)
            removed += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[4], board)
    print(f"Removed {removed} conflicting satellite vias")


if __name__ == "__main__":
    main()
