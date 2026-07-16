"""Connect the channel 1 and 2 current scalers to their ADC divider inputs."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {"CH1_CURRENT_ADC", "CH2_CURRENT_ADC"}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing ADC divider inputs")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


for item in list(board.GetTracks()):
    if item.GetNetname() not in NETS or item.GetLayer() != pcbnew.F_Cu:
        continue
    start = item.GetStart()
    end = item.GetEnd()
    dx = abs(pcbnew.ToMM(start.x) - pcbnew.ToMM(end.x))
    dy = abs(pcbnew.ToMM(start.y) - pcbnew.ToMM(end.y))
    if dx < 1.5 and dy > 3:
        board.Delete(item)


def add(net_name, start, end):
    track = pcbnew.PCB_TRACK(board)
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(board.FindNet(net_name))
    track.SetWidth(pcbnew.FromMM(0.25))
    track.SetStart(point(*start))
    track.SetEnd(point(*end))
    board.Add(track)


add("CH1_CURRENT_ADC", (29.94, 72.00), (30.83, 68.00))
add("CH2_CURRENT_ADC", (59.94, 72.00), (60.83, 68.00))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
