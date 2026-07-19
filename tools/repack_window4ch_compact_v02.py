"""Repack WINDOW-4CH into its compact 155 x 150 mm service layout."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "WINDOW-4CH" / "kicad"
BOARD_PATH = PROJECT / "WINDOW-4CH.kicad_pcb"
LOCK_PATH = PROJECT / "~WINDOW-4CH.kicad_pcb.lck"
WIDTH = 155.0
HEIGHT = 150.0

if LOCK_PATH.exists():
    raise SystemExit("Close WINDOW-4CH in KiCad before repacking the board")


def pt(x, y):
    return pcbnew.VECTOR2I_MM(x, y)


board = pcbnew.LoadBoard(str(BOARD_PATH))

# The complete high-current channel block above y=75 mm remains untouched.
# Only the low-voltage service area is repacked.
placements = {
    # Right-edge field wiring.
    "J201": (149.7, 9.0, 90),
    "J202": (149.7, 21.05, 90),
    "J203": (149.7, 33.10, 90),
    "J211": (149.7, 119.0, 90),
    "J212": (149.7, 127.5, 90),
    "J213": (149.7, 136.0, 90),
    "J214": (149.7, 144.5, 90),
    "R201": (141.0, 119.0, 270),
    "R202": (141.0, 127.5, 270),
    "R203": (141.0, 136.0, 270),
    "R204": (141.0, 144.5, 270),
    "CAP1": (124.5, 74.5, 0),
    "R209": (119.0, 78.0, 90),
    "R210": (119.0, 84.0, 90),

    # Protected 12 V input and low-voltage conversion.
    "F230": (15.0, 82.0, 0),
    "D230": (30.0, 91.0, 0),
    "D231": (39.0, 91.0, 0),
    "C231": (47.0, 91.0, 0),
    "C232": (52.0, 91.0, 0),
    "C230": (49.0, 103.0, 0),
    "DC1": (58.0, 79.0, 0),
    "C234": (84.0, 82.0, 0),
    "C235": (90.0, 82.0, 0),
    "C233": (87.0, 94.0, 0),
    "C237": (97.0, 80.0, 0),
    "C236": (97.0, 85.0, 0),
    "U230": (106.0, 82.0, 0),
    "C239": (114.0, 80.0, 0),
    "C238": (114.0, 85.0, 0),

    # Power-fail monitor and local control passives.
    "R270": (106.0, 94.0, 270),
    "C271": (109.0, 96.0, 270),
    "R271": (106.0, 97.0, 270),
    "R272": (96.0, 99.0, 90),
    "U270": (101.0, 99.0, 0),
    "C270": (104.0, 99.0, 270),
    "R250": (73.0, 104.0, 0),
    "R251": (77.0, 104.0, 0),
    "U250": (81.0, 109.0, 0),
    "C250": (87.0, 105.0, 0),
    "R260": (87.0, 109.0, 90),
    "R261": (91.0, 109.0, 90),
    "R262": (95.0, 109.0, 90),
    "R3011": (43.0, 109.0, 0),
    "R3012": (47.0, 109.0, 0),
    "R3021": (56.0, 109.0, 0),
    "R3022": (60.0, 109.0, 0),

    # Bottom service row; both STM32 USB sockets face the board edge.
    "MOD1": (31.2, 144.9, 180),
    "MOD2": (65.2, 144.9, 180),
    "CAN1": (72.5, 132.0, 0),
    "J240": (98.0, 144.0, 0),
    "R240": (92.0, 125.0, 0),
    "D240": (92.0, 132.0, 90),
    "L240": (99.0, 128.0, 0),
    "D241": (106.0, 132.0, 90),
    "C280": (115.0, 135.0, 90),
    "D280": (115.0, 146.0, 270),
    "J220": (121.0, 109.0, 0),

    # Four mechanical mounting points outside heatsink keep-outs.
    "H1": (5.0, 76.0, 0),
    "H2": (145.0, 48.0, 0),
    "H3": (5.0, 112.0, 0),
    "H4": (132.0, 145.0, 0),
}

for reference, (x, y, angle) in placements.items():
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        raise RuntimeError(f"Missing footprint {reference}")
    footprint.SetPosition(pt(x, y))
    footprint.SetOrientationDegrees(angle)

# Retain completed high-current copper and short local VNH control chains.
retained = {
    "CH1_OUTA", "CH1_OUTB", "CH2_OUTA", "CH2_OUTB",
    "CH3_OUTA", "CH3_OUTB", "CH4_OUTA", "CH4_OUTB",
    "FUSED_12V_CH1", "FUSED_12V_CH2", "FUSED_12V_CH3", "FUSED_12V_CH4",
}
for channel in range(1, 5):
    retained.update({
        f"CH{channel}_INA", f"CH{channel}_INB", f"CH{channel}_PWM",
        f"CH{channel}_CS_DIS", f"CH{channel}_CS_RAW",
    })

for item in list(board.GetTracks()):
    if item.GetNetname() not in retained:
        board.Delete(item)

for zone in list(board.Zones()):
    board.Delete(zone)

for drawing in list(board.GetDrawings()):
    if drawing.GetLayer() == pcbnew.Edge_Cuts:
        board.Delete(drawing)

outline = pcbnew.PCB_SHAPE(board)
outline.SetShape(pcbnew.SHAPE_T_RECT)
outline.SetLayer(pcbnew.Edge_Cuts)
outline.SetStart(pt(0, 0))
outline.SetEnd(pt(WIDTH, HEIGHT))
outline.SetWidth(pcbnew.FromMM(0.05))
board.Add(outline)

gnd = board.FindNet("GND")
for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
    zone = pcbnew.ZONE(board)
    zone.SetNet(gnd)
    zone.SetLayer(layer)
    zone.SetLocalClearance(pcbnew.FromMM(0.30))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    polygon = zone.Outline()
    polygon.NewOutline()
    for x, y in ((0.5, 0.5), (WIDTH - 0.5, 0.5),
                 (WIDTH - 0.5, HEIGHT - 0.5), (0.5, HEIGHT - 0.5)):
        polygon.Append(pt(x, y))
    board.Add(zone)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Repacked WINDOW-4CH to {WIDTH:.0f} x {HEIGHT:.0f} mm")
