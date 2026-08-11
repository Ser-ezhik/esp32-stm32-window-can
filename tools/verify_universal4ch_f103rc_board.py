"""Verify the critical net-to-pad contract of the universal four-channel PCB."""

from __future__ import annotations

import sys

import pcbnew


MCU_PADS = {
    "5": "MCU_HSE_IN",
    "6": "MCU_HSE_OUT",
    "7": "S1_NRST",
    "8": "REED_A_OPEN",
    "9": "REED_A_CLOSED",
    "10": "REED_A_IN_PLACE",
    "11": "POWER_GOOD",
    "14": "CH1_CURRENT_ADC",
    "15": "CH2_CURRENT_ADC",
    "16": "CH3_CURRENT_ADC",
    "17": "CH4_CURRENT_ADC",
    "20": "CAP_CS",
    "21": "CAP_SCK",
    "22": "CAP_MISO",
    "23": "CAP_MOSI",
    "24": "EEPROM_CS",
    "25": "CAP_IRQ",
    "26": "CH1_INA_MCU",
    "27": "CH1_INB_MCU",
    "29": "CH2_INA_MCU",
    "30": "CH2_INB_MCU",
    "33": "CH3_INA_MCU",
    "34": "CH3_INB_MCU",
    "35": "CH4_INA_MCU",
    "36": "CH4_INB_MCU",
    "37": "CH1_DIAG",
    "38": "CH2_DIAG",
    "39": "CH3_DIAG",
    "40": "CH4_DIAG",
    "41": "CH1_PWM_MCU",
    "42": "CH2_PWM_MCU",
    "43": "CH3_PWM_MCU",
    "44": "CH4_PWM_MCU",
    "46": "S1_SWDIO",
    "49": "S1_SWCLK",
    "51": "CAP_RESET",
    "60": "MCU_BOOT0",
    "61": "S1_CAN_RX",
    "62": "S1_CAN_TX",
}


def pad_map(board: pcbnew.BOARD, reference: str) -> dict[str, str]:
    footprint = board.FindFootprintByReference(reference)
    if not footprint:
        raise AssertionError(f"missing footprint {reference}")
    result: dict[str, str] = {}
    for pad in footprint.Pads():
        number = pad.GetNumber()
        net = pad.GetNetname()
        if number and number not in result:
            result[number] = net
        elif number and result[number] != net:
            raise AssertionError(f"{reference} pad {number} has inconsistent duplicate nets")
    return result


def expect_pads(board: pcbnew.BOARD, reference: str, expected: dict[str, str]) -> None:
    actual = pad_map(board, reference)
    for number, net in expected.items():
        if actual.get(number) != net:
            raise AssertionError(
                f"{reference} pad {number}: expected {net}, found {actual.get(number, '<missing>')}"
            )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_universal4ch_f103rc_board.py BOARD.kicad_pcb")

    board = pcbnew.LoadBoard(sys.argv[1])
    expect_pads(board, "U300", MCU_PADS)

    for channel in range(1, 5):
        prefix = f"CH{channel}"
        expect_pads(
            board,
            f"U{channel}",
            {
                "1": f"{prefix}_OUTA",
                "3": f"FUSED_12V_{prefix}",
                "4": f"{prefix}_INA",
                "5": f"{prefix}_DIAG",
                "6": f"{prefix}_CS_DIS",
                "7": f"{prefix}_PWM",
                "8": f"{prefix}_CS_RAW",
                "10": f"{prefix}_INB",
                "12": f"FUSED_12V_{prefix}",
                "15": f"{prefix}_OUTB",
                "18": "GND",
            },
        )
        expect_pads(
            board,
            f"J{channel}",
            {"1": f"FUSED_12V_{prefix}", "2": "GND", "3": f"{prefix}_OUTA", "4": f"{prefix}_OUTB"},
        )

    expect_pads(
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
        },
    )
    expect_pads(
        board,
        "U250",
        {"1": "EEPROM_CS", "2": "CAP_MISO", "4": "GND", "5": "CAP_MOSI", "6": "CAP_SCK", "8": "S1_3V3"},
    )
    expect_pads(
        board,
        "CAN1",
        {"1": "LOGIC_3V3", "2": "GND", "3": "S1_CAN_TX", "4": "S1_CAN_RX", "5": "CANH_BUS", "6": "CANL_BUS"},
    )
    expect_pads(board, "J240", {"1": "CANH_ENTRY", "2": "CANL_ENTRY", "3": "GND", "4": "GND"})
    expect_pads(board, "DC1", {"1": "LOGIC_12V_PROTECTED", "2": "GND", "3": "LOGIC_5V", "4": "GND"})
    expect_pads(board, "U230", {"1": "GND", "2": "LOGIC_3V3", "3": "S1_5V_REG"})

    reed_names = ("OPEN", "CLOSED", "IN_PLACE")
    for index, name in enumerate(reed_names, start=1):
        raw = f"REED_A_{name}_RAW_5V"
        protected = f"REED_A_{name}"
        expect_pads(board, f"J20{index}", {"1": "LOGIC_5V", "2": raw, "3": "GND"})
        expect_pads(board, f"R29{index - 1}", {"1": protected, "2": raw})

    for index in range(1, 4):
        expect_pads(board, f"J21{index}", {"1": f"CAP_C{index}_FIELD", "2": "GND"})

    # The hold-up capacitor is intentionally linked to the regulator branch by
    # a short insulated assembly wire between C280+ and J280B.
    expect_pads(board, "C280", {"1": "S1_5V_HOLD", "2": "GND"})
    expect_pads(board, "J280B", {"1": "S1_5V_REG"})

    print("PASS: four-channel F103RCT6 hardware contract verified")


if __name__ == "__main__":
    main()
