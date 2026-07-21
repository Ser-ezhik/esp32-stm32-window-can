"""Set the YD ESP32-S3 N16R8 socket row spacing to 25.40 mm."""

from __future__ import annotations

import math
import re
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "DOOR-8CH" / "kicad" / "DOOR-8CH.kicad_pcb"
FOOTPRINT = (
    ROOT
    / "hardware"
    / "DOOR-8CH"
    / "kicad"
    / "DOOR-8CH.pretty"
    / "ESP32-S3-DevKitC.kicad_mod"
)

OLD_ROW_X = 22.86
NEW_ROW_X = 25.40
TOLERANCE_MM = 0.002


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def iu(value: float) -> int:
    return pcbnew.FromMM(value)


def close(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCE_MM


def local_to_board(footprint: pcbnew.FOOTPRINT, x: float, y: float) -> pcbnew.VECTOR2I:
    angle = math.radians(footprint.GetOrientationDegrees())
    origin = footprint.GetPosition()
    return pcbnew.VECTOR2I(
        origin.x + iu(x * math.cos(angle) + y * math.sin(angle)),
        origin.y + iu(-x * math.sin(angle) + y * math.cos(angle)),
    )


def board_to_local(footprint: pcbnew.FOOTPRINT, point: pcbnew.VECTOR2I) -> tuple[float, float]:
    angle = math.radians(footprint.GetOrientationDegrees())
    origin = footprint.GetPosition()
    dx = mm(point.x - origin.x)
    dy = mm(point.y - origin.y)
    return (
        dx * math.cos(angle) - dy * math.sin(angle),
        dx * math.sin(angle) + dy * math.cos(angle),
    )


def remap_graphic_x(x: float) -> float:
    exact = {
        2.46012: 3.73012,
        20.44332: 21.71332,
        24.11: 26.65,
        24.36: 26.90,
    }
    for old, new in exact.items():
        if close(x, old):
            return new
    return x


def update_source_footprint() -> None:
    text = FOOTPRINT.read_text(encoding="utf-8")
    original = text
    text = text.replace(
        '  (descr "ESP32-S3 general-purpose development board, based on ESP32-S3-WROOM-1 or ESP32-S3-WROOM-1U,It has all the ESP32-S3 pins exposed and is easy to connect and use.")',
        '  (descr "YD ESP32-S3 N16R8 dual-USB-C 44-pin module; 2.54 mm pitch and 25.40 mm row spacing.")',
    )
    text = text.replace('(at 11.42632 29.46128 90)', '(at 12.69632 29.46128 90)')
    text = text.replace('(at 21.59 ', '(at 24.13 ')
    text = text.replace('(start 24.36 ', '(start 26.9 ')
    text = text.replace('(start 24.359999 ', '(start 26.899999 ')
    text = text.replace('(end 24.36 ', '(end 26.9 ')
    text = text.replace('(end 24.359999 ', '(end 26.899999 ')
    text = text.replace('(start 24.11 ', '(start 26.65 ')
    text = text.replace('(end 24.11 ', '(end 26.65 ')
    text = text.replace('2.46012', '3.73012')
    text = text.replace('20.44332', '21.71332')
    text = text.replace('(size 1.2 2) (drill 0.8)', '(size 1.27 2) (drill 1)')

    def move_right_pad(match: re.Match[str]) -> str:
        return match.group(1) + "25.4" + match.group(2)

    text, moved = re.subn(
        r'(\(pad "(?:2[3-9]|3[0-9]|4[0-4])"[^\n]*?\(at )22\.86( )',
        move_right_pad,
        text,
    )
    if moved not in (0, 22):
        raise RuntimeError(f"Expected 22 right-row source pads, changed {moved}")
    if text == original:
        print("Source footprint already uses 25.40 mm spacing")
        return
    FOOTPRINT.write_text(text, encoding="utf-8", newline="\n")
    print(f"Updated source footprint: {FOOTPRINT}")


def update_board() -> None:
    board = pcbnew.LoadBoard(str(BOARD))
    footprint = board.FindFootprintByReference("ESP1")
    if footprint is None:
        raise RuntimeError("ESP1 footprint not found")

    right_pads = [footprint.FindPadByNumber(str(number)) for number in range(23, 45)]
    current_x = mm(right_pads[0].GetFPRelativePosition().x)
    if not (close(current_x, OLD_ROW_X) or close(current_x, NEW_ROW_X)):
        raise RuntimeError(f"Unexpected ESP1 row spacing: {current_x:.3f} mm")

    endpoint_moves: dict[tuple[int, int], pcbnew.VECTOR2I] = {}
    moved_pads = 0
    for pad in footprint.Pads():
        pad.SetDrillSize(pcbnew.VECTOR2I(iu(1.0), iu(1.0)))
        pad.SetSize(pcbnew.VECTOR2I(iu(1.27), iu(2.0)))
        number = int(pad.GetNumber())
        if number < 23:
            continue
        relative = pad.GetFPRelativePosition()
        old_position = pad.GetPosition()
        relative.x = iu(NEW_ROW_X)
        pad.SetFPRelativePosition(relative)
        new_position = pad.GetPosition()
        endpoint_moves[(old_position.x, old_position.y)] = new_position
        if old_position != new_position:
            moved_pads += 1

    moved_endpoints = 0
    for track in board.GetTracks():
        if not isinstance(track, pcbnew.PCB_TRACK):
            continue
        start = track.GetStart()
        end = track.GetEnd()
        new_start = endpoint_moves.get((start.x, start.y))
        new_end = endpoint_moves.get((end.x, end.y))
        if new_start is not None:
            track.SetStart(new_start)
            moved_endpoints += 1
        if new_end is not None:
            track.SetEnd(new_end)
            moved_endpoints += 1

    moved_texts = 0
    moved_shapes = 0
    for item in footprint.GraphicalItems():
        if isinstance(item, pcbnew.PCB_TEXT):
            position = item.GetFPRelativePosition()
            x = mm(position.x)
            if close(x, 21.59):
                position.x = iu(24.13)
                item.SetFPRelativePosition(position)
                moved_texts += 1
            continue
        if not isinstance(item, pcbnew.PCB_SHAPE):
            continue
        old_start = item.GetStart()
        old_end = item.GetEnd()
        sx, sy = board_to_local(footprint, old_start)
        ex, ey = board_to_local(footprint, old_end)
        nsx = remap_graphic_x(sx)
        nex = remap_graphic_x(ex)
        if not close(nsx, sx) or not close(nex, ex):
            item.SetStart(local_to_board(footprint, nsx, sy))
            item.SetEnd(local_to_board(footprint, nex, ey))
            moved_shapes += 1

    footprint.SetLibDescription(
        "YD ESP32-S3 N16R8 dual-USB-C 44-pin module; "
        "2.54 mm pitch and 25.40 mm row spacing."
    )
    board.BuildConnectivity()
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)
    print(
        f"Updated board: pads={moved_pads}, track endpoints={moved_endpoints}, "
        f"texts={moved_texts}, shapes={moved_shapes}"
    )


if __name__ == "__main__":
    update_source_footprint()
    update_board()
