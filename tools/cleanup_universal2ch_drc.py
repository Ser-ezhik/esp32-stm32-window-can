from pathlib import Path
import math

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "hardware" / "UNIVERSAL-2CH" / "kicad" / "UNIVERSAL-2CH.kicad_pcb"


def mm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


board = pcbnew.LoadBoard(str(PCB))

# The 4-channel source contained four coincident front GND zones. Keeping all
# of them creates five false "zone to zone" unconnected reports after refill.
gnd_front = [
    zone for zone in board.Zones()
    if zone.GetNetname() == "GND" and zone.GetLayer() == pcbnew.F_Cu
]
for zone in gnd_front[1:]:
    board.Remove(zone)

# Edge connectors keep their reference designators on the assembly side, while
# the body outlines live on F.Fab. This avoids printing clipped ink at the PCB
# edge and still leaves an unambiguous assembly drawing.
for ref in ("J201", "J202", "J203", "J211", "J212", "J213", "J240"):
    fp = board.FindFootprintByReference(ref)
    for item in fp.GraphicalItems():
        if item.GetLayer() == pcbnew.F_SilkS:
            item.SetLayer(pcbnew.F_Fab)

reference_positions = {
    "H1": (5.0, 10.0),
    "H2": (99.0, 54.0),
    "H4": (99.0, 101.0),
    "R262": (38.0, 88.0),
    "R272": (70.0, 88.5),
    "C280": (53.0, 93.0),
    "F230": (70.0, 20.0),
    "R210": (53.0, 77.0),
    "R1206": (64.0, 60.0),
}
for ref, point in reference_positions.items():
    board.FindFootprintByReference(ref).Reference().SetPosition(mm(*point))

for drawing in board.GetDrawings():
    if not isinstance(drawing, pcbnew.PCB_TEXT):
        continue
    if drawing.GetText() == "2x VNH5019 / STM32 / CAN / CAP1188":
        drawing.SetLayer(pcbnew.F_Fab)
    elif drawing.GetText() == "UNIVERSAL-2CH":
        drawing.SetPosition(mm(39.0, 20.0))
        drawing.SetTextHeight(pcbnew.FromMM(1.0))
        drawing.SetTextWidth(pcbnew.FromMM(1.0))

# Edge mounting-hole outlines are documented on fabrication instead of being
# clipped in the production silkscreen.
for ref in ("H2", "H4"):
    fp = board.FindFootprintByReference(ref)
    for item in fp.GraphicalItems():
        if item.GetLayer() == pcbnew.F_SilkS:
            item.SetLayer(pcbnew.F_Fab)

# Stitch the four GND pours together. Without these vias the routed signal
# channels divide the front pour into several pad-connected regions which DRC
# correctly reports as separate parts of the same net.
layers = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
grid.GRID = 0.50
grid.CLEARANCE = 0.32
grid.PAD_EXTRA = grid.GRID
grid.EDGE = 1.00
blocked = [grid.build_blocked(board, "GND", layer, 0.85) for layer in layers]
existing_vias = {
    (round(pcbnew.ToMM(item.GetPosition().x), 3),
     round(pcbnew.ToMM(item.GetPosition().y), 3))
    for item in board.GetTracks()
    if isinstance(item, pcbnew.PCB_VIA)
}

# Remove an obsolete automatically selected stitch which is too close to the
# STM32 socket drill. A clean build will no longer recreate it.
for item in list(board.GetTracks()):
    if (
        isinstance(item, pcbnew.PCB_VIA)
        and item.GetNetname() == "GND"
        and abs(pcbnew.ToMM(item.GetPosition().x) - 2.1505) < 0.01
        and abs(pcbnew.ToMM(item.GetPosition().y) - 129.3643) < 0.01
    ):
        board.Delete(item)

drilled_items = []
for footprint in board.GetFootprints():
    for pad in footprint.Pads():
        drill = max(
            pcbnew.ToMM(pad.GetDrillSize().x),
            pcbnew.ToMM(pad.GetDrillSize().y),
        )
        if drill > 0:
            drilled_items.append((pad.GetPosition(), drill))
