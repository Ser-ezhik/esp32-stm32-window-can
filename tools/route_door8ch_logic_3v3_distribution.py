"""Distribute the regulated 3.3 V rail to CAN, RF and carrier EEPROM."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "LOGIC_3V3"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing 3.3 V distribution")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def track(layer, *points):
    for start, end in zip(points, points[1:]):
        item = pcbnew.PCB_TRACK(board)
        item.SetLayer(layer)
        item.SetNet(board.FindNet(NET_NAME))
        item.SetWidth(pcbnew.FromMM(0.40))
        item.SetStart(point(*start))
        item.SetEnd(point(*end))
        board.Add(item)


def via(x_mm, y_mm):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetPosition(point(x_mm, y_mm))
    item.SetWidth(pcbnew.FromMM(0.80))
    item.SetDrill(pcbnew.FromMM(0.35))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


# Delete only the distribution tracks created by this helper; the regulator
# and its local F.Cu decoupling are kept untouched.
for item in list(board.GetTracks()):
    if item.GetNetname() != NET_NAME:
        continue
    if isinstance(item, pcbnew.PCB_VIA) or item.GetLayer() == pcbnew.B_Cu:
        board.Delete(item)
    elif item.GetLayer() == pcbnew.F_Cu:
        start, end = item.GetStart(), item.GetEnd()
        xs = (pcbnew.ToMM(start.x), pcbnew.ToMM(end.x))
        ys = (pcbnew.ToMM(start.y), pcbnew.ToMM(end.y))
        touches_c238 = any(abs(x - 196.53) < 0.01 and abs(y - 91.00) < 0.01 for x, y in zip(xs, ys))
        is_local_regulator_link = touches_c238 and any(abs(x - 191.00) < 0.01 and abs(y - 91.00) < 0.01 for x, y in zip(xs, ys))
        is_stale_high_route = min(ys) < 85.0 and max(xs) >= 193.0
        if min(ys) >= 93.0 or (touches_c238 and not is_local_regulator_link) or is_stale_high_route:
            board.Delete(item)

# The long rail is on B.Cu. Two close vias move it to F.Cu only while it
# crosses the already routed ESP32 CAN control lines at x=145 and x=137.
track(pcbnew.F_Cu, (196.53, 91.00), (196.53, 94.00))
via(196.53, 94.00)
track(pcbnew.B_Cu, (196.53, 94.00), (196.53, 115.00), (150.00, 115.00))
via(150.00, 115.00)
track(pcbnew.F_Cu, (150.00, 115.00), (132.00, 115.00))
via(132.00, 115.00)
track(pcbnew.B_Cu, (132.00, 115.00), (20.00, 115.00))

# CAN headers are through-hole. EEPROM has an F.Cu pad, so it receives a
# short local layer transition after the B.Cu trunk.
track(pcbnew.B_Cu, (124.27, 115.00), (124.27, 143.70))  # CAN2
track(pcbnew.B_Cu, (64.27, 115.00), (64.27, 143.70))    # CAN1
track(pcbnew.B_Cu, (84.47, 115.00), (84.47, 126.00))
via(84.47, 126.00)
track(pcbnew.F_Cu, (84.47, 126.00), (84.47, 130.09))    # U250 pin 8
track(pcbnew.B_Cu, (20.00, 115.00), (20.00, 126.31), (25.92, 126.31))  # CC1101

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
