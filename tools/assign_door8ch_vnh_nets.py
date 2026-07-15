"""Assign VNH5019 channel nets and hardware slot straps on DOOR-8CH."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
KICAD_FP = Path(
    r"C:\Users\Ezhik\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
)

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before assigning nets")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def get_footprint(reference):
    item = board.FindFootprintByReference(reference)
    if item is None:
        raise RuntimeError(f"Missing footprint {reference}")
    return item


def get_net(name):
    item = board.FindNet(name)
    if item is None:
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
    return item


def connect(reference, pad_numbers, net_name):
    item = get_footprint(reference)
    target_net = get_net(net_name)
    for number in pad_numbers:
        pad = item.FindPadByNumber(str(number))
        if pad is None:
            raise RuntimeError(f"Missing pad {reference}.{number}")
        pad.SetNet(target_net)


def add_strap(reference, value, x_mm, y_mm):
    item = board.FindFootprintByReference(reference)
    if item is None:
        item = pcbnew.FootprintLoad(
            str(KICAD_FP / "Resistor_SMD.pretty"), "R_0603_1608Metric"
        )
        if item is None:
            raise RuntimeError("Unable to load slot-strap footprint")
        item.SetReference(reference)
        board.Add(item)
    item.SetValue(value)
    item.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    item.Reference().SetVisible(False)
    item.Value().SetVisible(False)


GND = "GND"
LOGIC_5V = "LOGIC_5V"
channel_to_mcu_pads = {
    0: {"ADC": 20, "PWM": 22, "INA": 2, "INB": 12, "DIAG": 27},
    1: {"ADC": 10, "PWM": 32, "INA": 26, "INB": 36, "DIAG": 3},
}

for slot in range(1, 5):
    module = f"MOD{slot}"
    local_3v3 = f"S{slot}_3V3"
    connect(module, (1, 31), GND)
    connect(module, (21,), LOGIC_5V)
    connect(module, (11,), local_3v3)

    center_x = (45, 105, 165, 207)[slot - 1]
    strap_values = (
        ("47K", "47K"),
        ("0R", "47K"),
        ("47K", "0R"),
        ("0R", "0R"),
    )[slot - 1]
    for bit, (module_pad, dx, value) in enumerate(
        ((15, -2, strap_values[0]), (7, 2, strap_values[1]))
    ):
        reference = f"R{3000 + slot * 10 + bit + 1}"
        add_strap(reference, f"{value} SLOT_S{slot}_ID{bit}", center_x + dx, 120)
        id_net = f"S{slot}_SLOT_ID{bit}"
        connect(module, (module_pad,), id_net)
        connect(reference, (1,), id_net)
        connect(reference, (2,), GND if value == "0R" else local_3v3)

for channel in range(1, 9):
    slot = (channel - 1) // 2 + 1
    half = (channel - 1) % 2
    module = f"MOD{slot}"
    mcu_pads = channel_to_mcu_pads[half]
    local_3v3 = f"S{slot}_3V3"
    base = 1000 + channel * 100

    fused_12v = f"FUSED_12V_CH{channel}"
    out_a = f"CH{channel}_OUTA"
    out_b = f"CH{channel}_OUTB"
    ina_mcu = f"CH{channel}_INA_MCU"
    inb_mcu = f"CH{channel}_INB_MCU"
    pwm_mcu = f"CH{channel}_PWM_MCU"
    ina = f"CH{channel}_INA"
    inb = f"CH{channel}_INB"
    pwm = f"CH{channel}_PWM"
    diag = f"CH{channel}_DIAG"
    cs_dis = f"CH{channel}_CS_DIS"
    cs_raw = f"CH{channel}_CS_RAW"
    adc = f"CH{channel}_CURRENT_ADC"

    connect(f"J{channel}", (1,), fused_12v)
    connect(f"J{channel}", (2,), GND)
    connect(f"J{channel + 8}", (1,), out_a)
    connect(f"J{channel + 8}", (2,), out_b)

    connect(f"U{channel}", (3, 12, 13, 23), fused_12v)
    connect(f"U{channel}", (18, 19, 20, 26, 27, 28), GND)
    connect(f"U{channel}", (1, 25, 30), out_a)
    connect(f"U{channel}", (15, 16, 21), out_b)
    connect(f"U{channel}", (4,), ina)
    connect(f"U{channel}", (10,), inb)
    connect(f"U{channel}", (7,), pwm)
    connect(f"U{channel}", (5, 9), diag)
    connect(f"U{channel}", (6,), cs_dis)
    connect(f"U{channel}", (8,), cs_raw)

    connect(module, (mcu_pads["INA"],), ina_mcu)
    connect(module, (mcu_pads["INB"],), inb_mcu)
    connect(module, (mcu_pads["PWM"],), pwm_mcu)
    connect(module, (mcu_pads["DIAG"],), diag)
    connect(module, (mcu_pads["ADC"],), adc)

    for reference, pad1_net, pad2_net in (
        (f"R{base + 1}", ina_mcu, ina),
        (f"R{base + 2}", inb_mcu, inb),
        (f"R{base + 3}", pwm_mcu, pwm),
        (f"R{base + 4}", ina, GND),
        (f"R{base + 5}", inb, GND),
        (f"R{base + 6}", pwm, GND),
        (f"R{base + 7}", diag, local_3v3),
        (f"R{base + 8}", cs_dis, GND),
        (f"R{base + 9}", cs_raw, GND),
        (f"R{base + 10}", cs_raw, adc),
    ):
        connect(reference, (1,), pad1_net)
        connect(reference, (2,), pad2_net)

    connect(f"C{base + 1}", (1,), fused_12v)
    connect(f"C{base + 1}", (2,), GND)
    connect(f"C{base + 2}", (1,), fused_12v)
    connect(f"C{base + 2}", (2,), GND)
    connect(f"C{base + 3}", (1,), adc)
    connect(f"C{base + 3}", (2,), GND)
    connect(f"D{base + 1}", (1,), GND)
    connect(f"D{base + 1}", (2,), local_3v3)
    connect(f"D{base + 1}", (3,), adc)

pcbnew.SaveBoard(str(BOARD_PATH), board)
