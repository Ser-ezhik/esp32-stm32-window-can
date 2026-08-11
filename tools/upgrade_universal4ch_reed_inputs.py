"""Convert the compact 4-channel board reed inputs to protected 5 V wiring."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = (
    ROOT
    / "hardware"
    / "UNIVERSAL-4CH-F103RC-IC"
    / "kicad"
    / "UNIVERSAL-4CH-F103RC-IC.kicad_pcb"
)
KICAD_ROOT = Path(pcbnew.__file__).resolve().parents[3]
RESISTOR_LIBRARY = KICAD_ROOT / "share" / "kicad" / "footprints" / "Resistor_SMD.pretty"


def point(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def ensure_net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    net = board.FindNet(name)
    if net:
        return net
    net = pcbnew.NETINFO_ITEM(board, name)
    board.Add(net)
    return net


def add_bottom_resistor(
    board: pcbnew.BOARD,
    reference: str,
    position: tuple[float, float],
    protected_net: str,
    raw_net: str,
) -> None:
    footprint = pcbnew.FootprintLoad(str(RESISTOR_LIBRARY), "R_0603_1608Metric")
    if footprint is None:
        raise RuntimeError("KiCad R_0603 footprint was not found")
    footprint.SetReference(reference)
    footprint.SetValue("4.7K 1% REED INPUT SERIES")
    footprint.SetPosition(point(*position))
    footprint.SetOrientationDegrees(90.0)
    footprint.Value().SetVisible(False)
    board.Add(footprint)
    footprint.Flip(footprint.GetPosition(), False)
    footprint.SetOrientationDegrees(90.0)
    footprint.FindPadByNumber("1").SetNet(ensure_net(board, protected_net))
    footprint.FindPadByNumber("2").SetNet(ensure_net(board, raw_net))


def add_front_label(board: pcbnew.BOARD, text: str, position: tuple[float, float], size=0.8) -> None:
    label = pcbnew.PCB_TEXT(board)
    label.SetText(text)
    label.SetPosition(point(*position))
    label.SetLayer(pcbnew.F_SilkS)
    label.SetTextHeight(pcbnew.FromMM(size))
    label.SetTextWidth(pcbnew.FromMM(size))
    label.SetTextThickness(pcbnew.FromMM(0.12))
    label.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    board.Add(label)


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    if board.FindFootprintByReference("R290") is not None:
        raise RuntimeError("R290 already exists; refusing to apply the upgrade twice")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BOARD_PATH.with_name(f"{BOARD_PATH.stem}-pre-reed5v-{stamp}.kicad_pcb")
    shutil.copy2(BOARD_PATH, backup)

    channels = (
        ("J201", "R290", "REED_A_OPEN", "REED_A_OPEN_RAW_5V", (89.525, 80.5)),
        ("J202", "R291", "REED_A_CLOSED", "REED_A_CLOSED_RAW_5V", (102.525, 80.5)),
        ("J203", "R292", "REED_A_IN_PLACE", "REED_A_IN_PLACE_RAW_5V", (115.525, 80.5)),
    )

    for connector_ref, resistor_ref, protected, raw, resistor_position in channels:
        connector = board.FindFootprintByReference(connector_ref)
        if connector is None:
            raise RuntimeError(f"Missing connector {connector_ref}")
        connector.SetValue(connector.GetValue().replace("3V3", "5V") + "_PROTECTED")
        connector.FindPadByNumber("1").SetNet(ensure_net(board, "LOGIC_5V"))
        connector.FindPadByNumber("2").SetNet(ensure_net(board, raw))
        add_bottom_resistor(board, resistor_ref, resistor_position, protected, raw)

    for x_mm in (86.025, 99.025, 112.025):
        add_front_label(board, "5V SIG GND", (x_mm + 3.5, 82.0), 0.8)
    add_front_label(board, "D-M9N / P-SAFE 5V", (102.5, 78.5), 0.8)

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Updated: {BOARD_PATH}")
    print(f"Backup:  {backup}")


if __name__ == "__main__":
    main()
