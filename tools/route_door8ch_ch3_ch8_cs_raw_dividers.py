"""Connect the local raw-current divider resistor pairs for channels 3-8."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {f"CH{channel}_CS_RAW" for channel in range(3, 9)}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channels 3-8 raw-current dividers")

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
    if 80 < pcbnew.ToMM(position.x) < 245 and 67 < pcbnew.ToMM(position.y) < 71:
        board.Delete(item)

for channel in range(3, 9):
    net_name = f"CH{channel}_CS_RAW"
    left = pad_position(f"R{1000 + channel * 100 + 9}", 1)
    right = pad_position(f"R{1000 + channel * 100 + 10}", 1)
    add(net_name, left, (left[0], 69.00))
    add(net_name, (left[0], 69.00), (right[0], 69.00))
    add(net_name, (right[0], 69.00), right)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
