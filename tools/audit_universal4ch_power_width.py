"""Measure effective copper width along the 12 main 4-channel power paths."""

from __future__ import annotations

import math
import statistics
import sys
from collections import defaultdict

import pcbnew

from reinforce_universal4ch_power import main_power_segments


STEP_MM = 0.025
SCAN_MM = 4.0
COPPER_THICKNESS_MM = 0.070  # 2 oz finished copper target
COPPER_RESISTIVITY_OHM_MM2_PER_M = 0.01724
CHECK_CURRENT_A = 5.0


def point_in_track(track: pcbnew.PCB_TRACK, x_mm: float, y_mm: float) -> bool:
    a = track.GetStart()
    b = track.GetEnd()
    ax, ay = pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)
    bx, by = pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        distance = math.hypot(x_mm - ax, y_mm - ay)
    else:
        t = max(0.0, min(1.0, ((x_mm - ax) * dx + (y_mm - ay) * dy) / length_sq))
        distance = math.hypot(x_mm - (ax + t * dx), y_mm - (ay + t * dy))
    return distance <= pcbnew.ToMM(track.GetWidth()) / 2.0


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_universal4ch_power_width.py BOARD")

    board = pcbnew.LoadBoard(sys.argv[1])
    selected = main_power_segments(board)
    tracks_by_key: dict[tuple[str, int], list[pcbnew.PCB_TRACK]] = defaultdict(list)
    zones_by_key: dict[tuple[str, int], list[pcbnew.SHAPE_POLY_SET]] = defaultdict(list)
    selected_by_net: dict[str, list[pcbnew.PCB_TRACK]] = defaultdict(list)

    for item in board.GetTracks():
        if item.Type() == pcbnew.PCB_TRACE_T:
            tracks_by_key[(item.GetNetname(), item.GetLayer())].append(item)
    for zone in board.Zones():
        if zone.GetZoneName() == "POWER_REINFORCEMENT":
            zones_by_key[(zone.GetNetname(), zone.GetLayer())].append(
                zone.GetFilledPolysList(zone.GetLayer())
            )
    for track in selected:
        selected_by_net[track.GetNetname()].append(track)

    def has_copper(net_name: str, layer: int, x_mm: float, y_mm: float) -> bool:
        p = pcbnew.VECTOR2I_MM(x_mm, y_mm)
        if any(poly.Contains(p) for poly in zones_by_key[(net_name, layer)]):
            return True
        return any(point_in_track(track, x_mm, y_mm) for track in tracks_by_key[(net_name, layer)])

    failed = False
    for net_name in sorted(selected_by_net):
        samples: list[tuple[float, float, float, int, float]] = []
        for track in selected_by_net[net_name]:
            a = track.GetStart()
            b = track.GetEnd()
            ax, ay = pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)
            bx, by = pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy)
            if length < 0.75:
                continue
            nx, ny = -dy / length, dx / length
            sample_count = max(3, int(length / 0.5))
            for index in range(1, sample_count):
                t = index / sample_count
                x = ax + t * dx
                y = ay + t * dy
                negative = 0.0
                positive = 0.0
                while negative < SCAN_MM and has_copper(
                    net_name, track.GetLayer(), x - nx * negative, y - ny * negative
                ):
                    negative += STEP_MM
                while positive < SCAN_MM and has_copper(
                    net_name, track.GetLayer(), x + nx * positive, y + ny * positive
                ):
                    positive += STEP_MM
                samples.append(
                    (
                        max(0.0, negative + positive - STEP_MM),
                        x,
                        y,
                        track.GetLayer(),
                        length / sample_count,
                    )
                )

        samples.sort()
        widths = [sample[0] for sample in samples]
        p05 = widths[max(0, int(len(widths) * 0.05) - 1)]
        median = statistics.median(widths)
        minimum = widths[0]
        resistance = sum(
            COPPER_RESISTIVITY_OHM_MM2_PER_M * (sample[4] / 1000.0)
            / (max(sample[0], 0.20) * COPPER_THICKNESS_MM)
            for sample in samples
        )
        narrow_length = sum(sample[4] for sample in samples if sample[0] < 1.50)
        status = (
            "PASS"
            if minimum >= 0.45 and median >= 2.75 and resistance <= 0.006
            else "FAIL"
        )
        failed |= status == "FAIL"
        narrow = samples[0]
        print(
            f"{net_name:15s} min={minimum:5.3f} mm  p05={p05:5.3f} mm  "
            f"median={median:5.3f} mm  {status}  "
            f"R2oz={resistance * 1000:4.2f} mOhm  "
            f"P5A={CHECK_CURRENT_A ** 2 * resistance:4.3f} W  "
            f"<1.5mm={narrow_length:3.1f} mm  "
            f"@({narrow[1]:.3f},{narrow[2]:.3f}) {pcbnew.LayerName(narrow[3])}"
        )

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
