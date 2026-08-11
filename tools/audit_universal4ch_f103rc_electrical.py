"""Electrical-domain and component-contract audit for the four-channel PCB."""

from __future__ import annotations

import sys
from collections import defaultdict

import pcbnew


def pad_map(board: pcbnew.BOARD, reference: str) -> dict[str, str]:
    footprint = board.FindFootprintByReference(reference)
    if not footprint:
        raise AssertionError(f"missing footprint {reference}")
    result: dict[str, str] = {}
    for pad in footprint.Pads():
        if pad.GetNumber():
            result[pad.GetNumber()] = pad.GetNetname()
    return result


def expect(board: pcbnew.BOARD, reference: str, expected: dict[str, str]) -> None:
    actual = pad_map(board, reference)
    for number, net in expected.items():
        if actual.get(number) != net:
            raise AssertionError(
                f"{reference}.{number}: expected {net}, got {actual.get(number, '<missing>')}"
            )


def expect_two_terminal(
    board: pcbnew.BOARD, reference: str, first: str, second: str
) -> None:
    expect(board, reference, {"1": first, "2": second})


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_universal4ch_f103rc_electrical.py BOARD")
    board = pcbnew.LoadBoard(sys.argv[1])

    # Protected low-voltage supply and hold-up path.
    expect(board, "J230", {"1": "LOGIC_12V_IN", "2": "GND"})
    expect_two_terminal(board, "F230", "LOGIC_12V_IN", "LOGIC_12V_FUSED")
    expect_two_terminal(board, "D230", "LOGIC_12V_PROTECTED", "LOGIC_12V_FUSED")
    expect_two_terminal(board, "D231", "LOGIC_12V_PROTECTED", "GND")
    expect(
        board,
        "DC1",
        {"1": "LOGIC_12V_PROTECTED", "2": "GND", "3": "LOGIC_5V", "4": "GND"},
    )
    expect_two_terminal(board, "D280", "S1_5V_HOLD", "LOGIC_5V")
    expect_two_terminal(board, "C280", "S1_5V_HOLD", "GND")
    expect(board, "J280B", {"1": "S1_5V_REG"})
    expect(board, "U230", {"1": "GND", "2": "LOGIC_3V3", "3": "S1_5V_REG"})
    expect_two_terminal(board, "R2301", "LOGIC_3V3", "S1_3V3")

    for reference in ("C230", "C231", "C232"):
        expect_two_terminal(board, reference, "LOGIC_12V_PROTECTED", "GND")
    for reference in ("C233", "C234", "C235", "C236", "C237"):
        expect_two_terminal(board, reference, "LOGIC_5V", "GND")
    for reference in ("C238", "C239"):
        expect_two_terminal(board, reference, "LOGIC_3V3", "GND")

    # Undervoltage detector: approximately 9.44 V rising threshold.
    expect(
        board,
        "U270",
        {
            "1": "POWER_GOOD",
            "2": "GND",
            "3": "PGOOD_SENSE",
            "4": "GND",
            "5": "LOGIC_12V_FUSED",
            "6": "POWER_GOOD",
        },
    )
    expect_two_terminal(board, "R270", "LOGIC_12V_FUSED", "PGOOD_SENSE")
    expect_two_terminal(board, "R271", "PGOOD_SENSE", "GND")
    expect_two_terminal(board, "R272", "S1_3V3", "POWER_GOOD")
    expect_two_terminal(board, "C270", "LOGIC_12V_FUSED", "GND")
    expect_two_terminal(board, "C271", "PGOOD_SENSE", "GND")

    # MCU supply pins and local decoupling.
    expect(
        board,
        "U300",
        {
            "1": "S1_3V3",
            "12": "GND",
            "13": "S1_3V3",
            "18": "GND",
            "19": "S1_3V3",
            "31": "GND",
            "32": "S1_3V3",
            "47": "GND",
            "48": "S1_3V3",
            "63": "GND",
            "64": "S1_3V3",
        },
    )
    for reference in ("C3004", "C3005", "C3006", "C3007", "C3008", "C3009"):
        expect_two_terminal(board, reference, "S1_3V3", "GND")

    # CAP1188 and EEPROM share SPI1 but use independent chip selects.
    expect(
        board,
        "CAP1",
        {
            "1": "CAP_CS",
            "2": "CAP_MOSI",
            "3": "CAP_MISO",
            "4": "CAP_SCK",
            "13": "CAP_IRQ",
            "20": "CAP_C3_RAW",
            "21": "CAP_C2_RAW",
            "22": "CAP_C1_RAW",
            "23": "S1_3V3",
            "24": "CAP_RESET",
            "25": "GND",
        },
    )
    expect(
        board,
        "U250",
        {
            "1": "EEPROM_CS",
            "2": "CAP_MISO",
            "3": "EEPROM_WP",
            "4": "GND",
            "5": "CAP_MOSI",
            "6": "CAP_SCK",
            "7": "EEPROM_HOLD",
            "8": "S1_3V3",
        },
    )
    for index in range(1, 4):
        expect_two_terminal(board, f"R20{index}", f"CAP_C{index}_RAW", f"CAP_C{index}_FIELD")
        expect(board, f"J21{index}", {"1": f"CAP_C{index}_FIELD", "2": "GND"})

    # CAN connector, protection, common-mode choke, optional termination.
    expect(board, "J240", {"1": "CANH_ENTRY", "2": "CANL_ENTRY", "3": "GND", "4": "GND"})
    expect(board, "L240", {"1": "CANH_ENTRY", "2": "CANL_ENTRY", "3": "CANL_BUS", "4": "CANH_BUS"})
    expect_two_terminal(board, "D240", "CANH_ENTRY", "GND")
    expect_two_terminal(board, "D241", "CANL_ENTRY", "GND")
    expect_two_terminal(board, "R240", "CANH_BUS", "CANL_BUS")
    expect(
        board,
        "CAN1",
        {"1": "LOGIC_3V3", "2": "GND", "3": "S1_CAN_TX", "4": "S1_CAN_RX", "5": "CANH_BUS", "6": "CANL_BUS"},
    )

    for channel in range(1, 5):
        prefix = f"CH{channel}"
        rail = "S1_3V3"
        expect_two_terminal(board, f"C1{channel}01", f"FUSED_12V_{prefix}", "GND")
        expect_two_terminal(board, f"C1{channel}02", f"FUSED_12V_{prefix}", "GND")
        expect_two_terminal(board, f"R1{channel}07", f"{prefix}_DIAG", rail)
        expect_two_terminal(board, f"R1{channel}09", f"{prefix}_CS_RAW", "GND")
        expect_two_terminal(board, f"R1{channel}10", f"{prefix}_CS_RAW", f"{prefix}_CURRENT_ADC")
        expect(board, f"D1{channel}01", {"1": "GND", "2": rail, "3": f"{prefix}_CURRENT_ADC"})
        expect(board, f"J{channel}", {"1": f"FUSED_12V_{prefix}", "2": "GND", "3": f"{prefix}_OUTA", "4": f"{prefix}_OUTB"})

    # Every named net must contain at least two pads, except the intentional
    # regulator-side assembly-wire test point.
    pads_by_net: dict[str, list[str]] = defaultdict(list)
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetname():
                pads_by_net[pad.GetNetname()].append(
                    f"{footprint.GetReference()}.{pad.GetNumber()}"
                )
    allowed_singletons: set[str] = set()
    singletons = {
        net: pads for net, pads in pads_by_net.items() if len(pads) == 1 and net not in allowed_singletons
    }
    if singletons:
        raise AssertionError(f"single-pad nets: {singletons}")
    if "S2_3V3" in pads_by_net:
        raise AssertionError("orphan legacy rail S2_3V3 is still present")

    print("PASS: complete four-channel electrical-domain contract verified")
    print("NOTE: C280+ to J280B remains a mandatory insulated assembly wire")


if __name__ == "__main__":
    main()
