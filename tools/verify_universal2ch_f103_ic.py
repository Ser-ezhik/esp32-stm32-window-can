"""Audit the direct-IC 2-channel PCB against firmware and required support nets."""

from pathlib import Path
import re
import sys

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware/UNIVERSAL-2CH-F103-IC/kicad/UNIVERSAL-2CH-F103-IC.kicad_pcb"
CONFIG = ROOT / "ArduinoIDE/STM32_Universal_Actuator_Node/config.h"
SKETCH = ROOT / "ArduinoIDE/STM32_Universal_Actuator_Node/STM32_Universal_Actuator_Node.ino"
CAP_DRIVER = ROOT / "ArduinoIDE/STM32_Universal_Actuator_Node/Cap1188Spi.h"


STM32_NETS = {
    "1": "S1_3V3", "2": "POWER_GOOD", "5": "MCU_HSE_IN", "6": "MCU_HSE_OUT",
    "7": "S1_NRST", "8": "GND", "9": "S1_3V3", "10": "CH1_CURRENT_ADC",
    "11": "CH2_CURRENT_ADC", "14": "CAP_CS", "15": "CAP_SCK", "16": "CAP_MISO",
    "17": "CAP_MOSI", "18": "REED_A_OPEN", "19": "REED_A_CLOSED", "20": "MCU_BOOT1",
    "23": "GND", "24": "S1_3V3", "25": "CH2_DIAG", "26": "CAP_IRQ",
    "27": "CH1_INA_MCU", "28": "CH1_INB_MCU", "29": "CH1_PWM_MCU",
    "30": "CH2_PWM_MCU", "32": "S1_CAN_RX", "33": "S1_CAN_TX", "34": "S1_SWDIO",
    "35": "GND", "36": "S1_3V3", "37": "S1_SWCLK", "38": "EEPROM_CS",
    "39": "CH2_INA_MCU", "40": "CH2_INB_MCU", "41": "CH1_DIAG",
    "44": "MCU_BOOT0", "45": "REED_A_IN_PLACE", "46": "CAP_RESET", "47": "GND",
    "48": "S1_3V3",
}

CONFIG_ARRAYS = {
    "CURRENT_PINS": ("PA_0", "PA_1"), "PWM_PINS": ("PA_8", "PA_9"),
    "INA_PINS": ("PB_14", "PB_3"), "INB_PINS": ("PB_15", "PB_4"),
    "DIAG_PINS": ("PB_5", "PB_12"), "REED_PINS": ("PB_0", "PB_1", "PB_8"),
}

CONFIG_SCALARS = {
    "SLOT_ID0": "PB_2", "SLOT_ID1": "PA_7", "CAP_CS": "PA_4",
    "CAP_IRQ": "PB_13", "CAP_RESET": "PB_9", "CABINET_EEPROM_CS": "PA_15",
    "POWER_GOOD": "PC_13", "CAN_RX": "PA_11", "CAN_TX": "PA_12",
}


def pads(board, reference):
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        return None
    result = {}
    for item in footprint.Pads():
        result.setdefault(item.GetNumber(), set()).add(item.GetNetname())
    return result


def expect_pads(board, failures, reference, expected):
    actual = pads(board, reference)
    if actual is None:
        failures.append(f"missing footprint {reference}")
        return
    for number, net_name in expected.items():
        if net_name not in actual.get(str(number), set()):
            failures.append(f"{reference}.{number}: {actual.get(str(number))} != {net_name}")


def expect_value(board, failures, reference, pattern):
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        failures.append(f"missing footprint {reference}")
    elif not re.search(pattern, footprint.GetValue(), re.IGNORECASE):
        failures.append(f"{reference} value {footprint.GetValue()!r} does not match {pattern!r}")


