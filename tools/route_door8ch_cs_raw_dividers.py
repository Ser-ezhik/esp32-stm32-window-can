"""Connect the local raw-current divider resistor pairs for channels 1 and 2."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {"CH1_CS_RAW", "CH2_CS_RAW"}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing current divider links")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


for item in list(board.GetTracks()):
    if item.GetNetname() not in NETS or item.GetLayer() != pcbnew.F_Cu:
        continue
    start = item.GetStart()
    end = item.GetEnd()
    if 20 < min(pcbnew.ToMM(start.x), pcbnew.ToMM(end.x)) and max(pcbnew.ToMM(start.x), pcbnew.ToMM(end.x)) < 65 and 67 < min(pcbnew.ToMM(start.y), pcbnew.ToMM(end.y)) < 71:
        board.Delete(item)


def route(net_name, left, right):
    for start, end in zip(
        (left, (left[0], 69.00), (right[0], 69.00)),
        ((left[0], 69.00), (right[0], 69.00), right),
    ):
        track = pcbnew.PCB_TRACK(board)
        track.SetLayer(pcbnew.F_Cu)
        track.SetNet(board.FindNet(net_name))
        track.SetWidth(pcbnew.FromMM(0.25))
        track.SetStart(point(*start))
        track.SetEnd(point(*end))
        board.Add(track)


route("CH1_CS_RAW", (25.18, 68.00), (29.18, 68.00))
route("CH2_CS_RAW", (55.18, 68.00), (59.18, 68.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
