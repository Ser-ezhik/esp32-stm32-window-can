"""Remove power vias that KiCad reports as connected on only one layer."""

from __future__ import annotations

import re
import sys

import pcbnew


POWER_PATTERN = re.compile(r"(?:FUSED_12V_CH[1-4]|CH[1-4]_OUT[AB])$")


def position_key(position: pcbnew.VECTOR2I) -> tuple[int, int]:
    return round(pcbnew.ToMM(position.x) * 10_000), round(pcbnew.ToMM(position.y) * 10_000)


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: remove_reported_dangling_power_vias.py INPUT DRC_REPORT OUTPUT")

    board = pcbnew.LoadBoard(sys.argv[1])
    report = open(sys.argv[2], encoding="utf-8", errors="replace").read()
    reported = {
        (round(float(x) * 10_000), round(float(y) * 10_000), net)
        for x, y, net in re.findall(
            r"\[via_dangling\].*?@\(([-\d.]+) mm,\s*([-\d.]+) mm\): Via \[([^]]+)\]",
            report,
            flags=re.DOTALL,
        )
        if POWER_PATTERN.fullmatch(net)
    }

    removed = 0
    for item in list(board.GetTracks()):
        if not isinstance(item, pcbnew.PCB_VIA):
            continue
        x, y = position_key(item.GetPosition())
        if (x, y, item.GetNetname()) in reported:
            board.Delete(item)
            removed += 1

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[3], board)
    print(f"Removed {removed} reported dangling power vias")


if __name__ == "__main__":
    main()
