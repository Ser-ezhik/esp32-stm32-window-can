"""Export a grouped BOM for the UNIVERSAL-2CH carrier."""

from collections import defaultdict
import csv
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "UNIVERSAL-2CH" / "kicad" / "UNIVERSAL-2CH.kicad_pcb"
OUTPUT = ROOT / "hardware" / "UNIVERSAL-2CH" / "UNIVERSAL-2CH-BOM.csv"

board = pcbnew.LoadBoard(str(BOARD))
groups = defaultdict(list)
for footprint in board.GetFootprints():
    groups[(str(footprint.GetValue()), str(footprint.GetFPID().GetLibItemName()))].append(
        footprint.GetReference()
    )

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as stream:
    writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
    writer.writerow(("Value", "References", "Footprint", "Quantity"))
    for (value, package), references in sorted(groups.items()):
        references.sort()
        writer.writerow((value, ",".join(references), package, len(references)))

print(f"Exported {len(groups)} BOM groups / {len(board.GetFootprints())} parts: {OUTPUT}")
