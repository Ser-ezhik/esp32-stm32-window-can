"""Resolve the final CAP_MISO/EEPROM_HOLD crossing on compact WINDOW-4CH."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))
net = board.FindNet("CAP_MISO")


def point(x, y):
    return pcbnew.VECTOR2I_MM(x, y)


def add_segment(start, end):
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(net)
    track.SetLayer(pcbnew.B_Cu)
    track.SetWidth(pcbnew.FromMM(0.20))
    track.SetStart(point(*start))
    track.SetEnd(point(*end))
    board.Add(track)


# Replace the generated transition via with the existing star via and remove the
# straight B.Cu segment that crossed the EEPROM_HOLD through-via.
for item in list(board.GetTracks()):
    if item.GetNetname() != "CAP_MISO":
        continue
    if isinstance(item, pcbnew.PCB_VIA):
        if item.GetPosition() == point(72.25, 108.25):
            board.Delete(item)
    elif item.GetLayer() == pcbnew.B_Cu:
        endpoints = {
            (item.GetStart().x, item.GetStart().y),
            (item.GetEnd().x, item.GetEnd().y),
        }
        expected = {
            (point(72.25, 108.25).x, point(72.25, 108.25).y),
            (point(97.75, 108.25).x, point(97.75, 108.25).y),
        }
        if endpoints == expected:
            board.Delete(item)

path = [
    (72.0, 108.365),
    (83.75, 108.365),
    (84.50, 107.50),
    (85.50, 107.50),
    (86.25, 108.25),
    (97.75, 108.25),
]
for start, end in zip(path, path[1:]):
    add_segment(start, end)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print("CAP_MISO now shares the star via and clears EEPROM_HOLD")
