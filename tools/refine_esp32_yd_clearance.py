"""Refine the ESP32 row detours around existing inner-layer trunks."""

from __future__ import annotations

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"


def p(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def k(value: pcbnew.VECTOR2I) -> tuple[int, int]:
    return value.x, value.y


def replace(
    board: pcbnew.BOARD,
    tracks: list[pcbnew.BOARD_ITEM],
    net: str,
    layer: int,
    old_points: list[tuple[float, float]],
    new_points: list[tuple[float, float]],
) -> None:
    wanted = {
        frozenset((k(p(*start)), k(p(*end))))
        for start, end in zip(old_points, old_points[1:])
    }
    found: list[pcbnew.PCB_TRACK] = []
    for track in tracks:
        if not isinstance(track, pcbnew.PCB_TRACK):
            continue
        candidate = frozenset((k(track.GetStart()), k(track.GetEnd())))
        if track.GetNetname() == net and track.GetLayer() == layer and candidate in wanted:
            found.append(track)
    if len(found) != len(wanted):
        raise RuntimeError(f"{net}: expected {len(wanted)} segments, found {len(found)}")
    width = found[0].GetWidth()
    net_code = found[0].GetNetCode()
    for track in found:
        board.Remove(track)
    for start, end in zip(new_points, new_points[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(p(*start))
        track.SetEnd(p(*end))
        track.SetWidth(width)
        track.SetLayer(layer)
        track.SetNetCode(net_code)
        board.Add(track)
    print(f"{net}: refined to {len(new_points) - 1} segments")


board = pcbnew.LoadBoard(str(BOARD))
tracks = list(board.GetTracks())

replace(
    board,
    tracks,
    "REED_A_IN_PLACE",
    pcbnew.In1_Cu,
    [(62.0, 52.5), (64.0, 77.5), (64.0, 81.5), (63.0, 81.5)],
    [(62.0, 52.5), (63.0, 77.8), (63.0, 81.5)],
)
replace(
    board,
    tracks,
    "REED_A_OPEN",
    pcbnew.In2_Cu,
    [(51.5, 75.0), (64.0, 77.5), (64.0, 81.5), (63.0, 81.5)],
    [(51.5, 75.0), (51.5, 77.5), (63.0, 77.8), (63.0, 81.5)],
)
replace(
    board,
    tracks,
    "REED_B_IN_PLACE",
    pcbnew.In2_Cu,
    [(29.5, 60.5), (5.5, 77.5), (5.5, 81.5), (6.0, 81.5)],
    [
        (29.5, 60.5),
        (20.0, 69.0),
        (20.0, 77.5),
        (5.5, 77.5),
        (5.5, 81.5),
        (6.0, 81.5),
    ],
)

h1 = board.FindFootprintByReference("H1")
if h1 is None:
    raise RuntimeError("H1 not found")
h1.SetPosition(p(76.0, 90.0))

board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD), board)
print("Moved H1 to (76.0, 90.0) mm")
