"""Route the relocated WINDOW-4CH reed, CAP1188 and SWD service signals."""

from pathlib import Path

import pcbnew

import route_door8ch_power_good_hold_up as router


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))


def pad_by_net(reference, net_name):
    footprint = board.FindFootprintByReference(reference)
    for pad in footprint.Pads():
        if pad.GetNetname() == net_name:
            return router.xy(pad.GetPosition())
    raise RuntimeError(f"Missing {net_name} pad on {reference}")


def net_pad(reference, net_name):
    footprint = board.FindFootprintByReference(reference)
    return next(pad for pad in footprint.Pads() if pad.GetNetname() == net_name)


def pad_copper_layer(pad):
    return pcbnew.B_Cu if pad.IsOnLayer(pcbnew.B_Cu) and not pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.F_Cu


def connect(net_name, start_reference, end_reference, width=0.20, start_layer=None, waypoints=()):
    start_pad = net_pad(start_reference, net_name)
    end_pad = net_pad(end_reference, net_name)
    if start_layer is None and start_pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
        start_layer = pad_copper_layer(start_pad)
    end_through_hole = end_pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
    end_layer = pad_copper_layer(end_pad) if not end_through_hole else pcbnew.F_Cu
    positions = [router.xy(start_pad.GetPosition()), *waypoints, router.xy(end_pad.GetPosition())]
    waypoint_layer = start_layer if start_layer is not None else pcbnew.In1_Cu
    for index, (start, end) in enumerate(zip(positions, positions[1:])):
        final_segment = index == len(positions) - 2
        router.route_multilayer(
            board, net_name, start, end, width,
            (start_layer if start_layer is not None else waypoint_layer) if index == 0 else waypoint_layer,
            end_layer if final_segment else waypoint_layer,
            end_through_hole if final_segment else False,
        )


def route_pad_pair(net_name, start_pad, end_pad, width, pth_start_layer=pcbnew.In2_Cu):
    start_layer = (pad_copper_layer(start_pad) if start_pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
                   else pth_start_layer)
    end_through_hole = end_pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
    end_layer = pad_copper_layer(end_pad) if not end_through_hole else pcbnew.F_Cu
    router.route_multilayer(
        board, net_name, router.xy(start_pad.GetPosition()), router.xy(end_pad.GetPosition()),
        width, start_layer, end_layer, end_through_hole,
    )


def route_net_star(net_name, root_reference, width):
    pads = [pad for footprint in board.GetFootprints() for pad in footprint.Pads()
            if pad.GetNetname() == net_name]
    root = next(pad for pad in pads if pad.GetParentFootprint().GetReference() == root_reference)
    for pad in pads:
        if pad is not root:
            route_pad_pair(net_name, root, pad, width)


# CAP1188 electrode paths. The field side is deliberately short and remains
# beside the edge connector; the raw side can change layers behind the module.
for channel in range(1, 5):
    raw = f"CAP_C{channel}_RAW"
    field = f"CAP_C{channel}_FIELD"
    resistor = f"R{200 + channel}"
    raw_source = pad_by_net("CAP1", raw)
    raw_target = pad_by_net(resistor, raw)
    raw_via_x = (220.0, 221.5, 223.0, 224.5)[channel - 1]
    raw_via = (raw_via_x, raw_target[1])
    raw_layer = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)[channel - 1]
    router.add_path(board, raw, raw_layer,
                    (raw_source, (239.0, raw_source[1]), (239.0, 124.0),
                     (raw_via_x, 124.0), raw_via), 0.20)
    if raw_layer != pcbnew.F_Cu:
        router.add_via(board, raw, raw_via)
    router.add_track(board, raw, pcbnew.F_Cu, raw_via, raw_target, 0.20)
    router.add_track(
        board, field, pcbnew.F_Cu,
        pad_by_net(resistor, field), pad_by_net(f"J{210 + channel}", field), 0.20,
    )

# Three reed signals for the single window.
for net_name, connector, waypoints in (
    ("REED_A_OPEN", "J201", ((125.0, 80.0), (205.0, 48.0), (220.0, 10.5))),
    ("REED_A_CLOSED", "J202", ((125.0, 74.0), (205.0, 54.0), (220.0, 22.55))),
    ("REED_A_IN_PLACE", "J203", ((125.0, 68.0), (205.0, 60.0), (220.0, 34.6))),
):
    connect(net_name, "MOD1", connector, 0.25, waypoints=waypoints)

# A local 3.3 V spine supplies the three reed connectors, then joins the held
# MASTER 3.3 V rail. It runs on In1.Cu away from electrode traces.
reed_supply_points = [pad_by_net(reference, "S1_3V3") for reference in ("J201", "J202", "J203")]
spine_x = 238.0
for supply in reed_supply_points:
    router.add_track(board, "S1_3V3", pcbnew.In2_Cu, supply, (spine_x, supply[1]), 0.30)
