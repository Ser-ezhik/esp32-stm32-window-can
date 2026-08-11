"""Remove geometrically duplicate power vias while preserving one instance."""

from __future__ import annotations

import sys

import pcbnew


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: deduplicate_universal4ch_power_vias.py INPUT OUTPUT")
    board = pcbnew.LoadBoard(sys.argv[1])
    seen = set()
    removed = 0
    for item in list(board.GetTracks()):
        if not isinstance(item, pcbnew.PCB_VIA):
            continue
        position = item.GetPosition()
        key = (position.x, position.y, item.GetNetCode(), item.GetDrillValue())
        if key in seen:
            board.Delete(item)
            removed += 1
        else:
            seen.add(key)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[2], board)
    print(f"Removed {removed} duplicate power vias")


if __name__ == "__main__":
    main()