def main():
    failures = []
    config = CONFIG.read_text(encoding="utf-8")
    sketch = SKETCH.read_text(encoding="utf-8")
    cap_driver = CAP_DRIVER.read_text(encoding="utf-8")
    board = pcbnew.LoadBoard(str(BOARD))

    for name, expected in CONFIG_ARRAYS.items():
        match = re.search(rf"{name}[^=]*=\s*\{{([^}}]+)\}}", config)
        actual = tuple(part.strip() for part in match.group(1).split(",")) if match else ()
        if actual != expected:
            failures.append(f"config {name}: {actual} != {expected}")
    for name, expected in CONFIG_SCALARS.items():
        if not re.search(rf"\b{name}\s*=\s*{expected}\s*;", config):
            failures.append(f"config {name} is not {expected}")

    expect_pads(board, failures, "U300", STM32_NETS)
    if board.FindFootprintByReference("R3003") is not None:
        failures.append("R3003 must be absent: PB2 internal pull-up selects Master")

    expect_pads(board, failures, "D230", {"1": "LOGIC_12V_PROTECTED", "2": "LOGIC_12V_FUSED"})
    expect_pads(board, failures, "D280", {"1": "S1_5V_HOLD", "2": "LOGIC_5V"})
    expect_pads(board, failures, "C280", {"1": "S1_5V_HOLD", "2": "GND"})
    expect_pads(board, failures, "U230", {"1": "GND", "2": "LOGIC_3V3", "3": "S1_5V_REG"})
    expect_pads(board, failures, "R2301", {"1": "LOGIC_3V3", "2": "S1_3V3"})
    expect_pads(board, failures, "J280B", {"1": "S1_5V_REG"})
    expect_value(board, failures, "R2301", r"0R")
    expect_value(board, failures, "C280", r"4700UF")

    for channel, prefix in ((1, "CH1"), (2, "CH2")):
        expect_pads(board, failures, f"U{channel}", {
            "1": f"{prefix}_OUTA", "3": f"FUSED_12V_{prefix}", "4": f"{prefix}_INA",
            "5": f"{prefix}_DIAG", "6": f"{prefix}_CS_DIS", "7": f"{prefix}_PWM",
            "8": f"{prefix}_CS_RAW", "9": f"{prefix}_DIAG", "10": f"{prefix}_INB",
            "12": f"FUSED_12V_{prefix}", "13": f"FUSED_12V_{prefix}",
            "15": f"{prefix}_OUTB", "18": "GND", "19": "GND", "20": "GND",
            "21": f"{prefix}_OUTB", "23": f"FUSED_12V_{prefix}", "25": f"{prefix}_OUTA",
            "26": "GND", "27": "GND", "28": "GND", "30": f"{prefix}_OUTA",
            "31": f"FUSED_12V_{prefix}", "32": f"{prefix}_OUTB", "33": f"{prefix}_OUTA",
        })
        base = 1100 if channel == 1 else 1200
        expect_value(board, failures, f"R{base + 8}", r"10K.*CS_DIS")
        expect_value(board, failures, f"R{base + 9}", r"1K")
        expect_value(board, failures, f"R{base + 10}", r"10K.*ADC")
        expect_value(board, failures, f"C{base + 3}", r"100n")

    expect_pads(board, failures, "CAP1", {
        "1": "CAP_CS", "2": "CAP_MOSI", "3": "CAP_MISO", "4": "CAP_SCK",
        "5": "GND", "6": "GND", "7": "GND", "8": "GND", "9": "GND",
        "10": "GND", "11": "GND", "12": "GND", "13": "CAP_IRQ", "14": "GND",
        "15": "GND", "16": "GND", "17": "GND", "18": "GND", "19": "GND",
        "20": "CAP_C3_RAW", "21": "CAP_C2_RAW",
        "22": "CAP_C1_RAW", "23": "S1_3V3", "24": "CAP_RESET", "25": "GND",
    })
    expect_value(board, failures, "R209", r"10K")
    expect_value(board, failures, "R210", r"10K")
    expect_pads(board, failures, "U250", {
        "1": "EEPROM_CS", "2": "CAP_MISO", "3": "EEPROM_WP", "4": "GND",
        "5": "CAP_MOSI", "6": "CAP_SCK", "7": "EEPROM_HOLD", "8": "S1_3V3",
    })
    expect_pads(board, failures, "U270", {
        "1": "POWER_GOOD", "2": "GND", "3": "PGOOD_SENSE", "4": "GND",
        "5": "LOGIC_12V_FUSED", "6": "POWER_GOOD",
    })
    expect_value(board, failures, "R270", r"226K")
    expect_value(board, failures, "R271", r"10K")

    if "__HAL_AFIO_REMAP_SWJ_NOJTAG();" not in sketch:
        failures.append("firmware does not release JTAG pins while retaining SWD")
    if "CURRENT_MA_PER_ADC_COUNT_NUM = 57;" not in config or "CURRENT_MA_PER_ADC_COUNT_DEN = 10;" not in config:
        failures.append("firmware current baseline is not 5.7 mA/count")
    if "pinMode(hw::SLOT_ID0, INPUT_PULLUP);" not in sketch:
        failures.append("firmware does not pull PB2 high for Master role")
    if not re.search(r"pinMode\(cs_, OUTPUT\);\s*digitalWrite\(cs_, HIGH\);", cap_driver):
        failures.append("CAP1188 chip-select is not driven inactive before SPI startup")
    if "SPISettings(1000000, MSBFIRST, SPI_MODE3)" not in cap_driver:
        failures.append("CAP1188 SPI mode/speed differs from the audited interface")

    if failures:
        print("FAILED:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1

    print("OK: direct-IC PCB pinout matches STM32 universal firmware")
    print("OK: VNH5019, CAP1188, EEPROM, CAN/power-good and power rails audited")
    print("OK: current baseline 5.7 mA/count, JTAG release and Master role verified")
    print("REQUIRED ASSEMBLY LINK: insulated wire C280+ -> J280B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
