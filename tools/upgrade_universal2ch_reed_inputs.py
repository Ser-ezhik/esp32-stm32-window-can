#!/usr/bin/env python3
"""Power the two reed connectors from 5 V and protect STM32 inputs."""

from __future__ import annotations

import math
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = (
    ROOT
    / "hardware"
    / "UNIVERSAL-2CH-F103-IC"
    / "kicad"
    / "UNIVERSAL-2CH-F103-IC.kicad_pcb"
)
FOOTPRINT_ROOT = (
    Path(pcbnew.__file__).resolve().parents[3] / "share" / "kicad" / "footprints"
)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import route_door8ch_f407_ic as multilayer
import route_door8ch_final_gaps as grid


def mm(value: float) -> int:
    return pcbnew.FromMM(value)


def point(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I_MM(x, y)


def xy(position: pcbnew.VECTOR2I) -> tuple[float, float]:
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def same_point(a: pcbnew.VECTOR2I, b: pcbnew.VECTOR2I, tolerance: float = 0.02) -> bool:
    return math.hypot(pcbnew.ToMM(a.x - b.x), pcbnew.ToMM(a.y - b.y)) <= tolerance


def get_or_add_net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    net = board.FindNet(name)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
    return net


def remove_tracks_touching(board: pcbnew.BOARD, net_name: str, positions) -> None:
    for item in board.GetTracks():
        if not isinstance(item, pcbnew.PCB_TRACK) or item.GetNetname() != net_name:
            continue
        if any(same_point(item.GetStart(), p) or same_point(item.GetEnd(), p) for p in positions):
            board.RemoveNative(item)


def remove_track_exact(board: pcbnew.BOARD, net_name: str, start, end) -> None:
    a, b = point(*start), point(*end)
    for item in board.GetTracks():
        if not isinstance(item, pcbnew.PCB_TRACK) or item.GetNetname() != net_name:
            continue
        if ((same_point(item.GetStart(), a) and same_point(item.GetEnd(), b)) or
                (same_point(item.GetStart(), b) and same_point(item.GetEnd(), a))):
            board.RemoveNative(item)
            return


def add_track(board, net, start, end, layer, width=0.20) -> None:
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(net)
    track.SetLayer(layer)
    track.SetWidth(mm(width))
    track.SetStart(point(*start))
    track.SetEnd(point(*end))
    board.Add(track)


def add_via(board, net, position, diameter=0.80, drill=0.40) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetNet(net)
    via.SetPosition(point(*position))
    via.SetWidth(mm(diameter))
    via.SetDrill(mm(drill))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(via)


def add_resistor(board, reference, position) -> pcbnew.FOOTPRINT:
    footprint = pcbnew.FootprintLoad(
        str(FOOTPRINT_ROOT / "Resistor_SMD.pretty"), "R_0603_1608Metric"
    )
    if footprint is None:
        raise RuntimeError("KiCad R_0603 footprint was not found")
    footprint.SetReference(reference)
    footprint.SetValue("4.7K 1% REED INPUT SERIES")
    footprint.SetPosition(point(*position))
    footprint.Value().SetVisible(False)
    board.Add(footprint)
    return footprint


def add_bottom_testpoint(board, reference, net, position) -> pcbnew.FOOTPRINT:
    footprint = pcbnew.FootprintLoad(
        str(FOOTPRINT_ROOT / "TestPoint.pretty"), "TestPoint_Pad_D1.0mm"
    )
    if footprint is None:
        raise RuntimeError("KiCad TestPoint_Pad_D1.0mm footprint was not found")
    footprint.SetReference(reference)
    footprint.SetValue("CAP1188_3V3_WIRE_POINT")
    footprint.SetPosition(point(*position))
    footprint.Value().SetVisible(False)
    board.Add(footprint)
    footprint.Flip(footprint.GetPosition(), False)
    pad = footprint.FindPadByNumber("1")
    pad.SetSize(point(0.6, 0.6))
    pad.SetNet(net)
    return footprint


def add_label(board, text, position, size=0.8) -> None:
    label = pcbnew.PCB_TEXT(board)
    label.SetText(text)
    label.SetPosition(point(*position))
    label.SetLayer(pcbnew.F_SilkS)
    label.SetTextHeight(mm(size))
    label.SetTextWidth(mm(size))
    label.SetTextThickness(mm(0.12))
    label.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    board.Add(label)


def add_wire_jumper(board, reference, net, start, end) -> pcbnew.FOOTPRINT:
    """Add two same-number PTH pads for an insulated, hand-fitted wire link."""
    footprint = pcbnew.FOOTPRINT(board)
    footprint.SetReference(reference)
    footprint.SetValue("INSULATED_WIRE_JUMPER")
    footprint.SetPosition(point(0.0, 0.0))
    board.Add(footprint)
    for position in (start, end):
        pad = pcbnew.PAD(footprint)
        pad.SetNumber("1")
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(point(1.2, 1.2))
        pad.SetDrillSize(point(0.6, 0.6))
        pad.SetLayerSet(pad.PTHMask())
        pad.SetPosition(point(*position))
        pad.SetNet(net)
        footprint.Add(pad)
    footprint.Reference().SetPosition(point((start[0] + end[0]) / 2, (start[1] + end[1]) / 2))
    footprint.Value().SetVisible(False)
    return footprint


def add_duplicate_wire_pad(footprint, pad_number, net, position) -> pcbnew.PAD:
    """Add a wire landing that is electrically paired with an existing PTH pad."""
    pad = pcbnew.PAD(footprint)
    pad.SetNumber(str(pad_number))
    pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(point(1.2, 1.2))
    pad.SetDrillSize(point(0.6, 0.6))
    pad.SetLayerSet(pad.PTHMask())
    pad.SetPosition(point(*position))
    pad.SetNet(net)
    footprint.Add(pad)
    return pad


def physical_island(board: pcbnew.BOARD, seed: pcbnew.BOARD_ITEM):
    """Return the copper-connected island containing seed, not the whole net."""
    net_name = seed.GetNetname()
    items = [
        item
        for item in board.GetTracks()
        if item.GetNetname() == net_name
    ]
    items.extend(
        pad
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
        if pad.GetNetname() == net_name
    )

    def layers(item):
        if isinstance(item, pcbnew.PCB_VIA) or (
            isinstance(item, pcbnew.PAD)
            and item.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        ):
            return {pcbnew.F_Cu, pcbnew.B_Cu}
        if isinstance(item, pcbnew.PAD):
            return {layer for layer in (pcbnew.F_Cu, pcbnew.B_Cu) if item.IsOnLayer(layer)}
        return {item.GetLayer()}

    def segment_distance(p, a, b):
        px, py = xy(p)
        ax, ay = xy(a)
        bx, by = xy(b)
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        ratio = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (ax + ratio * dx), py - (ay + ratio * dy))

    def connected(first, second):
        common_layers = layers(first) & layers(second)
        if not common_layers:
            return False
        if isinstance(first, pcbnew.PAD) and isinstance(second, pcbnew.PAD):
            return any(
                first.GetEffectiveShape(layer).Collide(second.GetPosition(), 0)
                or second.GetEffectiveShape(layer).Collide(first.GetPosition(), 0)
                for layer in common_layers
            )
        if isinstance(first, pcbnew.PAD) or isinstance(second, pcbnew.PAD):
            pad, copper = (first, second) if isinstance(first, pcbnew.PAD) else (second, first)
            anchors = (copper.GetPosition(),) if isinstance(copper, pcbnew.PCB_VIA) else (copper.GetStart(), copper.GetEnd())
            return any(
                pad.GetEffectiveShape(layer).Collide(anchor, 0)
                for layer in common_layers
                for anchor in anchors
            )
        if isinstance(first, pcbnew.PCB_VIA) or isinstance(second, pcbnew.PCB_VIA):
            via, track = (first, second) if isinstance(first, pcbnew.PCB_VIA) else (second, first)
            return segment_distance(via.GetPosition(), track.GetStart(), track.GetEnd()) <= 0.01
        return any(
            segment_distance(anchor, other.GetStart(), other.GetEnd()) <= 0.01
            for anchor in (first.GetStart(), first.GetEnd())
            for other in (second,)
        ) or any(
            segment_distance(anchor, first.GetStart(), first.GetEnd()) <= 0.01
            for anchor in (second.GetStart(), second.GetEnd())
        )

    result = {seed.m_Uuid.AsString(): seed}
    queue = [seed]
    while queue:
        current = queue.pop()
        for candidate in items:
            key = candidate.m_Uuid.AsString()
            if key in result or not connected(current, candidate):
                continue
            result[key] = candidate
            queue.append(candidate)
    return list(result.values())


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    if board.FindFootprintByReference("R290") is not None:
        raise RuntimeError("R290 already exists; refusing to apply the upgrade twice")

    backup = BOARD_PATH.with_name(
        f"{BOARD_PATH.stem}-pre-reed5v-{datetime.now():%Y%m%d-%H%M%S}.kicad_pcb"
    )
    shutil.copy2(BOARD_PATH, backup)

    logic_5v = board.FindNet("LOGIC_5V")
    ground = board.FindNet("GND")
    reed_open = board.FindNet("REED_A_OPEN")
    reed_closed = board.FindNet("REED_A_CLOSED")
    if any(net is None for net in (logic_5v, ground, reed_open, reed_closed)):
        raise RuntimeError("Required board nets are missing")

    raw_open = get_or_add_net(board, "REED_A_OPEN_RAW_5V")
    raw_closed = get_or_add_net(board, "REED_A_CLOSED_RAW_5V")
    j201 = board.FindFootprintByReference("J201")
    j202 = board.FindFootprintByReference("J202")

    remove_tracks_touching(board, "REED_A_OPEN", [j201.FindPadByNumber("2").GetPosition()])
    remove_tracks_touching(board, "REED_A_CLOSED", [j202.FindPadByNumber("2").GetPosition()])
    remove_tracks_touching(
        board,
        "S1_3V3",
        [j201.FindPadByNumber("1").GetPosition(), j202.FindPadByNumber("1").GetPosition()],
    )
    for start, end in (
        ((87.9572, 26.5428), (87.9572, 38.0)),
        ((87.9572, 38.0), (87.9572, 55.3526)),
    ):
        remove_track_exact(board, "S1_3V3", start, end)
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA) and item.GetNetname() == "S1_3V3":
            if same_point(item.GetPosition(), point(87.9572, 55.3526)):
                board.RemoveNative(item)
                break
    remove_track_exact(
        board,
        "S1_3V3",
        (83.5636, 55.3526),
        (87.9572, 55.3526),
    )
    for start, end in (
        ((81.55, 45.95), (75.4375, 45.95)),
    ):
        remove_track_exact(board, "S1_3V3", start, end)

    for connector, raw, value in (
        (j201, raw_open, "REED_OPEN_5V_SIG_GND_PROTECTED"),
        (j202, raw_closed, "REED_CLOSED_5V_SIG_GND_PROTECTED"),
    ):
        connector.FindPadByNumber("1").SetNet(logic_5v)
        connector.FindPadByNumber("2").SetNet(raw)
        connector.SetValue(value)

    r290 = add_resistor(board, "R290", (80.0, 17.0))
    r291 = add_resistor(board, "R291", (84.0, 43.0))
    for resistor, raw, protected in (
        (r290, raw_open, reed_open),
        (r291, raw_closed, reed_closed),
    ):
        resistor.FindPadByNumber("1").SetNet(protected)
        resistor.FindPadByNumber("2").SetNet(raw)

    grid.GRID = 0.25
    grid.CLEARANCE = 0.30
    grid.PAD_EXTRA = 0.0
    grid.EDGE = 0.75

    routes = (
        (j201, r290, raw_open, reed_open, (87.5012, 23.4988)),
        (j202, r291, raw_closed, reed_closed, (81.6193, 34.5)),
    )
    for connector, resistor, raw, protected, old_endpoint in routes:
        raw_pad = xy(resistor.FindPadByNumber("2").GetPosition())
        protected_pad = xy(resistor.FindPadByNumber("1").GetPosition())
        connector_pad = xy(connector.FindPadByNumber("2").GetPosition())
        raw_escape = (raw_pad[0] + 1.5, raw_pad[1])
        protected_escape = (protected_pad[0] - 1.5, protected_pad[1])
        connector_escape = (83.0, connector_pad[1])
        add_track(board, raw, raw_pad, raw_escape, pcbnew.F_Cu)
        add_track(board, raw, connector_pad, connector_escape, pcbnew.F_Cu)
        grid.route(board, raw.GetNetname(), pcbnew.F_Cu, raw_escape, connector_escape, 0.20)
        add_track(board, protected, protected_pad, protected_escape, pcbnew.F_Cu)
        add_via(board, protected, old_endpoint)
        try:
            grid.route(
                board,
                protected.GetNetname(),
                pcbnew.F_Cu,
                protected_escape,
                old_endpoint,
                0.20,
            )
        except RuntimeError:
            # A direct straight segment is checked by the subsequent KiCad DRC.
            add_track(board, protected, protected_escape, old_endpoint, pcbnew.F_Cu)

    multilayer.GRID = 0.25
    multilayer.CLEARANCE = 0.30
    multilayer.route_edge(
        board,
        "LOGIC_5V",
        board.FindFootprintByReference("C233").FindPadByNumber("1"),
        j202.FindPadByNumber("1"),
        0.35,
    )

    # The former reed-supply branch also linked two dense 3.3 V islands.  A
    # short insulated wire preserves that link without crossing the new 5 V
    # feed or moving the existing CH2 control routing.
    branch_3v3 = get_or_add_net(board, "S1_3V3_REED_BRANCH")
    branch_seed = board.FindFootprintByReference("D1201").FindPadByNumber("2")
    for item in physical_island(board, branch_seed):
        if item.GetNetname() == "S1_3V3":
            item.SetNet(branch_3v3)

    add_bottom_testpoint(
        board,
        "TP290",
        board.FindNet("S1_3V3"),
        (83.5636, 55.3526),
    )

    jumper_landing = (78.0, 54.0)
    add_duplicate_wire_pad(
        board.FindFootprintByReference("J220"),
        "6",
        branch_3v3,
        jumper_landing,
    )
    grid.route(
        board,
        "S1_3V3_REED_BRANCH",
        pcbnew.B_Cu,
        (74.941, 56.166),
        jumper_landing,
        0.25,
    )
    add_label(board, "WIRE TP290 -> JP290", (72.0, 54.0), 0.8)
    multilayer.route_edge(
        board,
        "LOGIC_5V",
        j202.FindPadByNumber("1"),
        j201.FindPadByNumber("1"),
        0.35,
    )

    add_label(board, "5V SIG GND", (89.0, 14.2))
    add_label(board, "5V SIG GND", (89.0, 28.0))
    add_label(board, "D-M9N / P-SAFE", (79.0, 46.0))

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Updated: {BOARD_PATH}")
    print(f"Backup:  {backup}")


if __name__ == "__main__":
    main()
