"""Isolate existing DOOR-8CH nets before adding the power-fail hardware."""

from __future__ import annotations

import os
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = Path(os.environ.get(
    "BOARD_PATH", ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
))


def ensure_net(board, name):
    net = board.FindNet(name)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
    return net


def xy(position):
    return round(pcbnew.ToMM(position.x), 4), round(pcbnew.ToMM(position.y), 4)


def main():
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    power_good = ensure_net(board, "POWER_GOOD")
    ensure_net(board, "PGOOD_SENSE")
    s1_hold = ensure_net(board, "S1_5V_HOLD")
    s1_3v3 = ensure_net(board, "S1_3V3")

    changes = {
        "MOD1": {"21": s1_hold, "30": power_good},
        "U250": {"8": s1_3v3},
        "C250": {"1": s1_3v3},
        "R260": {"2": s1_3v3},
        "R261": {"2": s1_3v3},
        "R262": {"2": s1_3v3},
    }
    for reference, assignments in changes.items():
        footprint = board.FindFootprintByReference(reference)
        for pad in footprint.Pads():
            if pad.GetNumber() in assignments:
                pad.SetNet(assignments[pad.GetNumber()])

    remove = []
    for track in board.GetTracks():
        if isinstance(track, pcbnew.PCB_VIA):
            if track.GetNetname() == "LOGIC_3V3" and xy(track.GetPosition()) == (84.47, 126.5):
                remove.append(track)
            continue
        start, end = xy(track.GetStart()), xy(track.GetEnd())
        if track.GetNetname() == "LOGIC_5V" and {start, end} == {(37.38, 153.0), (37.38, 158.0)}:
            remove.append(track)
        elif track.GetNetname() == "LOGIC_3V3":
            if {start, end} in (
                {(84.47, 115.0), (84.47, 126.5)},
                {(84.47, 126.5), (84.47, 127.3975)},
            ):
                remove.append(track)
            elif min(start[0], end[0]) >= 84.0 and max(start[0], end[0]) <= 90.0 and min(start[1], end[1]) >= 127.35:
                track.SetNet(s1_3v3)

    for item in remove:
        board.RemoveNative(item)

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Prepared power-fail nets; removed {len(remove)} old copper items")


if __name__ == "__main__":
    main()
