"""Route filtered channel 7 and 8 current measurements to STM32 slot S4."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {"CH7_CURRENT_ADC", "CH8_CURRENT_ADC"}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing CH7/CH8 ADC inputs")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


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
    if item.GetNetname() not in NETS:
        continue
    if isinstance(item, pcbnew.PCB_VIA) or item.GetLayer() != pcbnew.F_Cu:
        board.Delete(item)
        continue
    position = item.GetPosition()
    if pcbnew.ToMM(position.y) > 85:
        board.Delete(item)

routes = (
    ("CH7_CURRENT_ADC", pcbnew.In1_Cu, (212.825, 68.00), (212.00, 70.00), 124.00, (232.62, 130.14)),
    ("CH8_CURRENT_ADC", pcbnew.In2_Cu, (242.825, 68.00), (244.00, 70.00), 126.00, (235.16, 130.14)),
)

for net_name, layer, source, entry, approach_y, target in routes:
    add_track(net_name, pcbnew.F_Cu, source, entry)
    add_via(net_name, entry)
    add_track(net_name, layer, entry, (entry[0], approach_y))
    add_track(net_name, layer, (entry[0], approach_y), (target[0], approach_y))
    add_via(net_name, (target[0], approach_y))
    add_track(net_name, pcbnew.F_Cu, (target[0], approach_y), target)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
