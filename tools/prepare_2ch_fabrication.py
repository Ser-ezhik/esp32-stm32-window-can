"""Relocate conflicting silk labels and remove narrow pour features."""
import json
import sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
report = json.load(open(sys.argv[2], encoding="utf-8"))
bad = {i["uuid"] for v in report["violations"]
       if v["type"].startswith("silk_") for i in v["items"]}
silks = (pcbnew.F_SilkS, pcbnew.B_SilkS)
items = list(board.GetDrawings())
for fp in board.GetFootprints():
    items.extend(fp.GraphicalItems())
    items.extend([fp.Reference(), fp.Value()])
texts = [i for i in items if isinstance(i, pcbnew.PCB_TEXT)
         and i.GetLayer() in silks and i.IsVisible()]
moving = [i for i in texts if i.m_Uuid.AsString() in bad]

def box(item, margin=0.0):
    b = item.GetBoundingBox()
    m = pcbnew.FromMM(margin)
    return b.GetLeft()-m, b.GetTop()-m, b.GetRight()+m, b.GetBottom()+m

def overlaps(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]

edge = board.GetBoardEdgesBoundingBox()
limits = (edge.GetLeft()+pcbnew.FromMM(.6), edge.GetTop()+pcbnew.FromMM(.6),
          edge.GetRight()-pcbnew.FromMM(.6), edge.GetBottom()-pcbnew.FromMM(.6))
obstacles = {l: [] for l in silks}
moving_ids = {i.m_Uuid.AsString() for i in moving}
for i in items:
    if i.GetLayer() not in silks or i.m_Uuid.AsString() in moving_ids:
        continue
    if isinstance(i, pcbnew.PCB_TEXT) and not i.IsVisible():
        continue
    # Outline rectangles/circles are outlines, not solid text obstacles.
    if isinstance(i, pcbnew.PCB_SHAPE) and i.GetShape() == pcbnew.SHAPE_T_RECT:
        l, t, r, b = box(i, .2)
        w = pcbnew.FromMM(.4)
        obstacles[i.GetLayer()].extend([(l,t,r,t+w),(l,b-w,r,b),(l,t,l+w,b),(r-w,t,r,b)])
        continue
    obstacles[i.GetLayer()].append(box(i, .15))
for fp in board.GetFootprints():
    for pad in fp.Pads():
        for silk, mask in ((pcbnew.F_SilkS, pcbnew.F_Mask), (pcbnew.B_SilkS, pcbnew.B_Mask)):
            if pad.IsOnLayer(mask):
                obstacles[silk].append(box(pad, .3))

offsets = sorted(((x*.25, y*.25) for x in range(-40,41) for y in range(-40,41)),
                 key=lambda p: p[0]*p[0]+p[1]*p[1])
for text in moving:
    origin = text.GetPosition()
    for dx, dy in offsets:
        text.SetPosition(pcbnew.VECTOR2I(origin.x+pcbnew.FromMM(dx), origin.y+pcbnew.FromMM(dy)))
        b = box(text, .1)
        if b[0] < limits[0] or b[1] < limits[1] or b[2] > limits[2] or b[3] > limits[3]:
            continue
        if not any(overlaps(b, o) for o in obstacles[text.GetLayer()]):
            obstacles[text.GetLayer()].append(b)
            break
    else:
        raise RuntimeError("No space for " + text.GetText())
    print(text.GetText(), pcbnew.ToMM(text.GetPosition().x), pcbnew.ToMM(text.GetPosition().y))

for zone in board.Zones():
    if not zone.GetIsRuleArea():
        zone.SetMinThickness(pcbnew.FromMM(.8))
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(sys.argv[3], board)
