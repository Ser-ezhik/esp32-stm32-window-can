"""Check WINDOW-4CH STM32 socket nets against the universal firmware pinout."""

from pathlib import Path
import re
import sys

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "WINDOW-4CH" / "kicad" / "WINDOW-4CH.kicad_pcb"
CONFIG = ROOT / "ArduinoIDE" / "STM32_Universal_Actuator_Node" / "config.h"

FIRMWARE_PINS = {
    "CURRENT_PINS": ("PA_0", "PA_1"),
    "PWM_PINS": ("PA_8", "PA_9"),
    "INA_PINS": ("PB_14", "PB_3"),
    "INB_PINS": ("PB_15", "PB_4"),
    "DIAG_PINS": ("PB_5", "PB_12"),
    "REED_PINS": ("PB_0", "PB_1", "PB_8"),
}

SOCKET_NETS = {
    "MOD1": {
        "20": "CH1_CURRENT_ADC", "10": "CH2_CURRENT_ADC",
        "22": "CH1_PWM_MCU", "32": "CH2_PWM_MCU",
        "2": "CH1_INA_MCU", "26": "CH2_INA_MCU",
        "12": "CH1_INB_MCU", "36": "CH2_INB_MCU",
        "27": "CH1_DIAG", "3": "CH2_DIAG",
        "6": "REED_A_OPEN", "5": "REED_A_CLOSED", "38": "REED_A_IN_PLACE",
        "18": "CAP_CS", "8": "CAP_SCK", "17": "CAP_MISO", "7": "CAP_MOSI",
        "13": "CAP_IRQ", "29": "CAP_RESET", "35": "EEPROM_CS",
        "30": "POWER_GOOD", "33": "S1_CAN_RX", "24": "S1_CAN_TX",
        "28": "S1_UART1_RX", "37": "S1_UART1_TX",
    },
    "MOD2": {
        "20": "CH3_CURRENT_ADC", "10": "CH4_CURRENT_ADC",
        "22": "CH3_PWM_MCU", "32": "CH4_PWM_MCU",
        "2": "CH3_INA_MCU", "26": "CH4_INA_MCU",
        "12": "CH3_INB_MCU", "36": "CH4_INB_MCU",
        "27": "CH3_DIAG", "3": "CH4_DIAG",
        "28": "S2_UART_RX", "37": "S2_UART_TX",
        "15": "S2_SLOT_ID0", "7": "S2_SLOT_ID1",
    },
}

SCALAR_PINS = {
    "CAP_CS": "PA_4", "CAP_IRQ": "PB_13", "CAP_RESET": "PB_9",
    "CABINET_EEPROM_CS": "PA_15", "POWER_GOOD": "PC_13",
    "CAN_RX": "PA_11", "CAN_TX": "PA_12",
    "UART1_RX": "PB_7", "UART1_TX": "PB_6",
    "SLOT_ID0": "PB_2", "SLOT_ID1": "PA_7",
}


def main():
    config = CONFIG.read_text(encoding="utf-8")
    failures = []
    for name, pins in FIRMWARE_PINS.items():
        match = re.search(rf"{name}[^=]*=\s*\{{([^}}]+)\}}", config)
        actual = tuple(part.strip() for part in match.group(1).split(",")) if match else ()
        if actual != pins:
            failures.append(f"config.h {name}: {actual} != {pins}")
    for name, pin in SCALAR_PINS.items():
        if not re.search(rf"\b{name}\s*=\s*{pin}\s*;", config):
            failures.append(f"config.h {name} is not {pin}")

    board = pcbnew.LoadBoard(str(BOARD))
    for reference, expected in SOCKET_NETS.items():
        footprint = board.FindFootprintByReference(reference)
        actual = {pad.GetNumber(): pad.GetNetname() for pad in footprint.Pads()}
        for number, net in expected.items():
            if actual.get(number) != net:
                failures.append(f"{reference} pad {number}: {actual.get(number)!r} != {net!r}")

    if failures:
        print("FAILED:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("OK: universal firmware pin constants match WINDOW-4CH S1/S2 socket nets")
    print(f"OK: checked {sum(len(nets) for nets in SOCKET_NETS.values())} socket connections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
