"""Improve dense reference placement without moving any copper or footprints."""

from __future__ import annotations

import re
import sys

import pcbnew


def set_text_style(text: pcbnew.PCB_TEXT, size_mm: float = 0.8) -> None:
    text.SetTextSize(pcbnew.VECTOR2I_MM(size_mm, size_mm))
    text.SetTextThickness(pcbnew.FromMM(0.10))


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: polish_universal4ch_silkscreen.py INPUT OUTPUT")

    board = pcbnew.LoadBoard(sys.argv[1])

    # Keep connector references below the housings and pin legends above them.
    for ref in ("J201", "J202", "J203"):
        footprint = board.FindFootprintByReference(ref)
        reference = footprint.Reference()
        x_mm = pcbnew.ToMM(footprint.GetPosition().x) + 3.5
        reference.SetPosition(pcbnew.VECTOR2I_MM(x_mm, 91.0))
        set_text_style(reference, 0.8)

    for drawing in board.GetDrawings():
        if not isinstance(drawing, pcbnew.PCB_TEXT):
            continue
        if drawing.GetText() == "5V SIG GND":
            position = drawing.GetPosition()
            drawing.SetPosition(pcbnew.VECTOR2I(position.x, pcbnew.FromMM(81.8)))

    # The four VNH channels use identical passive placement. Put each reference
    # in a predictable row next to its component instead of stacking all names.
    for channel in range(11, 15):
        for footprint in board.GetFootprints():
            ref = footprint.GetReference()
            if not re.fullmatch(rf"[RCD]{channel}\d{{2}}", ref):
                continue
            reference = footprint.Reference()
            set_text_style(reference)
            position = footprint.GetPosition()
            x_mm = pcbnew.ToMM(position.x)
            y_mm = pcbnew.ToMM(position.y)
            if ref.startswith("R") and 37.0 <= y_mm <= 38.0:
                y_mm = 39.0
            elif ref.startswith("R") and 41.5 <= y_mm <= 42.5:
                y_mm = 43.5
            elif y_mm <= 35.5:
                y_mm -= 1.2
            elif y_mm >= 49.0:
                y_mm = 44.8
            elif y_mm >= 45.5:
                y_mm += 1.3
            reference.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))

    # Make the remaining bottom-side references consistent and legible.
    for footprint in board.GetFootprints():
        if footprint.GetLayer() == pcbnew.B_Cu:
            set_text_style(footprint.Reference(), 0.8)

    jumper_note = "C280+ -> J280B"
    if not any(
        isinstance(drawing, pcbnew.PCB_TEXT) and drawing.GetText() == jumper_note
        for drawing in board.GetDrawings()
    ):
        note = pcbnew.PCB_TEXT(board)
        note.SetText(jumper_note)
        note.SetLayer(pcbnew.B_SilkS)
        note.SetMirrored(True)
        note.SetTextAngle(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
        note.SetPosition(pcbnew.VECTOR2I_MM(81.0, 82.0))
        set_text_style(note, 0.8)
        board.Add(note)

    pcbnew.SaveBoard(sys.argv[2], board)


if __name__ == "__main__":
    main()
