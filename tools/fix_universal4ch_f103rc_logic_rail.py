"""Merge the orphan CH3/CH4 3.3 V branch into the powered S1_3V3 rail."""

from __future__ import annotations

import sys
from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as router


ROOT = Path(__file__).resolve().parents[1]
BOARD = (
    ROOT
    / "hardware"
    / "UNIVERSAL-4CH-F103RC-IC"
    / "kicad"
    / "UNIVERSAL-4CH-F103RC-IC.kicad_pcb"
)
BRIDGE_START = (72.641, 42.986)
BRIDGE_END = (54.033, 46.213)


def main() -> None:
    board_path = Path(sys.argv[1]) if len(sys.argv) > 1 else BOARD
    board = pcbnew.LoadBoard(str(board_path))
    powered_net = board.FindNet("S1_3V3")
    if not powered_net:
        raise RuntimeError("S1_3V3 is missing")

    pads = [
        pad
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
        if pad.GetNetname() == "S2_3V3"
    ]
    tracks = [item for item in board.GetTracks() if item.GetNetname() == "S2_3V3"]
    if len(pads) != 4 or not tracks:
        raise RuntimeError(
            f"unexpected S2_3V3 topology: {len(pads)} pads, {len(tracks)} tracks"
        )

    for pad in pads:
        pad.SetNet(powered_net)
    for item in tracks:
        item.SetNet(powered_net)
    for zone in board.Zones():
        if zone.GetNetname() == "S2_3V3":
            zone.SetNet(powered_net)

    router.GRID = 0.25
    router.CLEARANCE = 0.25
    router.PAD_EXTRA = 0.15
    router.EDGE = 0.75
    path = router.find_path(
        board, "S1_3V3", pcbnew.F_Cu, BRIDGE_START, BRIDGE_END, 0.20
    )
    for first, second in zip(path, path[1:]):
        router.add_track(board, "S1_3V3", pcbnew.F_Cu, first, second, 0.20)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(board_path), board)
    print(f"Merged S2_3V3 into S1_3V3 and added {len(path) - 1} bridge segments")


if __name__ == "__main__":
    main()
