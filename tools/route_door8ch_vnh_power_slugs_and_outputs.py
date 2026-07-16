"""Add VNH5019 slug via arrays and route all actuator outputs."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing VNH outputs")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def mm(position):
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def point(position):
    return pcbnew.VECTOR2I_MM(*position)


def pad_position(reference, number):
    footprint = board.FindFootprintByReference(reference)
    pad = footprint.FindPadByNumber(str(number))
    return mm(pad.GetPosition())


def add_track(net_name, layer, start, end, width):
    item = pcbnew.PCB_TRACK(board)
    item.SetNet(board.FindNet(net_name))
    item.SetLayer(layer)
    item.SetWidth(pcbnew.FromMM(width))
    item.SetStart(point(start))
    item.SetEnd(point(end))
    board.Add(item)


def add_via(net_name, position):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(net_name))
    item.SetPosition(point(position))
    item.SetWidth(pcbnew.FromMM(0.65))
    item.SetDrill(pcbnew.FromMM(0.30))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


def add_grid(net_name, layer, x_values, y_values):
    for y_mm in y_values:
        for x1, x2 in zip(x_values, x_values[1:]):
            add_track(net_name, layer, (x1, y_mm), (x2, y_mm), 0.50)
    for x_mm in x_values:
        for y1, y2 in zip(y_values, y_values[1:]):
            add_track(net_name, layer, (x_mm, y1), (x_mm, y2), 0.50)


output_nets = {
    f"CH{channel}_{suffix}"
    for channel in range(1, 9)
    for suffix in ("OUTA", "OUTB")
}

# This helper owns every actuator-output route. Supply routes are retained;
# only their new in-slug thermal vias are recreated below.
for item in list(board.GetTracks()):
    if item.GetNetname() in output_nets:
        board.Delete(item)
        continue
    if not isinstance(item, pcbnew.PCB_VIA) and item.GetNetname().startswith("FUSED_12V_CH"):
        start_x, start_y = mm(item.GetStart())
        end_x, end_y = mm(item.GetEnd())
        for channel in range(1, 9):
            slug_x, slug_y = pad_position(f"U{channel}", 31)
            inside = lambda x, y: abs(x - slug_x) <= 1.5 and abs(y - slug_y) <= 3.1
            if inside(start_x, start_y) and inside(end_x, end_y):
                board.Delete(item)
                break
        continue
    if not isinstance(item, pcbnew.PCB_VIA):
        continue
    x_mm, y_mm = mm(item.GetPosition())
    for channel in range(1, 9):
        slug_x, slug_y = pad_position(f"U{channel}", 31)
        if abs(x_mm - slug_x) <= 2.0 and abs(y_mm - slug_y) <= 4.5:
            board.Delete(item)
            break

# Channel 8 originally looped its VCC trunk beneath the output slugs. Replace
# that detour with a left-side feed so through thermal vias remain possible.
for item in list(board.GetTracks()):
    if item.GetNetname() != "FUSED_12V_CH8":
        continue
    if isinstance(item, pcbnew.PCB_VIA):
        x_mm, y_mm = mm(item.GetPosition())
        if (
            (abs(x_mm - 244.50) < 0.01 and abs(y_mm - 35.00) < 0.01)
            or (abs(x_mm - 221.00) < 0.01 and abs(y_mm - 53.00) < 0.01)
        ):
            board.Delete(item)
        continue
    start = mm(item.GetStart())
    end = mm(item.GetEnd())
    owned = {
        frozenset({(223.50, 30.00), (223.50, 39.50)}),
        frozenset({(223.50, 35.00), (229.55, 35.00)}),
        frozenset({(232.35, 35.00), (243.125, 35.00)}),
        frozenset({(221.00, 53.00), (223.50, 39.50)}),
    }
    rounded = frozenset({tuple(round(value, 3) for value in start), tuple(round(value, 3) for value in end)})
    if max(start[0], end[0]) >= 239.00 or rounded in owned:
        board.Delete(item)

add_track("FUSED_12V_CH8", pcbnew.B_Cu, (223.50, 30.00), (223.50, 39.50), 2.50)
add_track("FUSED_12V_CH8", pcbnew.B_Cu, (223.50, 35.00), (229.55, 35.00), 2.50)
add_track("FUSED_12V_CH8", pcbnew.F_Cu, (243.125, 35.00), (232.35, 35.00), 0.50)
add_track("FUSED_12V_CH8", pcbnew.B_Cu, (221.00, 53.00), (223.50, 39.50), 2.50)

for channel in range(1, 9):
    driver = f"U{channel}"
    connector = f"J{channel + 8}"
    fused = f"FUSED_12V_CH{channel}"
    out_a = f"CH{channel}_OUTA"
    out_b = f"CH{channel}_OUTB"

    slug_vcc = pad_position(driver, 31)
    slug_out_b = pad_position(driver, 32)
    slug_out_a = pad_position(driver, 33)

    vcc_x = tuple(slug_vcc[0] + value for value in (-1.40, 0.00, 1.40))
    vcc_y = tuple(slug_vcc[1] + value for value in (-3.00, -1.00, 1.00, 3.00))
    output_offsets = (-1.40, 0.00) if channel == 8 else (-1.40, 0.00, 1.40)
    out_a_x = tuple(slug_out_a[0] + value for value in output_offsets)
    out_b_x = tuple(slug_out_b[0] + value for value in output_offsets)
    out_a_y = tuple(slug_out_a[1] + value for value in (-1.40, 0.00, 1.40))
    out_b_y = tuple(slug_out_b[1] + value for value in (-1.40, 0.00, 1.40))

    for x_offset in (-1.40, 0.00, 1.40):
        for y_offset in (-3.00, -1.00, 1.00, 3.00):
            add_via(fused, (slug_vcc[0] + x_offset, slug_vcc[1] + y_offset))
    for x_offset in output_offsets:
        for y_offset in (-1.40, 0.00, 1.40):
            add_via(out_a, (slug_out_a[0] + x_offset, slug_out_a[1] + y_offset))
            add_via(out_b, (slug_out_b[0] + x_offset, slug_out_b[1] + y_offset))

    add_grid(fused, pcbnew.B_Cu, vcc_x, vcc_y)
    add_grid(out_a, pcbnew.In2_Cu if channel == 8 else pcbnew.B_Cu, out_a_x, out_a_y)
    add_grid(out_b, pcbnew.In1_Cu, out_b_x, out_b_y)

    j_out_a = pad_position(connector, 1)
    j_out_b = pad_position(connector, 2)
    out_a_entry = (out_a_x[-1], out_a_y[0])
    out_b_entry = (out_b_x[-1], out_b_y[-1])

    # OUTA descends on B.Cu; OUTB uses In1.Cu so it can cross the VCC trunk.
    out_a_layer = pcbnew.In2_Cu if channel == 8 else pcbnew.B_Cu
    add_track(out_a, out_a_layer, j_out_a, (j_out_a[0], 24.00), 2.50)
    add_track(out_a, out_a_layer, (j_out_a[0], 24.00), out_a_entry, 2.50)
    if channel == 8:
        add_track(out_b, pcbnew.In1_Cu, j_out_b, (j_out_b[0], 31.00), 2.50)
        add_track(out_b, pcbnew.In1_Cu, (j_out_b[0], 31.00), (248.00, 34.00), 2.50)
        add_track(out_b, pcbnew.In1_Cu, (248.00, 34.00), (248.00, 45.00), 2.50)
        add_track(out_b, pcbnew.In1_Cu, (248.00, 45.00), out_b_entry, 2.50)
    else:
        add_track(out_b, pcbnew.In1_Cu, j_out_b, (j_out_b[0], 45.00), 2.50)
        add_track(out_b, pcbnew.In1_Cu, (j_out_b[0], 45.00), out_b_entry, 2.50)

    # Short top-layer links join every signal lead belonging to each output.
    for pad_number, target in (
        (1, (slug_out_a[0] - 1.40, pad_position(driver, 1)[1])),
        (30, (out_a_x[-1], pad_position(driver, 30)[1])),
        (25, (out_a_x[-1], pad_position(driver, 25)[1])),
    ):
        add_track(out_a, pcbnew.F_Cu, pad_position(driver, pad_number), target, 0.80)

    for pad_number, target in (
        (15, (slug_out_b[0] - 1.40, pad_position(driver, 15)[1])),
        (16, (out_b_x[-1], pad_position(driver, 16)[1])),
        (21, (out_b_x[-1], pad_position(driver, 21)[1])),
    ):
        add_track(out_b, pcbnew.F_Cu, pad_position(driver, pad_number), target, 0.80)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
