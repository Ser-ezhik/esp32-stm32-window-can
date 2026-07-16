"""Verify that generated DOOR-8CH schematics still mirror the routed PCB."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "tools" / "_vendor" / "kiutils_runtime"
sys.path.insert(0, str(VENDOR))

import pcbnew
from kiutils.schematic import Schematic


PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD = PROJECT / "DOOR-8CH.kicad_pcb"
FLAT = PROJECT / "DOOR-8CH.kicad_sch"


def main():
    board = pcbnew.LoadBoard(str(BOARD))
    schematic = Schematic.from_file(str(FLAT), encoding="utf-8")

    board_references = Counter(fp.GetReference() for fp in board.GetFootprints())
    schematic_references = Counter(
        next(prop.value for prop in symbol.properties if prop.key == "Reference")
        for symbol in schematic.schematicSymbols
    )
    logical_pads = []
    for footprint in board.GetFootprints():
        pads = {}
        for pad in footprint.Pads():
            if pad.GetNumber():
                pads[pad.GetNumber()] = pad.GetNetname()
        logical_pads.extend(pads.items())
    board_nets = Counter(net for _, net in logical_pads if net)
    schematic_nets = Counter(label.text for label in schematic.globalLabels)
    blank_pads = sum(1 for _, net in logical_pads if not net)

    failures = []
    if board_references != schematic_references:
        failures.append("component reference multiset differs")
    if board_nets != schematic_nets:
        failures.append("pad/net label multiset differs")
    if blank_pads != len(schematic.noConnects):
        failures.append(f"blank pad count {blank_pads} != no-connect count {len(schematic.noConnects)}")
    if failures:
        raise SystemExit("FAILED: " + "; ".join(failures))

    print(f"OK: {sum(board_references.values())} component references")
    print(f"OK: {sum(board_nets.values())} connected pads/net labels")
    print(f"OK: {blank_pads} blank pads/no-connect markers")


if __name__ == "__main__":
    main()
