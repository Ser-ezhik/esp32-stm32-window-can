"""Check that the dedicated 4-channel firmware matches the PCB pin contract."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "ArduinoIDE" / "STM32_Universal_Actuator_Node_4CH_F103RC"


def require(pattern: str, text: str, description: str) -> None:
    if not re.search(pattern, text, re.MULTILINE | re.DOTALL):
        raise AssertionError(f"missing firmware contract: {description}")


def main() -> None:
    config = (FIRMWARE / "config.h").read_text(encoding="utf-8")
    can = (FIRMWARE / "BxCan.h").read_text(encoding="utf-8")
    sketch = (
        FIRMWARE / "STM32_Universal_Actuator_Node_4CH_F103RC.ino"
    ).read_text(encoding="utf-8")

    expected = {
        "CURRENT_PINS": "PA_0, PA_1, PA_2, PA_3",
        "PWM_PINS": "PA_8, PA_9, PA_10, PA_11",
        "INA_PINS": "PB_0, PB_10, PB_12, PB_14",
        "INB_PINS": "PB_1, PB_11, PB_13, PB_15",
        "DIAG_PINS": "PC_6, PC_7, PC_8, PC_9",
        "REED_PINS": "PC_0, PC_1, PC_2",
    }
    for name, pins in expected.items():
        require(
            rf"{name}\s*\[[^\]]+\]\s*=\s*\{{\s*{re.escape(pins)}\s*\}}",
            config,
            f"{name} = {pins}",
        )

    scalar_pins = {
        "CAP_CS": "PA_4",
        "CAP_IRQ": "PC_5",
        "CAP_RESET": "PC_10",
        "CABINET_EEPROM_CS": "PC_4",
        "POWER_GOOD": "PC_3",
        "CAN_RX": "PB_8",
        "CAN_TX": "PB_9",
    }
    for name, pin in scalar_pins.items():
        require(rf"{name}\s*=\s*{pin}\s*;", config, f"{name} = {pin}")

    require(r"ACTUATOR_COUNT\s*=\s*4\s*;", config, "four local actuators")
    require(r"PHYSICAL_SLAVE_COUNT\s*=\s*0\s*;", config, "no UART slaves")
    require(r"REQUIRED_LOGICAL_SLAVE_COUNT\s*=\s*1\s*;", config, "ESP32 four-actuator provisioning")
    require(r"GPIOB->CRH", can, "PB8/PB9 GPIO configuration")
    require(r"AFIO_MAPR_CAN_REMAP_1", can, "bxCAN PB8/PB9 remap")
    require(r"boardRole\s*=\s*BoardRole::Master", sketch, "fixed CAN-master role")
    require(r"__HAL_AFIO_REMAP_SWJ_NOJTAG", sketch, "SWD-only debug remap")
    require(
        r"CAN_ACTUATORS_BASE\s*\+\s*carrier\.cabinetId\s*\*\s*4u\s*\+\s*1u",
        sketch,
        "second local actuator telemetry frame",
    )
    require(
        r"request\.slaveCount\s*!=\s*hw::REQUIRED_LOGICAL_SLAVE_COUNT",
        sketch,
        "reject incompatible actuator counts",
    )
    require(
        r"request\.objectType\s*>\s*static_cast<uint8_t>\(ObjectType::SingleDoor\)",
        sketch,
        "reject unsupported double-door sensor layout",
    )

    print("PASS: dedicated 4-channel firmware matches the PCB pin contract")


if __name__ == "__main__":
    main()
