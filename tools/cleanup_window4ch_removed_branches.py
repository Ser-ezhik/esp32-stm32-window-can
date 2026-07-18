"""Remove known dead copper branches left by omitted WINDOW-4CH modules."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
board = pcbnew.LoadBoard(str(BOARD_PATH))

DEAD_ENDPOINTS = {
    "S2_3V3": {(169.0, 158.0), (112.62, 153.0)},
    "S1_3V3": {(239.0, 74.0), (187.0, 69.0), (217.0, 85.0), (176.0, 71.0),
                (65.0, 69.0), (52.241, 74.783)},
    "LOGIC_3V3": {
        (20.0, 126.31), (124.27, 115.0), (132.0, 115.0),
        (84.47, 115.0), (182.85, 88.0), (64.27, 115.0),
    },
    "LOGIC_5V": {
        (217.38, 158.0), (177.38, 158.0), (58.7973, 105.0037),
        (97.38, 158.0), (23.0, 158.0), (20.0, 158.0), (172.0, 158.0),
        (58.7973, 110.0), (61.0, 158.0),
    },
    "CANL_BUS": {(140.0, 156.4), (150.0, 112.0)},
    "CANH_BUS": {(128.0, 153.86), (148.0, 110.0), (160.0, 140.0), (68.0, 110.0)},
}


def mm_key(position):
    return round(position.x / 1_000_000.0, 4), round(position.y / 1_000_000.0, 4)


removed = 0
for item in list(board.GetTracks()):
    endpoints = DEAD_ENDPOINTS.get(item.GetNetname())
    if not endpoints:
        continue
    if isinstance(item, pcbnew.PCB_VIA):
        hit = mm_key(item.GetPosition()) in endpoints
    else:
        hit = mm_key(item.GetStart()) in endpoints or mm_key(item.GetEnd()) in endpoints
    if hit:
        board.Delete(item)
        removed += 1

for item in list(board.GetTracks()):
    if (not isinstance(item, pcbnew.PCB_VIA)
            and item.GetNetname().startswith("REED_A_")
            and item.GetLength() < pcbnew.FromMM(0.15)):
        board.Delete(item)
        removed += 1

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
print(f"Removed {removed} dead branch items")
