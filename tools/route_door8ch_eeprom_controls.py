"""Route the EEPROM's local WP and HOLD pull-up connections."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {"EEPROM_WP", "EEPROM_HOLD"}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing EEPROM controls")

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


def add_via(net_name, x_mm, y_mm):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(net_name))
    item.SetPosition(point(x_mm, y_mm))
    item.SetWidth(pcbnew.FromMM(0.80))
    item.SetDrill(pcbnew.FromMM(0.35))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


def route(net_name, *points):
    for item in list(board.GetTracks()):
        clear_hold_route = net_name == "EEPROM_HOLD" and (
            isinstance(item, pcbnew.PCB_VIA) or item.GetLayer() == pcbnew.B_Cu
        )
        if item.GetNetname() == net_name and (item.GetLayer() == pcbnew.F_Cu or clear_hold_route):
            board.Delete(item)
    for start, end in zip(points, points[1:]):
        add_track(net_name, pcbnew.F_Cu, start, end)


route("EEPROM_WP", (79.53, 132.63), (76.00, 132.63), (76.00, 136.82), (88.00, 136.82))
route("EEPROM_HOLD", (84.47, 131.37), (82.00, 131.37))
add_via("EEPROM_HOLD", 82.00, 131.37)
add_track("EEPROM_HOLD", pcbnew.B_Cu, (82.00, 131.37), (82.00, 143.00))
add_track("EEPROM_HOLD", pcbnew.B_Cu, (82.00, 143.00), (88.00, 143.00))
add_via("EEPROM_HOLD", 88.00, 143.00)
add_track("EEPROM_HOLD", pcbnew.F_Cu, (88.00, 143.00), (88.00, 140.82))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