for item in board.GetTracks():
    if isinstance(item, pcbnew.PCB_VIA):
        drilled_items.append((item.GetPosition(), pcbnew.ToMM(item.GetDrillValue())))


def hole_clear(point, drill=0.40):
    px = pcbnew.ToMM(point.x)
    py = pcbnew.ToMM(point.y)
    for center, other_drill in drilled_items:
        distance = math.hypot(
            px - pcbnew.ToMM(center.x),
            py - pcbnew.ToMM(center.y),
        )
        if distance < (drill + other_drill) / 2 + 0.25:
            return False
    return True
stitches = 0
for y in range(6, 110, 8):
    for x in range(6, 104, 8):
        point = (float(x), float(y))
        if point in existing_vias:
            continue
        key = grid.grid_key(point)
        if all(key not in layer_blocked for layer_blocked in blocked):
            router.add_via(board, "GND", point, 0.80, 0.40)
            stitches += 1

# The coarse grid point at (62, 78) is too close to C280's drilled lead.
for item in list(board.GetTracks()):
    if (
        isinstance(item, pcbnew.PCB_VIA)
        and item.GetNetname() == "GND"
        and item.GetPosition() == mm(62.0, 78.0)
    ):
        board.Delete(item)
        stitches -= 1

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())

# The dense controller fan-out can leave narrow pour regions between traces.
# Give every filled region its own through stitch at a point where another GND
# layer also exists, including regions too narrow for the coarse stitch grid.
zones_by_layer = {zone.GetLayer(): zone for zone in board.Zones()}
for _ in range(2):
    added = 0
    current_vias = [
        item for item in board.GetTracks()
        if isinstance(item, pcbnew.PCB_VIA) and item.GetNetname() == "GND"
    ]
    blocked = [grid.build_blocked(board, "GND", layer, 0.85) for layer in layers]
    for layer, zone in zones_by_layer.items():
        filled = zone.GetFilledPolysList(layer)
        for index in range(filled.OutlineCount()):
            contour = filled.COutline(index)
            if any(contour.PointInside(via.GetPosition()) for via in current_vias):
                continue
            box = contour.BBox()
            left = pcbnew.ToMM(box.GetX())
            top = pcbnew.ToMM(box.GetY())
            right = left + pcbnew.ToMM(box.GetWidth())
            bottom = top + pcbnew.ToMM(box.GetHeight())
            candidate = None
            y = top + 0.75
            while y < bottom - 0.50 and candidate is None:
                x = left + 0.75
                while x < right - 0.50:
                    point = mm(x, y)
                    filled_layers = sum(
                        other.HitTestFilledArea(other_layer, point)
                        for other_layer, other in zones_by_layer.items()
                    )
                    key = grid.grid_key((x, y))
                    if (
                        contour.PointInside(point)
                        and zone.HitTestFilledArea(layer, point)
                        and filled_layers >= 2
                        and all(key not in layer_blocked for layer_blocked in blocked)
                        and hole_clear(point)
                    ):
                        candidate = (x, y)
                        break
                    x += 0.50
                y += 0.50
            if candidate is not None:
                router.add_via(board, "GND", candidate, 0.80, 0.40)
                stitches += 1
                added += 1
    if not added:
        break
    filler.Fill(board.Zones())

# A narrow front-copper strip between the two current-sense channels is too
# small for the coarse stitch grid but has a verified 0.60/0.30 mm location.
final_stitch = (29.175, 63.9912)
if not any(
    isinstance(item, pcbnew.PCB_VIA)
    and item.GetNetname() == "GND"
    and item.GetPosition() == mm(*final_stitch)
    for item in board.GetTracks()
):
    router.add_via(board, "GND", final_stitch, 0.60, 0.30)
    stitches += 1
    filler.Fill(board.Zones())

pcbnew.SaveBoard(str(PCB), board)
print(
    f"Cleaned {len(gnd_front) - 1} duplicate GND zones, front silkscreen, "
    f"and added {stitches} GND stitches"
)
