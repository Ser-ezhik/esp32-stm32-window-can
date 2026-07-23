"""Verify UNIVERSAL-2CH socket nets against the STM32 universal firmware."""

from pathlib import Path
import re
import sys

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "UNIVERSAL-2CH" / "kicad" / "UNIVERSAL-2CH.kicad_pcb"
CONFIG = ROOT / "ArduinoIDE" / "STM32_Universal_Actuator_Node" / "config.h"
SKETCH = (
    ROOT
    / "ArduinoIDE"
    / "STM32_Universal_Actuator_Node"
    / "STM32_Universal_Actuator_Node.ino"
)

ARRAY_PINS = {
    "CURRENT_PINS": ("PA_0", "PA_1"),
    "PWM_PINS": ("PA_8", "PA_9"),
    "INA_PINS": ("PB_14", "PB_3"),
    "INB_PINS": ("PB_15", "PB_4"),
    "DIAG_PINS": ("PB_5", "PB_12"),
    "REED_PINS": ("PB_0", "PB_1", "PB_8"),
}

SCALAR_PINS = {
    "SLOT_ID0": "PB_2",
    "SLOT_ID1": "PA_7",
    "CAP_CS": "PA_4",
    "CAP_IRQ": "PB_13",
    "CAP_RESET": "PB_9",
    "CABINET_EEPROM_CS": "PA_15",
    "POWER_GOOD": "PC_13",
    "CAN_RX": "PA_11",
    "CAN_TX": "PA_12",
}

SOCKET_NETS = {
    "20": "CH1_CURRENT_ADC",
    "10": "CH2_CURRENT_ADC",
    "22": "CH1_PWM_MCU",
    "32": "CH2_PWM_MCU",
    "2": "CH1_INA_MCU",
    "26": "CH2_INA_MCU",
    "12": "CH1_INB_MCU",
    "36": "CH2_INB_MCU",
    "27": "CH1_DIAG",
    "3": "CH2_DIAG",
    "6": "REED_A_OPEN",
    "5": "REED_A_CLOSED",
    "38": "REED_A_IN_PLACE",
    "18": "CAP_CS",
    "8": "CAP_SCK",
    "17": "CAP_MISO",
    "7": "CAP_MOSI",
    "13": "CAP_IRQ",
    "29": "CAP_RESET",
    "35": "EEPROM_CS",
    "30": "POWER_GOOD",
    "33": "S1_CAN_RX",
    "24": "S1_CAN_TX",
    "15": "S1_SLOT_ID0",
    "34": "S1_SWDIO",
    "25": "S1_SWCLK",
    "16": "S1_NRST",
}


def main():
    config = CONFIG.read_text(encoding="utf-8")
    sketch = SKETCH.read_text(encoding="utf-8")
    failures = []

    for name, expected in ARRAY_PINS.items():
        match = re.search(rf"{name}[^=]*=\s*\{{([^}}]+)\}}", config)
        actual = tuple(part.strip() for part in match.group(1).split(",")) if match else ()
        if actual != expected:
            failures.append(f"config.h {name}: {actual} != {expected}")

    for name, expected in SCALAR_PINS.items():
        if not re.search(rf"\b{name}\s*=\s*{expected}\s*;", config):
            failures.append(f"config.h {name} is not {expected}")

    board = pcbnew.LoadBoard(str(BOARD))
    socket = board.FindFootprintByReference("MOD1")
    actual_nets = {pad.GetNumber(): pad.GetNetname() for pad in socket.Pads()}
    for number, expected in SOCKET_NETS.items():
        if actual_nets.get(number) != expected:
            failures.append(
                f"MOD1 pad {number}: {actual_nets.get(number)!r} != {expected!r}"
            )

    if "__HAL_AFIO_REMAP_SWJ_NOJTAG();" not in sketch:
        failures.append("JTAG is not disabled while SWD is retained")
    if "CURRENT_MA_PER_ADC_COUNT_NUM = 57;" not in config:
        failures.append("current-sense numerator is not the 5.7 mA/count baseline")
    if "CURRENT_MA_PER_ADC_COUNT_DEN = 10;" not in config:
        failures.append("current-sense denominator is not the 5.7 mA/count baseline")

    if failures:
        print("FAILED:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1

    print("OK: UNIVERSAL-2CH socket nets match STM32 firmware pins")
    print(f"OK: checked {len(SOCKET_NETS)} functional socket connections")
    print("OK: JTAG release and 5.7 mA/count current baseline are present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
