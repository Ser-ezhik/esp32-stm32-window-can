"""Remove low-current routes before rebuilding them around fixed power copper."""

from pathlib import Path
import re

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before preparing power-first routing")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def keep_route(net_name):
    return (
        net_name == "GND"
        or net_name.startswith("FUSED_12V")
        or net_name.startswith("LOGIC_")
        or re.fullmatch(r"S[1-4]_3V3", net_name)
        or net_name.startswith("CAN")
        or "OUTA" in net_name
        or "OUTB" in net_name
    )


for item in list(board.GetTracks()):
    if not keep_route(item.GetNetname()):
        board.Delete(item)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
