"""Add hand-selected redundant OUTA vias in verified open copper corridors."""

from __future__ import annotations

import sys

import pcbnew


VIA_LOCATIONS = {
    "CH1_OUTA": ((16.30, 31.50),),
    # Keep these exactly on the existing B.Cu trunk centerline. KiCad's
    # connectivity engine does not treat a near-collinear via as an endpoint.
    "CH4_OUTA": ((110.4334, 34.80), (110.4334, 34.10)),
}


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: add_universal4ch_manual_power_vias.py INPUT OUTPUT")
    board = pcbnew.LoadBoard(sys.argv[1])
    cs_net = board.FindNet("CH4_CS_DIS")
    remove_points = {
        frozenset(((111.0777, 36.1494), (111.0777, 35.2648))),
        frozenset(((111.0777, 35.2648), (102.4741, 26.6612))),
    }
    for track in list(board.GetTracks()):
        if isinstance(track, pcbnew.PCB_VIA) or track.GetNetname() != "CH4_CS_DIS":
            continue
        start = (round(pcbnew.ToMM(track.GetStart().x), 4), round(pcbnew.ToMM(track.GetStart().y), 4))
        end = (round(pcbnew.ToMM(track.GetEnd().x), 4), round(pcbnew.ToMM(track.GetEnd().y), 4))
        if frozenset((start, end)) in remove_points:
            board.Delete(track)

    # Split the existing CH4_OUTA B.Cu trunk at the redundant vias. A via that
    # merely lies over the middle of a segment is electrically touching, but
    # KiCad still reports it as dangling unless it is a segment endpoint.
    outa_net = board.FindNet("CH4_OUTA")
    trunk_endpoints = frozenset(((110.4334, 35.5002), (110.4334, 33.2233)))
    for track in list(board.GetTracks()):
        if isinstance(track, pcbnew.PCB_VIA) or track.GetNetname() != "CH4_OUTA":
            continue
        start = (round(pcbnew.ToMM(track.GetStart().x), 4), round(pcbnew.ToMM(track.GetStart().y), 4))
        end = (round(pcbnew.ToMM(track.GetEnd().x), 4), round(pcbnew.ToMM(track.GetEnd().y), 4))
        if track.GetLayer() == pcbnew.B_Cu and frozenset((start, end)) == trunk_endpoints:
            width = track.GetWidth()
            board.Delete(track)
            points = ((110.4334, 35.5002), (110.4334, 34.80), (110.4334, 34.10), (110.4334, 33.2233))
            for segment_start, segment_end in zip(points, points[1:]):
                segment = pcbnew.PCB_TRACK(board)
                segment.SetNet(outa_net)
                segment.SetStart(pcbnew.VECTOR2I_MM(*segment_start))
                segment.SetEnd(pcbnew.VECTOR2I_MM(*segment_end))
                segment.SetLayer(pcbnew.B_Cu)
                segment.SetWidth(width)
                board.Add(segment)

            # Give the same vias explicit F.Cu endpoints as well. Zone-only
            # contact is valid copper but remains a dangling-via warning.
            front_points = ((110.4334, 35.5002), (110.4334, 34.80), (110.4334, 34.10))
            for segment_start, segment_end in zip(front_points, front_points[1:]):
                segment = pcbnew.PCB_TRACK(board)
                segment.SetNet(outa_net)
                segment.SetStart(pcbnew.VECTOR2I_MM(*segment_start))
                segment.SetEnd(pcbnew.VECTOR2I_MM(*segment_end))
                segment.SetLayer(pcbnew.F_Cu)
                segment.SetWidth(width)
                board.Add(segment)
            break
    route = (
        (102.4741, 26.6612),
        (108.8, 31.0),
        (112.0, 31.0),
        (112.0, 37.0),
        (111.0777, 36.1494),
    )
    for start, end in zip(route, route[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetNet(cs_net)
        track.SetStart(pcbnew.VECTOR2I_MM(*start))
        track.SetEnd(pcbnew.VECTOR2I_MM(*end))
        track.SetLayer(pcbnew.F_Cu)
        track.SetWidth(pcbnew.FromMM(0.20))
        board.Add(track)
    for net_name, positions in VIA_LOCATIONS.items():
        net = board.FindNet(net_name)
        if not net:
            raise RuntimeError(f"Missing net {net_name}")
        for x_mm, y_mm in positions:
            via = pcbnew.PCB_VIA(board)
            via.SetNet(net)
            via.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
            via.SetWidth(pcbnew.FromMM(0.60))
            via.SetDrill(pcbnew.FromMM(0.30))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            board.Add(via)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[2], board)
    print(f"Added {sum(map(len, VIA_LOCATIONS.values()))} hand-selected power vias")


if __name__ == "__main__":
    main()
