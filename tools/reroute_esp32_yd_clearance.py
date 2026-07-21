"""Clear copper and H1 from the widened 25.40 mm ESP32 socket row."""

from __future__ import annotations

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"


def point(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def key(value: pcbnew.VECTOR2I) -> tuple[int, int]:
    return value.x, value.y


def edge(a: tuple[float, float], b: tuple[float, float]) -> frozenset[tuple[int, int]]:
    return frozenset((key(point(*a)), key(point(*b))))


def replace_route(
    board: pcbnew.BOARD,
    net_name: str,
    layer: int,
    old_edges: list[tuple[tuple[float, float], tuple[float, float]]],
    new_points: list[tuple[float, float]],
) -> None:
    wanted = {edge(a, b) for a, b in old_edges}
    removed: list[pcbnew.PCB_TRACK] = []
    for track in board.GetTracks():
        if not isinstance(track, pcbnew.PCB_TRACK):
            continue
        if track.GetNetname() != net_name or track.GetLayer() != layer:
            continue
        if frozenset((key(track.GetStart()), key(track.GetEnd()))) in wanted:
            removed.append(track)
    if len(removed) != len(wanted):
        raise RuntimeError(
            f"{net_name}: expected {len(wanted)} old segments, found {len(removed)}"
        )
    width = removed[0].GetWidth()
    net_code = removed[0].GetNetCode()
    for track in removed:
        board.Remove(track)
    for start, end in zip(new_points, new_points[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(point(*start))
        track.SetEnd(point(*end))
        track.SetWidth(width)
        track.SetLayer(layer)
        track.SetNetCode(net_code)
        board.Add(track)
    print(f"{net_name}: replaced {len(removed)} segments with {len(new_points) - 1}")


board = pcbnew.LoadBoard(str(BOARD))

replace_route(
    board,
    "ESP_CAN_RX_GPIO38",
    pcbnew.B_Cu,
    [((30.86, 79.6), (35.0, 78.0))],
    [(30.86, 79.6), (30.86, 78.0), (35.0, 78.0)],
)
replace_route(
    board,
    "REED_A_IN_PLACE",
    pcbnew.In1_Cu,
    [
        ((62.0, 52.5), (62.0, 80.5)),
        ((62.0, 80.5), (63.0, 81.5)),
    ],
    [(62.0, 52.5), (64.0, 77.5), (64.0, 81.5), (63.0, 81.5)],
)
replace_route(
    board,
    "REED_A_OPEN",
    pcbnew.In2_Cu,
    [
        ((51.5, 75.0), (57.0, 80.5)),
        ((57.0, 80.5), (62.0, 80.5)),
        ((62.0, 80.5), (63.0, 81.5)),
    ],
    [(51.5, 75.0), (64.0, 77.5), (64.0, 81.5), (63.0, 81.5)],
)
replace_route(
    board,
    "REED_B_IN_PLACE",
    pcbnew.In2_Cu,
    [
        ((29.5, 60.5), (9.5, 80.5)),
        ((9.5, 80.5), (7.0, 80.5)),
        ((7.0, 80.5), (6.0, 81.5)),
    ],
    [(29.5, 60.5), (5.5, 77.5), (5.5, 81.5), (6.0, 81.5)],
)

h1 = board.FindFootprintByReference("H1")
if h1 is None:
    raise RuntimeError("H1 not found")
h1.SetPosition(point(8.0, 73.5))

board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD), board)
print("Moved H1 to (8.0, 73.5) mm")
