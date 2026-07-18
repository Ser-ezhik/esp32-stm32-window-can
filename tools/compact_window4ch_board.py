"""Crop WINDOW-4CH to 240 x 160 mm without disturbing validated power blocks."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "WINDOW-4CH" / "kicad"
BOARD_PATH = PROJECT / "WINDOW-4CH.kicad_pcb"
LOCK_PATH = PROJECT / "~WINDOW-4CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close WINDOW-4CH in KiCad before compacting the board")

board = pcbnew.LoadBoard(str(BOARD_PATH))
SHIFT_MM = 20.0
BOARD_WIDTH_MM = 240.0
BOARD_HEIGHT_MM = 160.0
REROUTED_NETS = {
    "REED_A_OPEN", "REED_A_CLOSED", "REED_A_IN_PLACE",
    "CAP_C1_FIELD", "CAP_C2_FIELD", "CAP_C3_FIELD", "CAP_C4_FIELD",
    "CAP_C1_RAW", "CAP_C2_RAW", "CAP_C3_RAW", "CAP_C4_RAW",
    "S1_SWDIO", "S1_SWCLK", "S1_NRST",
    "LOGIC_3V3", "LOGIC_5V", "CANH_BUS",
}


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def shift_left(position):
    return pcbnew.VECTOR2I(position.x - pcbnew.FromMM(SHIFT_MM), position.y)


for reference in ("J201", "J202", "J203"):
    board.FindFootprintByReference(reference).SetPosition(
        shift_left(board.FindFootprintByReference(reference).GetPosition())
    )

for reference, y_mm in zip(("J211", "J212", "J213", "J214"), (129.0, 137.5, 146.0, 154.5)):
    board.FindFootprintByReference(reference).SetPosition(point(234.7, y_mm))

for reference, y_mm in zip(("R201", "R202", "R203", "R204"), (129.0, 137.5, 146.0, 154.5)):
    footprint = board.FindFootprintByReference(reference)
    footprint.SetPosition(point(226.0, y_mm))
    footprint.SetOrientationDegrees(270)

board.FindFootprintByReference("J220").SetPosition(point(210.0, 128.0))
board.FindFootprintByReference("H4").SetPosition(point(212.0, 152.0))

# The relocated service nets are intentionally rerouted from clean pads.
for item in list(board.GetTracks()):
    if item.GetNetname() in REROUTED_NETS:
        board.Delete(item)
        continue
    if isinstance(item, pcbnew.PCB_VIA):
        outside = item.GetPosition().x > pcbnew.FromMM(239.5)
    else:
        outside = item.GetStart().x > pcbnew.FromMM(239.5) or item.GetEnd().x > pcbnew.FromMM(239.5)
    if outside:
        board.Delete(item)

for zone in list(board.Zones()):
    board.Delete(zone)

gnd = board.FindNet("GND")
for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
    zone = pcbnew.ZONE(board)
    zone.SetNet(gnd)
    zone.SetLayer(layer)
    zone.SetLocalClearance(pcbnew.FromMM(0.30))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    outline = zone.Outline()
    outline.NewOutline()
    for x_mm, y_mm in ((0.5, 0.5), (239.5, 0.5), (239.5, 159.5), (0.5, 159.5)):
        outline.Append(point(x_mm, y_mm))
    board.Add(zone)

for drawing in list(board.GetDrawings()):
    if drawing.GetLayer() == pcbnew.Edge_Cuts:
        board.Delete(drawing)

outline = pcbnew.PCB_SHAPE(board)
outline.SetShape(pcbnew.SHAPE_T_RECT)
outline.SetLayer(pcbnew.Edge_Cuts)
outline.SetStart(point(0.0, 0.0))
outline.SetEnd(point(BOARD_WIDTH_MM, BOARD_HEIGHT_MM))
outline.SetWidth(pcbnew.FromMM(0.05))
board.Add(outline)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Compacted WINDOW-4CH to 240 x 160 mm")
