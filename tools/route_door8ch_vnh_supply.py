"""Route each independent fused 12 V feed from its terminal to its VNH5019."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing VNH supply feeds")

board = pcbnew.LoadBoard(str(BOARD_PATH))

# The helper owns the individual fused input feeds. Re-running it replaces
# these routes but leaves motor outputs and all low-voltage routing intact.
for item in list(board.GetTracks()):
    if item.GetNetname().startswith("FUSED_12V_CH"):
        board.Delete(item)


def get_net(name):
    item = board.FindNet(name)
    if item is None:
        raise RuntimeError(f"Missing net {name}")
    return item


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def track(net_name, layer, width_mm, start, end):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(layer)
    item.SetNet(get_net(net_name))
    item.SetWidth(pcbnew.FromMM(width_mm))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


def via(net_name, x_mm, y_mm):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(get_net(net_name))
    item.SetPosition(point(x_mm, y_mm))
    item.SetWidth(pcbnew.FromMM(1.20))
    item.SetDrill(pcbnew.FromMM(0.60))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


centres = (24, 54, 84, 114, 146, 176, 206, 236)
for channel, center_x in enumerate(centres, start=1):
    net_name = f"FUSED_12V_CH{channel}"
    connector = board.FindFootprintByReference(f"J{channel}")
    capacitor = board.FindFootprintByReference(f"C{1000 + channel * 100 + 1}")
    driver = board.FindFootprintByReference(f"U{channel}")
    if connector is None or capacitor is None or driver is None:
        raise RuntimeError(f"Missing footprint in channel {channel}")

    terminal = next(p for p in connector.Pads() if p.GetNumber() == "1").GetPosition()
    positive = next(p for p in capacitor.Pads() if p.GetNumber() == "1").GetPosition()
    top_power = next(p for p in driver.Pads() if p.GetNumber() == "3").GetPosition()
    lower_power = [
        next(p for p in driver.Pads() if p.GetNumber() == number).GetPosition()
        for number in ("12", "13")
    ]
    right_power = next(p for p in driver.Pads() if p.GetNumber() == "23").GetPosition()

    terminal_xy = (pcbnew.ToMM(terminal.x), pcbnew.ToMM(terminal.y))
    positive_xy = (pcbnew.ToMM(positive.x), pcbnew.ToMM(positive.y))
    left_x = center_x - 12.5
    right_x = 244.5 if channel == 8 else center_x + 12.0

    # The B.Cu rail is the 5 A path. The short F.Cu stubs fan out into the
    # four VNH supply pins, avoiding a thin single-pin bottleneck.
    track(net_name, pcbnew.B_Cu, 2.5, terminal_xy, (left_x, terminal_xy[1]))
    if channel == 8:
        # Keep the high-current feed away from U8's left-side signal escape.
        # The x=240 trunk feeds the bulk capacitor and both left-side power vias.
        track(net_name, pcbnew.B_Cu, 2.5, (left_x, terminal_xy[1]), (left_x, 30.0))
        track(net_name, pcbnew.B_Cu, 2.5, (left_x, 15.0), (240.0, 15.0))
        track(net_name, pcbnew.B_Cu, 2.5, (240.0, 15.0), (240.0, positive_xy[1]))
        track(net_name, pcbnew.B_Cu, 2.5, (240.0, positive_xy[1]), positive_xy)
        track(net_name, pcbnew.B_Cu, 2.5, (240.0, 39.5), (left_x, 39.5))
    else:
        track(net_name, pcbnew.B_Cu, 2.5, (left_x, terminal_xy[1]), positive_xy)
        track(net_name, pcbnew.B_Cu, 2.5, positive_xy, (left_x, 30.0))
    rail_start_x = 240.0 if channel == 8 else left_x
    track(net_name, pcbnew.B_Cu, 2.5, (rail_start_x, 35.0), (right_x, 35.0))

    for x_mm, y_mm in ((left_x, 30.0), (left_x, 39.5), (right_x, 35.0)):
        via(net_name, x_mm, y_mm)

    track(net_name, pcbnew.F_Cu, 0.50, (left_x, 30.0), (pcbnew.ToMM(top_power.x), pcbnew.ToMM(top_power.y)))
    for pad in lower_power:
        track(net_name, pcbnew.F_Cu, 0.50, (left_x, 39.5), (pcbnew.ToMM(pad.x), pcbnew.ToMM(pad.y)))
    track(net_name, pcbnew.F_Cu, 0.50, (right_x, 35.0), (pcbnew.ToMM(right_power.x), pcbnew.ToMM(right_power.y)))

pcbnew.SaveBoard(str(BOARD_PATH), board)
