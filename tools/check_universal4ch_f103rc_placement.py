"""Mechanical placement checks for UNIVERSAL-4CH-F103RC-IC.

The board is intentionally unrouted. This checker verifies placement-specific
constraints that KiCad's connectivity DRC cannot distinguish from unfinished
routing.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = (
    ROOT
    / "hardware"
    / "UNIVERSAL-4CH-F103RC-IC"
    / "kicad"
    / "UNIVERSAL-4CH-F103RC-IC.kicad_pcb"
)
BOARD_WIDTH = 136.0
BOARD_HEIGHT = 105.0
EDGE_MARGIN = 0.0
MIN_OVERLAP = 0.20
PAD_TO_SMD_CLEARANCE = 0.20


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def bbox_mm(item) -> tuple[float, float, float, float]:
    try:
        box = item.GetBoundingBox(False, False)
    except TypeError:
        box = item.GetBoundingBox()
    return mm(box.GetX()), mm(box.GetY()), mm(box.GetRight()), mm(box.GetBottom())


def intersection(a, b) -> tuple[float, float]:
    return min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])


def expanded(box, margin: float):
    return box[0] - margin, box[1] - margin, box[2] + margin, box[3] + margin


board = pcbnew.LoadBoard(str(BOARD_PATH))
footprints = list(board.GetFootprints())
errors: list[str] = []

# Bodies and silkscreen must remain inside the manufactured board outline.
for fp in footprints:
    box = bbox_mm(fp)
    if (
        box[0] < EDGE_MARGIN
        or box[1] < EDGE_MARGIN
        or box[2] > BOARD_WIDTH - EDGE_MARGIN
        or box[3] > BOARD_HEIGHT - EDGE_MARGIN
    ):
        errors.append(f"OUTSIDE {fp.GetReference()}: {box}")

# Same-side bodies may not overlap. Tiny bounding-box contacts are tolerated
# because some library courtyard/silkscreen extents deliberately touch.
for first, second in combinations(footprints, 2):
    if first.IsFlipped() != second.IsFlipped():
        continue
    width, height = intersection(bbox_mm(first), bbox_mm(second))
    if width > MIN_OVERLAP and height > MIN_OVERLAP:
        errors.append(
            f"OVERLAP {'BOTTOM' if first.IsFlipped() else 'TOP'} "
            f"{first.GetReference()} {second.GetReference()}: {width:.2f} x {height:.2f} mm"
        )

# Through-hole copper/drills must not emerge through a bottom-side SMD body.
bottom_smd = []
for fp in footprints:
    if not fp.IsFlipped():
        continue
    pads = list(fp.Pads())
    if pads and all(pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for pad in pads):
        bottom_smd.append(fp)

for tht_fp in footprints:
    for pad in tht_fp.Pads():
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
            continue
        pad_box = expanded(bbox_mm(pad), PAD_TO_SMD_CLEARANCE)
        for smd_fp in bottom_smd:
            if smd_fp.GetReference() == tht_fp.GetReference():
                continue
            width, height = intersection(pad_box, bbox_mm(smd_fp))
            if width > 0 and height > 0:
                errors.append(
                    f"THT_VS_SMD {tht_fp.GetReference()}.{pad.GetNumber()} "
                    f"hits {smd_fp.GetReference()}"
                )

print(f"Board: {BOARD_WIDTH:.1f} x {BOARD_HEIGHT:.1f} mm")
print(f"Footprints: {len(footprints)}")
print(f"Placement errors: {len(errors)}")
for error in errors:
    print(error)

raise SystemExit(1 if errors else 0)