router.add_path(
    board, "S1_3V3", pcbnew.In2_Cu,
    ((spine_x, reed_supply_points[0][1]), (spine_x, reed_supply_points[-1][1])), 0.30,
)
router.route_multilayer(
    board, "S1_3V3", (spine_x, reed_supply_points[-1][1]),
    pad_by_net("R272", "S1_3V3"), 0.30, pcbnew.In2_Cu,
)

# SWD is a service-only interface but remains fully routed on every board.
for index, net_name in enumerate(("S1_SWDIO", "S1_SWCLK", "S1_NRST")):
    connect(net_name, "MOD1", "J220", 0.25, waypoints=((125.0, 122.0 - index * 3.0),))
connect("S1_3V3", "R272", "J220", 0.30, pcbnew.F_Cu)

# Restore the compact board's shared rails after branches for S3/S4, ESP32 and
# CAN2 have been removed. These redundant paths intentionally join at retained
# module pads rather than at deleted distribution stubs.
connect("S1_3V3", "MOD1", "R272", 0.30, pcbnew.In2_Cu,
        waypoints=((55.0, 156.0), (190.0, 156.0)))
logic5_root = net_pad("DC1", "LOGIC_5V")
logic5_junction = (140.0, 110.0)
logic5_right_junction = (165.0, 110.0)
router.add_track(board, "LOGIC_5V", pcbnew.In2_Cu,
                 router.xy(logic5_root.GetPosition()), logic5_junction, 0.50)
router.add_track(board, "LOGIC_5V", pcbnew.In2_Cu,
                 logic5_junction, logic5_right_junction, 0.50)
for footprint in board.GetFootprints():
    for pad in footprint.Pads():
        if pad.GetNetname() == "LOGIC_5V" and pad is not logic5_root:
            end_pth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            target = router.xy(pad.GetPosition())
            source = logic5_right_junction if target[0] > 150.0 else logic5_junction
            router.route_multilayer(
                board, "LOGIC_5V", source, target, 0.50,
                pcbnew.In2_Cu, pad_copper_layer(pad) if not end_pth else pcbnew.F_Cu, end_pth,
            )

logic3_root = net_pad("U230", "LOGIC_3V3")
logic3_pads = [pad for footprint in board.GetFootprints() for pad in footprint.Pads()
               if pad.GetNetname() == "LOGIC_3V3"]
for pad in logic3_pads:
    if pad is logic3_root and pad.GetPosition() == logic3_root.GetPosition():
        continue
    if pad.GetParentFootprint().GetReference() != "CAN1":
        route_pad_pair("LOGIC_3V3", logic3_root, pad, 0.30)
logic3_waypoints = ((180.0, 80.0), (120.0, 80.0))
router.route_multilayer(board, "LOGIC_3V3", router.xy(logic3_root.GetPosition()),
                        logic3_waypoints[0], 0.30, pcbnew.F_Cu, pcbnew.In1_Cu, False)
router.route_multilayer(board, "LOGIC_3V3", logic3_waypoints[0], logic3_waypoints[1],
                        0.30, pcbnew.In1_Cu, pcbnew.In1_Cu, False)
router.route_multilayer(board, "LOGIC_3V3", logic3_waypoints[1],
                        pad_by_net("CAN1", "LOGIC_3V3"), 0.30,
                        pcbnew.In1_Cu, pcbnew.F_Cu, True)

# Approach the compact CAN filter pads from the right, away from CAN_ENTRY.
canh_root = net_pad("CAN1", "CANH_BUS")
for reference, waypoint in (("R240", (154.0, 135.0)), ("L240", (160.0, 139.0))):
    target = net_pad(reference, "CANH_BUS")
    router.route_multilayer(
        board, "CANH_BUS", router.xy(canh_root.GetPosition()), waypoint, 0.30,
        pcbnew.In1_Cu, pcbnew.In1_Cu, False,
    )
    router.add_via(board, "CANH_BUS", waypoint)
    router.add_track(board, "CANH_BUS", pcbnew.F_Cu, waypoint,
                     router.xy(target.GetPosition()), 0.30)

# Stitch all four GND pours even when optional through-hole modules are absent.
for position in ((5.0, 5.0), (230.0, 5.0), (5.0, 155.0), (230.0, 150.0)):
    router.add_via(board, "GND", position, 0.80, 0.40)

gnd_layers = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
gnd_blocked = [router.grid_router.build_blocked(board, "GND", layer, 0.80)
               for layer in gnd_layers]
for y in range(10, 151, 20):
    for x in range(20, 231, 20):
        key = router.grid_router.grid_key((x, y))
        if all(key not in blocked for blocked in gnd_blocked):
            router.add_via(board, "GND", (x, y), 0.80, 0.40)

# U230 sits inside a small F.Cu ground island formed by the compact CAN and
# regulator routing. Give it a deterministic copper return to the DC/DC ground.
router.route_multilayer(
    board, "GND", pad_by_net("U230", "GND"), pad_by_net("DC1", "GND"),
    0.40, pcbnew.F_Cu, pcbnew.F_Cu, True,
)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("Routed WINDOW-4CH service I/O")
