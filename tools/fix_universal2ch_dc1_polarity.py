"""Replace the wrong DC1 footprint with the verified 18 x 13 mm module."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
KICAD = ROOT / "hardware" / "UNIVERSAL-2CH-F103-IC" / "kicad"
BOARD_PATH = KICAD / "UNIVERSAL-2CH-F103-IC.kicad_pcb"
SOURCE_PATH = KICAD / "UNIVERSAL-2CH-F103-IC-pre-dc1-polarity-fix-20260812.kicad_pcb"


def v(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def add_track(board, net_name, layer, width, start, end):
    track = pcbnew.PCB_TRACK(board)
    track.SetNetCode(board.GetNetInfo().GetNetItem(net_name).GetNetCode())
    track.SetLayer(layer)
    track.SetWidth(pcbnew.FromMM(width))
    track.SetStart(start)
    track.SetEnd(end)
    board.Add(track)


def add_via(board, net_name, position, diameter=0.8, drill=0.4):
    via = pcbnew.PCB_VIA(board)
    via.SetNetCode(board.GetNetInfo().GetNetItem(net_name).GetNetCode())
    via.SetPosition(position)
    via.SetWidth(pcbnew.FromMM(diameter))
    via.SetDrill(pcbnew.FromMM(drill))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(via)


def point(position):
    return (round(position.x / 1_000_000, 4), round(position.y / 1_000_000, 4))


def remove_trace(board, tracks, removed_tracks, net_name, start, end):
    wanted = {point(start), point(end)}
    for track in tracks:
        if id(track) in removed_tracks:
            continue
        if (track.Type() == pcbnew.PCB_TRACE_T and track.GetNetname() == net_name
                and {point(track.GetStart()), point(track.GetEnd())} == wanted):
            board.Remove(track)
            removed_tracks.add(id(track))
            return
    raise RuntimeError(f"Missing trace {net_name}: {wanted}")


def main() -> None:
    # Always rebuild from the untouched pre-fix board so an interrupted run cannot
    # accumulate edits or retain the first, incomplete polarity correction.
    board = pcbnew.LoadBoard(str(SOURCE_PATH))
    dc1 = next(fp for fp in board.GetFootprints() if fp.GetReference() == "DC1")
    pads = {pad.GetNumber(): pad for pad in dc1.Pads()}
    tracks = list(board.GetTracks())
    removed_tracks = set()

    old_positions = {number: pad.GetPosition() for number, pad in pads.items()}
    expected = {
        "1": ("LOGIC_12V_PROTECTED", v(81.3, 67.5)),
        "2": ("GND", v(81.3, 81.5)),
        "3": ("LOGIC_5V", v(63.0, 81.5)),
        "4": ("GND", v(63.0, 67.5)),
    }
    for number, (net, position) in expected.items():
        if pads[number].GetNetname() != net or pads[number].GetPosition() != position:
            raise RuntimeError(f"Unexpected source state at DC1 pad {number}")

    # Verified module: 18 x 13 mm. Hole centers are 15 x 9 mm.
    # The module is rotated 180 degrees on this PCB: input right, output left.
    new_positions = {
        "1": v(77.6, 70.75),  # IN+
        "2": v(77.6, 79.75),  # IN-
        "3": v(62.6, 70.75),  # OUT+
        "4": v(62.6, 79.75),  # OUT-
    }

    # Remove only the old stubs touching DC1. The surrounding routed network is
    # retained and gets four new, short connections below.
    removed = 0
    for track in tracks:
        if track.Type() != pcbnew.PCB_TRACE_T:
            continue
        if any(
            track.GetStart() == position or track.GetEnd() == position
            for position in old_positions.values()
        ):
            board.Remove(track)
            removed_tracks.add(id(track))
            removed += 1
    if removed != 10:
        raise RuntimeError(f"Expected ten old DC1 stubs, removed {removed}")

    for number, position in new_positions.items():
        pads[number].SetPosition(position)
        pads[number].SetSize(v(3.2, 3.2))

    # Move two bottom-side bypass capacitors away from the new plated holes.
    c237 = next(fp for fp in board.GetFootprints() if fp.GetReference() == "C237")
    remove_trace(board, tracks, removed_tracks, "LOGIC_5V", v(62.775, 78.0), v(63.0, 78.225))
    remove_trace(board, tracks, removed_tracks, "LOGIC_5V", v(59.0895, 80.85), v(60.3448, 82.1052))
    remove_trace(board, tracks, removed_tracks, "LOGIC_5V", v(60.3448, 82.1052), v(60.95, 81.5))
    remove_trace(board, tracks, removed_tracks, "LOGIC_5V", v(57.072, 80.85), v(59.0895, 80.85))
    remove_trace(board, tracks, removed_tracks, "LOGIC_5V", v(54.222, 78.0), v(57.072, 80.85))
    remove_trace(board, tracks, removed_tracks, "LOGIC_5V", v(49.475, 78.0), v(54.222, 78.0))
    remove_trace(board, tracks, removed_tracks, "GND", v(61.225, 78.0), v(58.15, 78.0))
    remove_trace(board, tracks, removed_tracks, "GND", v(61.225, 78.0), v(61.225, 76.0))
    remove_trace(board, tracks, removed_tracks, "GND", v(63.225, 84.0), v(66.525, 84.0))
    remove_trace(board, tracks, removed_tracks, "S1_3V3_REED_BRANCH", v(59.0, 71.775), v(59.0, 70.3))
    remove_trace(board, tracks, removed_tracks, "S1_3V3_REED_BRANCH", v(59.0, 70.3), v(58.6911, 69.9911))
    c237.SetPosition(v(64.0, 84.0))

    # Reroute the two signal traces which previously crossed the new holes.
    remove_trace(board, tracks, removed_tracks, "S1_3V3_REED_BRANCH", v(54.9589, 69.9911), v(65.3864, 69.9911))
    add_track(board, "S1_3V3_REED_BRANCH", pcbnew.B_Cu, 0.25,
              v(54.9589, 69.9911), v(58.0, 67.5))
    add_track(board, "S1_3V3_REED_BRANCH", pcbnew.B_Cu, 0.25,
              v(58.0, 67.5), v(65.3864, 65.4722))
    add_track(board, "S1_3V3_REED_BRANCH", pcbnew.B_Cu, 0.25,
              v(59.0, 71.775), v(58.0, 67.5))

    remove_trace(board, tracks, removed_tracks, "CAP_RESET", v(74.64, 69.8), v(88.0, 69.8))
    add_track(board, "CAP_RESET", pcbnew.F_Cu, 0.20,
              v(74.64, 69.8), v(74.64, 67.5))
    add_track(board, "CAP_RESET", pcbnew.F_Cu, 0.20,
              v(74.64, 67.5), v(88.0, 67.5))
    add_track(board, "CAP_RESET", pcbnew.F_Cu, 0.20,
              v(88.0, 67.5), v(88.0, 69.8))

    # Clean, non-crossing connections to the existing local trunks.
    add_track(board, "LOGIC_12V_PROTECTED", pcbnew.B_Cu, 0.50,
              new_positions["1"], v(79.1393, 69.6607))
    add_track(board, "GND", pcbnew.F_Cu, 0.35,
              new_positions["2"], v(79.7688, 79.9688))
    add_track(board, "GND", pcbnew.B_Cu, 0.35,
              new_positions["2"], v(80.35, 81.5))
    add_track(board, "GND", pcbnew.B_Cu, 0.25,
              new_positions["2"], v(81.3, 80.1))
    add_track(board, "GND", pcbnew.B_Cu, 0.25,
              new_positions["2"], v(81.7998, 81.9998))
    add_track(board, "LOGIC_5V", pcbnew.F_Cu, 0.35,
              new_positions["3"], v(65.2, 75.0))
    add_track(board, "LOGIC_5V", pcbnew.F_Cu, 0.35,
              v(65.2, 75.0), v(65.404, 75.0))

    # Restore the moved LOGIC_5V bypass capacitor through a nearby via.
    add_track(board, "LOGIC_5V", pcbnew.B_Cu, 0.35, v(64.775, 84.0), v(65.0, 79.096))
    add_via(board, "LOGIC_5V", v(65.0, 79.096))
    add_track(board, "LOGIC_5V", pcbnew.F_Cu, 0.35, v(65.0, 79.096), v(65.404, 79.096))
    add_track(board, "GND", pcbnew.B_Cu, 0.25, v(63.225, 84.0), v(62.0, 84.0))
    add_via(board, "GND", v(62.0, 84.0))

    # Reconnect the pre-existing 5 V branch that formerly ended at the old pad.
    route_b = [v(49.475, 78.0), v(55.0, 78.0), v(55.5, 78.5),
               v(56.0, 78.5), v(56.5, 79.0)]
    for start, end in zip(route_b, route_b[1:]):
        add_track(board, "LOGIC_5V", pcbnew.B_Cu, 0.35, start, end)
    add_via(board, "LOGIC_5V", v(56.5, 79.0))
    route_f = [v(56.5, 79.0), v(58.5, 77.0), v(58.5, 76.5),
               v(59.0, 76.0), v(60.0, 76.0), v(61.5, 77.5),
               v(63.5, 77.5), v(65.0, 76.0), v(65.0, 79.096)]
    for start, end in zip(route_f, route_f[1:]):
        add_track(board, "LOGIC_5V", pcbnew.F_Cu, 0.35, start, end)

    add_track(board, "GND", pcbnew.F_Cu, 0.35, new_positions["4"], v(60.0, 83.0))
    add_track(board, "GND", pcbnew.F_Cu, 0.35, v(60.0, 83.0), v(55.5, 83.6885))

    ground_b = [new_positions["4"], v(62.0, 79.5), v(60.5, 77.5),
                v(60.5, 76.5), v(59.0, 75.0), v(59.0, 74.5), v(58.5, 74.0)]
    for start, end in zip(ground_b, ground_b[1:]):
        add_track(board, "GND", pcbnew.B_Cu, 0.35, start, end)
    add_via(board, "GND", v(58.5, 74.0))
    add_track(board, "GND", pcbnew.F_Cu, 0.35, v(58.5, 74.0), v(54.5, 67.5))
    add_via(board, "GND", v(54.5, 67.5))
    add_track(board, "GND", pcbnew.B_Cu, 0.35, v(54.5, 67.5), v(54.725, 67.5))

    # Update the physical outline from 22.3 x 17 mm to 18 x 13 mm.
    for item in dc1.GraphicalItems():
        if isinstance(item, pcbnew.PCB_SHAPE):
            if item.GetLayer() == pcbnew.F_Fab:
                item.SetStart(v(61.1, 68.75))
                item.SetEnd(v(79.1, 81.75))
            elif item.GetLayer() == pcbnew.F_CrtYd:
                item.SetStart(v(60.6, 68.25))
                item.SetEnd(v(79.6, 82.25))
            elif item.GetLayer() == pcbnew.F_SilkS:
                item.SetStart(v(65.0, 75.25))
                item.SetEnd(v(76.0, 75.25))
        elif isinstance(item, pcbnew.PCB_TEXT):
            positions = {
                "OUT-": ("OUT+", v(65.3, 72.55)),
                "OUT+": ("OUT-", v(65.3, 77.95)),
                "IN+": ("IN+", v(75.7, 72.55)),
                "IN-": ("IN-", v(75.7, 77.95)),
            }
            if item.GetText() in positions:
                text, position = positions[item.GetText()]
                item.SetText(text)
                item.SetPosition(position)

    dc1.SetValue("DCE001_FIXED_5V_18x13mm")
    for zone in board.Zones():
        if zone.GetNetname() == "GND" and zone.GetLayer() == pcbnew.B_Cu:
            zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD_PATH), board)

    print(f"Corrected board: {BOARD_PATH}")
    print("DC1 body: 18.0 x 13.0 mm")
    print("DC1 hole grid: 15.0 x 9.0 mm")
    print("Top row: OUT+ / IN+")
    print("Bottom row: OUT- / IN-")
    print(f"Removed old stubs: {removed}; added new stubs: 5")


if __name__ == "__main__":
    main()
