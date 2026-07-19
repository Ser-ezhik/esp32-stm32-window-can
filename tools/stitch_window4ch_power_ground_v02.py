"""Add clearance-checked GND stitching vias to the compact power section."""

from pathlib import Path

import pcbnew

import route_door8ch_final_gaps as grid
import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))
layers = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

# The regular grid point at (80, 8) nearly coincides with J3.2 at (80.04, 8).
for item in list(board.GetTracks()):
    if (isinstance(item, pcbnew.PCB_VIA) and item.GetNetname() == "GND" and
            item.GetPosition() == pcbnew.VECTOR2I_MM(80, 8)):
        board.Delete(item)

grid.GRID = 0.25
grid.CLEARANCE = 0.35
grid.PAD_EXTRA = 0.25
diameter = 0.65
blocked = {
    layer: grid.build_blocked(board, "GND", layer, diameter)
    for layer in layers
}

added = []
for y in (8, 16, 24, 32, 40, 48, 56, 64, 72):
    for x in range(8, 149, 8):
        if (x, y) == (80, 8):
            continue
        key = grid.grid_key((x, y))
        if any(key in blocked[layer] for layer in layers):
            continue
        router.add_via(board, "GND", (x, y), diameter=diameter, drill=0.30)
        added.append((x, y))

# The remaining F.Cu islands are narrow corridors around the driver block and
# do not intersect the regular 8 mm grid. Give every such island one stitch.
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
front_zone = next(
    zone for zone in board.Zones()
    if zone.GetNetname() == "GND" and zone.GetLayer() == pcbnew.F_Cu
)
polygons = front_zone.GetFilledPolysList(pcbnew.F_Cu)
gnd_vias = [
    item for item in board.GetTracks()
    if isinstance(item, pcbnew.PCB_VIA) and item.GetNetname() == "GND"
]

for index in range(polygons.OutlineCount()):
    outline = polygons.Outline(index)
    bbox = outline.BBox()
    if pcbnew.ToMM(bbox.GetY()) > 75:
        continue
    if any(outline.PointInside(via.GetPosition()) for via in gnd_vias):
        continue
    x0 = pcbnew.ToMM(bbox.GetX())
    y0 = pcbnew.ToMM(bbox.GetY())
    x1 = x0 + pcbnew.ToMM(bbox.GetWidth())
    y1 = y0 + pcbnew.ToMM(bbox.GetHeight())
    candidate = None
    y = round((y0 + 0.25) / 0.25) * 0.25
    while y <= y1 - 0.25 and candidate is None:
        x = round((x0 + 0.25) / 0.25) * 0.25
        while x <= x1 - 0.25:
            position = pcbnew.VECTOR2I_MM(x, y)
            key = grid.grid_key((x, y))
            if (outline.PointInside(position) and
                    all(key not in blocked[layer] for layer in layers)):
                candidate = (x, y)
                break
            x += 0.25
        y += 0.25
    if candidate is None:
        raise RuntimeError(f"No safe stitch point in F.Cu GND island {index}")
    router.add_via(board, "GND", candidate, diameter=diameter, drill=0.30)
    gnd_vias.append(next(
        item for item in reversed(list(board.GetTracks()))
        if isinstance(item, pcbnew.PCB_VIA) and item.GetPosition() == pcbnew.VECTOR2I_MM(*candidate)
    ))
    added.append(candidate)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Added {len(added)} clearance-checked power-section GND vias")
