"""Restore validated local VNH DIAG copper from WINDOW-4CH v0.1."""

import subprocess
import tempfile
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
GIT_OBJECT = "e350838:hardware/WINDOW-4CH/kicad/WINDOW-4CH.kicad_pcb"
DIAG_NETS = {f"CH{channel}_DIAG" for channel in range(1, 5)}


def mm(position):
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


board = pcbnew.LoadBoard(str(BOARD_PATH))

# Remove only the failed channel-2 escape test at x=43 mm.
test_points = [pcbnew.VECTOR2I_MM(43.0, y) for y in (32.0, 36.0, 68.0)]
for item in list(board.GetTracks()):
    if item.GetNetname() != "CH2_DIAG":
        continue
    if isinstance(item, pcbnew.PCB_VIA):
        remove = any(item.GetPosition() == point for point in test_points)
    else:
        remove = any(item.GetStart() == point or item.GetEnd() == point for point in test_points)
    if remove:
        board.Delete(item)

payload = subprocess.check_output(["git", "show", GIT_OBJECT], cwd=ROOT)
with tempfile.NamedTemporaryFile(suffix=".kicad_pcb", delete=False) as handle:
    handle.write(payload)
    history_path = Path(handle.name)

try:
    history = pcbnew.LoadBoard(str(history_path))
    restored = 0
    for old in history.GetTracks():
        if old.GetNetname() not in DIAG_NETS:
            continue
        if isinstance(old, pcbnew.PCB_VIA):
            if mm(old.GetPosition())[1] >= 75.0:
                continue
            item = pcbnew.PCB_VIA(board)
            item.SetNet(board.FindNet(old.GetNetname()))
            item.SetPosition(old.GetPosition())
            item.SetWidth(old.GetWidth(old.TopLayer()))
            item.SetDrill(old.GetDrillValue())
            item.SetLayerPair(old.TopLayer(), old.BottomLayer())
        else:
            if max(mm(old.GetStart())[1], mm(old.GetEnd())[1]) >= 75.0:
                continue
            item = pcbnew.PCB_TRACK(board)
            item.SetNet(board.FindNet(old.GetNetname()))
            item.SetLayer(old.GetLayer())
            item.SetWidth(old.GetWidth())
            item.SetStart(old.GetStart())
            item.SetEnd(old.GetEnd())
        board.Add(item)
        restored += 1
finally:
    history_path.unlink(missing_ok=True)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Restored {restored} validated local DIAG items")
