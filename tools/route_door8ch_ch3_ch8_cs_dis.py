"""Route the channel 3-7 VNH current-sense disable straps locally."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {f"CH{channel}_CS_DIS" for channel in range(3, 9)}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channels 3-8 CS_DIS")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def pad_position(reference, pad_number):
    footprint = board.FindFootprintByReference(reference)
    pad = next(pad for pad in footprint.Pads() if pad.GetNumber() == str(pad_number))
    position = pad.GetPosition()
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def add_track(net_name, layer, start, end):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(layer)
    item.SetNet(board.FindNet(net_name))
    item.SetWidth(pcbnew.FromMM(0.25))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


def add_via(net_name, position):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(net_name))
    item.SetPosition(point(*position))
    item.SetWidth(pcbnew.FromMM(0.80))
    item.SetDrill(pcbnew.FromMM(0.35))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


for item in list(board.GetTracks()):
    if item.GetNetname() in NETS:
        board.Delete(item)

for channel in (3, 4, 6, 7):
    net_name = f"CH{channel}_CS_DIS"
    source = pad_position(f"U{channel}", 6)
    target = pad_position(f"R{1000 + channel * 100 + 8}", 1)
    entry = (source[0] - 0.875, source[1])
    approach_y = 67.00
    exit_point = (target[0] - 0.175, approach_y)
    add_track(net_name, pcbnew.F_Cu, source, entry)
    add_via(net_name, entry)
    add_track(net_name, pcbnew.In1_Cu, entry, (entry[0], approach_y))
    add_track(net_name, pcbnew.In1_Cu, (entry[0], approach_y), exit_point)
    add_via(net_name, exit_point)
    add_track(net_name, pcbnew.F_Cu, exit_point, target)

# Channel 5 exits above the resistor row, then uses the narrow gap between
# the PWM and INA input resistors before approaching R1508 from the right.
net_name = "CH5_CS_DIS"
source = pad_position("U5", 6)
target = pad_position("R1508", 1)
entry = (136.00, 33.00)
exit_point = (144.00, 60.00)
add_track(net_name, pcbnew.F_Cu, source, entry)
add_via(net_name, entry)
add_track(net_name, pcbnew.In1_Cu, entry, (136.00, 60.00))
add_track(net_name, pcbnew.In1_Cu, (136.00, 60.00), exit_point)
add_via(net_name, exit_point)
add_track(net_name, pcbnew.F_Cu, exit_point, (144.00, 66.00))
add_track(net_name, pcbnew.F_Cu, (144.00, 66.00), target)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
