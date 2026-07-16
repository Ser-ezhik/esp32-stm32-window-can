"""Assign the three electrical exposed slugs of every VNH5019A-E."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before assigning VNH slugs")

board = pcbnew.LoadBoard(str(BOARD_PATH))

for channel in range(1, 9):
    footprint = board.FindFootprintByReference(f"U{channel}")
    if footprint is None:
        raise RuntimeError(f"Missing U{channel}")

    assignments = {
        "31": f"FUSED_12V_CH{channel}",  # Heat Slug1 / VCC
        "33": f"CH{channel}_OUTA",       # Heat Slug2 / OUTA
        "32": f"CH{channel}_OUTB",       # Heat Slug3 / OUTB
    }
    for pad_number, net_name in assignments.items():
        pad = footprint.FindPadByNumber(pad_number)
        net = board.FindNet(net_name)
        if pad is None or net is None:
            raise RuntimeError(f"Missing U{channel}.{pad_number} or {net_name}")
        pad.SetNet(net)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
