"""Connect each VNH fused rail to its local high-frequency decoupler."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
NETS = {f"FUSED_12V_CH{channel}" for channel in range(1, 9)}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing VNH decoupling")

board = pcbnew.LoadBoard(str(BOARD_PATH))


for item in list(board.GetTracks()):
    if item.GetNetname() in NETS and item.GetLayer() == pcbnew.F_Cu:
        start = item.GetStart()
        end = item.GetEnd()
        if 52 < pcbnew.ToMM(start.y) < 62 and 52 < pcbnew.ToMM(end.y) < 62:
            board.Delete(item)

for channel in range(1, 9):
    net_name = f"FUSED_12V_CH{channel}"
    bulk = board.FindFootprintByReference(f"C{1000 + channel * 100 + 1}")
    local = board.FindFootprintByReference(f"C{1000 + channel * 100 + 2}")
    bulk_pad = next(p for p in bulk.Pads() if p.GetNumber() == "1")
    local_pad = next(p for p in local.Pads() if p.GetNumber() == "1")
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(pcbnew.F_Cu)
    item.SetNet(board.FindNet(net_name))
    item.SetWidth(pcbnew.FromMM(1.00))
    item.SetStart(bulk_pad.GetPosition())
    item.SetEnd(local_pad.GetPosition())
    board.Add(item)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
