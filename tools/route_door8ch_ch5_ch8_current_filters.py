"""Route the local current-sense filters and ADC divider nodes for channels 5-8."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {f"CH{channel}_CURRENT_ADC" for channel in range(5, 9)}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channels 5-8 current filters")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def pad_position(reference, pad_number):
    footprint = board.FindFootprintByReference(reference)
    pad = next(pad for pad in footprint.Pads() if pad.GetNumber() == str(pad_number))
    position = pad.GetPosition()
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def add(net_name, start, end):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(pcbnew.F_Cu)
    item.SetNet(board.FindNet(net_name))
    item.SetWidth(pcbnew.FromMM(0.25))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


for item in list(board.GetTracks()):
    if item.GetNetname() not in NETS or item.GetLayer() != pcbnew.F_Cu:
        continue
    position = item.GetPosition()
    if 145 < pcbnew.ToMM(position.x) < 247 and 66 < pcbnew.ToMM(position.y) < 84:
        board.Delete(item)

for channel in range(5, 9):
    net_name = f"CH{channel}_CURRENT_ADC"
    diode = pad_position(f"D{1000 + channel * 100 + 1}", 3)
    capacitor = pad_position(f"C{1000 + channel * 100 + 3}", 1)
    divider = pad_position(f"R{1000 + channel * 100 + 10}", 2)
    if channel == 7:
        add(net_name, diode, (212.00, 80.00))
        add(net_name, (212.00, 80.00), (212.00, 84.00))
        add(net_name, (212.00, 84.00), (205.50, 84.00))
        add(net_name, (205.50, 84.00), (205.50, 82.00))
        add(net_name, (205.50, 82.00), capacitor)
    else:
        add(net_name, diode, capacitor)
    add(net_name, divider, diode)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
