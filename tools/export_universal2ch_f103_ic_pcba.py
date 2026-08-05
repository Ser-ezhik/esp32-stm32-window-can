"""Export JLCPCB BOM/CPL for the direct-IC two-channel controller."""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "UNIVERSAL-2CH-F103-IC"
BOARD_PATH = PROJECT / "kicad" / "UNIVERSAL-2CH-F103-IC.kicad_pcb"
OUTPUT = PROJECT / "fabrication" / os.environ.get(
    "UNIVERSAL_2CH_RELEASE_VERSION", "v1.0-audited"
)

EXCLUDED = {"U1", "U2", "R240", "J280B"}

# Verified starting selections. JLCPCB performs a live availability check when
# the BOM is uploaded; unavailable parts are left unplaced rather than delayed.
REF_PARTS = {
    "CAP1": ("CAP1188-1-CP-TR capacitive touch controller", "C2652057"),
    "D230": ("SS54 5A 40V SMB; LGE SS54", "C432139"),
    "D231": ("SMBJ16A 600W unidirectional SMB; LGE SMBJ16A", "C713715"),
    "D240": ("ESD24VD3B bidirectional CAN ESD SOD-323", "C484324"),
    "D241": ("ESD24VD3B bidirectional CAN ESD SOD-323", "C484324"),
    "D280": ("SS34 3A 40V SMA Schottky; MDD SS34", "C8678"),
    "L240": ("ACT45B-101-2P-TL003 CAN common-mode choke", "C88056"),
    "U230": ("AMS1117-3.3 SOT-223", "C6186"),
    "U250": ("25LC256-I/SN SPI EEPROM SOIC-8", "C84670"),
    "U270": ("TLV6700DDCR dual comparator SOT-23-6", "C2868382"),
    "U300": ("STM32F103C8T6 LQFP-48", "C8734"),
    "Y300": ("X32258MOB4SI 8MHz 12pF SMD3225-4P", "C2682775"),
}


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def part_for(reference: str, value: str, footprint: str) -> tuple[str, str]:
    if reference in REF_PARTS:
        return REF_PARTS[reference]
    if reference in {"D1101", "D1201"}:
        return "BAT54S dual Schottky SOT-23; Nexperia BAT54S,215", "C47546"
    if footprint == "C_0603_1608Metric":
        if value.lower().startswith("18p"):
            return "18pF 50V C0G 0603", "C1647"
        if value.lower().startswith("10n"):
            return "10nF 50V X7R 0603", "C57112"
        return "100nF 50V X7R 0603; YAGEO CC0603KRX7R9BB104", "C14663"
    if footprint == "C_0805_2012Metric":
        return "1uF 50V X7R 0805; Samsung CL21B105KBFNNNE", "C28323"
    if footprint == "C_1206_3216Metric":
        if reference == "C231":
            return "1uF 50V X7R 1206; CCTC TCC1206X7R105M500FT", "C5448921"
        return "10uF 25V X7R 1206; YAGEO CC1206KKX7R8BB106", "C70462"
    if footprint == "R_0603_1608Metric":
        upper = value.upper()
        if upper.startswith("100R"):
            return "100R 1% 0603; UNI-ROYAL 0603WAF1000T5E", "C22775"
        if upper.startswith("1K"):
            return "1K 1% 0603; UNI-ROYAL 0603WAF1001T5E", "C21190"
        if upper.startswith("4K7"):
            return "4.7K 1% 0603; UNI-ROYAL 0603WAF4701T5E", "C23162"
        if upper.startswith("10K"):
            return "10K 1% 0603; UNI-ROYAL 0603WAF1002T5E", "C25804"
        if upper.startswith("226K"):
            return "226K 1% 0603; FH RS-03K2263FT", "C321793"
        if upper.startswith("0R"):
            return "0R 0603; UNI-ROYAL 0603WAF0000T5E", "C21189"
    raise RuntimeError(f"No JLCPCB mapping for {reference}: {value} / {footprint}")


def correction(reference: str) -> float:
    """Return bottom-side JLC library offsets verified by the pin-1 preview."""
    if reference in {"CAP1", "U250", "U300"}:
        return 90.0
    if reference in {
        "D230", "D231", "D280", "L240", "U270", "Y300",
    }:
        return 180.0
    return 0.0


