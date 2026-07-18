"""Derive the two-STM32 WINDOW-4CH board from the routed DOOR-8CH v1.41 PCB."""

from __future__ import annotations

import re
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "WINDOW-4CH" / "kicad"
BOARD_PATH = PROJECT / "WINDOW-4CH.kicad_pcb"
LOCK_PATH = PROJECT / "~WINDOW-4CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close WINDOW-4CH in KiCad before deriving the board")

board = pcbnew.LoadBoard(str(BOARD_PATH))

KEEP_REFERENCES = {"MOD1", "MOD2", "CAN1", "CAP1"}
REMOVE_REFERENCES = {
    "MOD3", "MOD4", "ESP1", "RF1", "CAN2",
    "J204", "J205", "J206",
    "J215", "J216", "J217", "J218",
    "R205", "R206", "R207", "R208",
    "HS5A", "HS5B", "HS6A", "HS6B", "HS7A", "HS7B", "HS8A", "HS8B",
}

REMOVE_NET = re.compile(
    r"(^CH[5-8]_)|(^FUSED_12V_CH[5-8]$)|(^S[34]_)|UART[23]|"
    r"(^ESP_)|(^RF_)|(^CAN2_)|(^REED_B_)|(^CAP_C[5-8]_(RAW|FIELD)$)"
)


def footprint_nets(footprint):
    return {pad.GetNetname() for pad in footprint.Pads() if pad.GetNetname()}


remove_footprints = []
for footprint in board.GetFootprints():
    reference = footprint.GetReference()
    selected = reference in REMOVE_REFERENCES or any(REMOVE_NET.search(net) for net in footprint_nets(footprint))
    if selected and reference not in KEEP_REFERENCES:
        remove_footprints.append(footprint)

# Delete complete copper for private nets that disappear from WINDOW-4CH.
for item in list(board.GetTracks()):
    if REMOVE_NET.search(item.GetNetname()):
        board.Delete(item)

for footprint in remove_footprints:
    board.Delete(footprint)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Removed {len(remove_footprints)} footprints; WINDOW-4CH keeps {len(board.GetFootprints())}")
