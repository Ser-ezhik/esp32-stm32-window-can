"""Complete the local 3.3 V network around the carrier identity EEPROM."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "LOGIC_3V3"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing EEPROM 3.3 V")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def route(*points):
    for start, end in zip(points, points[1:]):
        item = pcbnew.PCB_TRACK(board)
        item.SetLayer(pcbnew.F_Cu)
        item.SetNet(board.FindNet(NET_NAME))
        item.SetWidth(pcbnew.FromMM(0.25))
        item.SetStart(point(*start))
        item.SetEnd(point(*end))
        board.Add(item)


# Replace only the EEPROM-local F.Cu routes; the B.Cu distribution trunk and
# its nearby via are intentionally preserved.
for item in list(board.GetTracks()):
    if isinstance(item, pcbnew.PCB_VIA) or item.GetNetname() != NET_NAME or item.GetLayer() != pcbnew.F_Cu:
        continue
    start, end = item.GetStart(), item.GetEnd()
    xs = (pcbnew.ToMM(start.x), pcbnew.ToMM(end.x))
    ys = (pcbnew.ToMM(start.y), pcbnew.ToMM(end.y))
    if min(xs) >= 84.4 and max(xs) <= 90.2 and min(ys) >= 125.9 and max(ys) <= 140.0:
        board.Delete(item)

# The incoming via reaches U250 pin 8, then fans out to its decoupling and
# the CS/WP/HOLD pull-ups which share the same 3.3 V rail.
route((84.47, 126.50), (84.47, 130.09), (90.00, 130.09), (90.00, 139.18))
route((84.47, 130.09), (84.47, 128.00), (87.22, 128.00))
route((90.00, 131.18), (88.00, 131.18))
route((90.00, 135.18), (88.00, 135.18))
route((90.00, 139.18), (88.00, 139.18))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
