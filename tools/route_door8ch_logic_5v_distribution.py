"""Distribute the protected 5 V rail to ESP32 and all STM32 slots."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NET_NAME = "LOGIC_5V"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing 5 V distribution")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def add_track(layer, start, end, width=0.80):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(layer)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetWidth(pcbnew.FromMM(width))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


def add_via(position):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(NET_NAME))
    item.SetPosition(point(*position))
    item.SetWidth(pcbnew.FromMM(1.20))
    item.SetDrill(pcbnew.FromMM(0.60))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


for item in list(board.GetTracks()):
    if item.GetNetname() != NET_NAME:
        continue
    if isinstance(item, pcbnew.PCB_VIA) or item.GetLayer() != pcbnew.F_Cu:
        board.Delete(item)
        continue
    start = item.GetStart()
    end = item.GetEnd()
    endpoints = {
        (round(pcbnew.ToMM(start.x), 2), round(pcbnew.ToMM(start.y), 2)),
        (round(pcbnew.ToMM(end.x), 2), round(pcbnew.ToMM(end.y), 2)),
    }
    if any(y_mm > 101.00 for _, y_mm in endpoints):
        board.Delete(item)

# Leave the local DC-DC route on F.Cu and pass the complete CAN/protection
# area on In2.Cu. Return to F.Cu only at the lower distribution trunk.
add_track(pcbnew.F_Cu, (145.00, 100.50), (160.00, 105.00), 0.60)
add_via((160.00, 105.00))
add_track(pcbnew.In2_Cu, (160.00, 105.00), (160.00, 135.00))
add_track(pcbnew.In2_Cu, (160.00, 135.00), (172.00, 147.00))
add_track(pcbnew.In2_Cu, (172.00, 147.00), (172.00, 158.00))
add_via((172.00, 158.00))

slot_x = (37.38, 97.38, 177.38, 217.38)
add_track(pcbnew.F_Cu, (20.00, 158.00), (slot_x[-1], 158.00))
for x_mm in slot_x:
    add_track(pcbnew.F_Cu, (x_mm, 158.00), (x_mm, 153.00))

# ESP32 pad 21 is left of the CANL trunk, so it can cross the 3.3 V B.Cu rail
# directly on In2.Cu before joining the same lower trunk.
esp_x = 58.7973
add_track(pcbnew.In1_Cu, (esp_x, 105.0037), (esp_x, 110.00))
add_track(pcbnew.In1_Cu, (esp_x, 110.00), (20.00, 110.00))
add_track(pcbnew.In1_Cu, (20.00, 110.00), (20.00, 158.00))
add_via((20.00, 158.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