board = pcbnew.LoadBoard(str(BOARD_PATH))
parts: list[dict[str, str]] = []
placements: list[dict[str, str]] = []
manual: list[dict[str, str]] = []
audit: list[dict[str, str]] = []

for fp in sorted(board.GetFootprints(), key=lambda item: item.GetReference()):
    ref = fp.GetReference()
    value = str(fp.GetValue())
    footprint = str(fp.GetFPID().GetLibItemName())
    is_smd = bool(fp.GetAttributes() & pcbnew.FP_SMD)
    excluded = ref in EXCLUDED or not is_smd
    if excluded:
        if ref in {"H1", "H2", "H3", "H4", "HS1A", "HS1B", "HS2A", "HS2B"}:
            continue
        reason = (
            "VNH5019A-E intentionally excluded."
            if ref in {"U1", "U2"}
            else "DNP CAN termination."
            if ref == "R240"
            else "Assembly wire solder pad; no component."
            if ref == "J280B"
            else "Through-hole/module part; install manually."
        )
        manual.append({
            "Reference": ref,
            "QuantityPerBoard": "1",
            "Part": value,
            "Footprint": footprint,
            "Reason": reason,
        })
        continue

    comment, lcsc = part_for(ref, value, footprint)
    parts.append({
        "Reference": ref,
        "Comment": comment,
        "Footprint": footprint,
        "LCSC Part #": lcsc,
    })
    position = fp.GetPosition()
    base = fp.GetOrientationDegrees() % 360.0
    # JLCPCB library models use package-specific zero angles. These offsets
    # are for the bottom-side preview and are not interchangeable with the
    # top-side corrections used by the larger controller board.
    fix = correction(ref)
    final = (base + fix) % 360.0
    placements.append({
        "Designator": ref,
        "Mid X": f"{pcbnew.ToMM(position.x):.6f}mm",
        "Mid Y": f"{-pcbnew.ToMM(position.y):.6f}mm",
        "Layer": "Bottom",
        "Rotation": f"{final:.1f}",
    })
    if ref in {
        "CAP1", "D1101", "D1201", "D230", "D231", "D240", "D241",
        "D280", "L240", "U230", "U250", "U270", "U300", "Y300",
    }:
        audit.append({
            "Reference": ref,
            "Footprint": footprint,
            "KiCadRotation": f"{base:.1f}",
            "JlcCorrection": f"{fix:+.1f}",
            "FinalRotation": f"{final:.1f}",
        })

groups: dict[tuple[str, str, str], list[str]] = defaultdict(list)
for part in parts:
    groups[(part["Comment"], part["Footprint"], part["LCSC Part #"])].append(part["Reference"])
bom = [
    {
        "Comment": key[0],
        "Designator": ",".join(sorted(refs)),
        "Footprint": key[1],
        "LCSC Part #": key[2],
    }
    for key, refs in sorted(groups.items())
]

write_csv(OUTPUT / "UNIVERSAL-2CH-F103-IC_BOM_JLCPCB_SMD_EXCEPT_VNH.csv",
          ("Comment", "Designator", "Footprint", "LCSC Part #"), bom)
write_csv(OUTPUT / "UNIVERSAL-2CH-F103-IC_CPL_JLCPCB_SMD_EXCEPT_VNH.csv",
          ("Designator", "Mid X", "Mid Y", "Layer", "Rotation"), placements)
write_csv(OUTPUT / "UNIVERSAL-2CH-F103-IC_MANUAL_ASSEMBLY.csv",
          ("Reference", "QuantityPerBoard", "Part", "Footprint", "Reason"), manual)
write_csv(OUTPUT / "UNIVERSAL-2CH-F103-IC_ORIENTATION_AUDIT.csv",
          ("Reference", "Footprint", "KiCadRotation", "JlcCorrection", "FinalRotation"), audit)

print(f"BOM groups: {len(bom)}")
print(f"Bottom-side SMD placements: {len(placements)}")
print(f"Manual/DNP placements: {len(manual)}")
print(OUTPUT)
