"""Create the two internal GND planes for the four-layer DOOR-8CH PCB."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before adding GND planes")

board = pcbnew.LoadBoard(str(BOARD_PATH))
gnd = board.FindNet("GND")
if gnd is None:
    raise RuntimeError("Missing GND net")


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


# This helper owns full-board internal GND zones, so it may safely be rerun.
for zone in list(board.Zones()):
    if zone.GetNetname() == "GND" and zone.GetLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        board.Delete(zone)

for layer in (pcbnew.In1_Cu, pcbnew.In2_Cu):
    zone = pcbnew.ZONE(board)
    zone.SetNet(gnd)
    zone.SetLayer(layer)
    zone.SetLocalClearance(pcbnew.FromMM(0.30))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zone.SetIsFilled(True)
    outline = zone.Outline()
    outline.NewOutline()
    for x_mm, y_mm in ((0.50, 0.50), (259.50, 0.50), (259.50, 159.50), (0.50, 159.50)):
        outline.Append(point(x_mm, y_mm))
    board.Add(zone)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
