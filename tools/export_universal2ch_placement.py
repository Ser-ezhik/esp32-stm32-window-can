"""Export JLCPCB placement and grouped BOM data for UNIVERSAL-2CH."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "UNIVERSAL-2CH"
BOARD_PATH = PROJECT / "kicad" / "UNIVERSAL-2CH.kicad_pcb"
FABRICATION = PROJECT / "fabrication"
RAW_DIR = FABRICATION / "pcba-raw"

EXCLUDED_REFERENCES = {
    "CAN1",
    "CAP1",
    "DC1",
    "MOD1",
    "U1",
    "U2",
}
THROUGH_HOLE_PREFIXES = (
    "CP_Radial_",
    "TerminalBlock_",
    "DINKLE_",
    "PinHeader_",
    "Fuseholder_",
    "MountingHole_",
)


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def grouped_bom(parts: list[tuple[str, str, str]]) -> list[dict[str, str]]:
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for reference, value, package in parts:
        groups[(value, package)].append(reference)
    return [
        {
            "Comment": value,
            "Designator": ",".join(sorted(references)),
            "Footprint": package,
            "LCSC Part #": "",
        }
        for (value, package), references in sorted(groups.items())
    ]


board = pcbnew.LoadBoard(str(BOARD_PATH))
placements: list[dict[str, str]] = []
parts: list[tuple[str, str, str]] = []
manual: list[dict[str, str]] = []

for footprint in sorted(board.GetFootprints(), key=lambda item: item.GetReference()):
    if footprint.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES:
        continue

    reference = footprint.GetReference()
    value = str(footprint.GetValue())
    package = str(footprint.GetFPID().GetLibItemName())
    through_hole = package.startswith(THROUGH_HOLE_PREFIXES)
    excluded = reference in EXCLUDED_REFERENCES
    bottom = footprint.IsFlipped()
    dnp = reference == "R240"

    if excluded or through_hole or bottom or dnp:
        reason = (
            "VNH5019A-E excluded from assembly."
            if reference in {"U1", "U2"}
            else "Socketed module excluded from assembly."
            if excluded
            else "Bottom-side component excluded for top-only assembly."
            if bottom
            else "DNP CAN termination."
            if dnp
            else "Through-hole component excluded from SMD-only assembly."
        )
        manual.append(
            {
                "Reference": reference,
                "QuantityPerBoard": "1",
                "Part": value,
                "Footprint": package,
                "Reason": reason,
            }
        )
        continue

    position = footprint.GetPosition()
    rotation = footprint.GetOrientationDegrees() % 360.0
    placements.append(
        {
            "Designator": reference,
            "Mid X": f"{position.x / 1_000_000:.6f}",
            "Mid Y": f"{-position.y / 1_000_000:.6f}",
            "Layer": "Top",
            "Rotation": f"{rotation:.6f}",
        }
    )
    parts.append((reference, value, package))

write_csv(
    RAW_DIR / "UNIVERSAL-2CH_CPL_SMD_ONLY_raw.csv",
    ("Designator", "Mid X", "Mid Y", "Layer", "Rotation"),
    placements,
)
write_csv(
    RAW_DIR / "UNIVERSAL-2CH_BOM_SMD_ONLY_raw.csv",
    ("Comment", "Designator", "Footprint", "LCSC Part #"),
    grouped_bom(parts),
)
write_csv(
    RAW_DIR / "UNIVERSAL-2CH_MANUAL_ASSEMBLY_raw.csv",
    ("Reference", "QuantityPerBoard", "Part", "Footprint", "Reason"),
    manual,
)

print(f"Exported {len(placements)} top-side SMD placements")
print(f"Excluded {len(manual)} manual/DNP placements")
