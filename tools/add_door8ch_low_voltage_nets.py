"""Add and assign DOOR-8CH low-voltage power, CAN, CAP1188, RF and UART nets."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
KICAD_FOOTPRINTS = Path(
    r"C:\Users\Ezhik\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
)

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before assigning low-voltage nets")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def get_net(name):
    item = board.FindNet(name)
    if item is None:
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
    return item


def remove(reference):
    item = board.FindFootprintByReference(reference)
    if item is not None:
        board.Delete(item)


def load(library, name):
    item = pcbnew.FootprintLoad(str(KICAD_FOOTPRINTS / library), name)
    if item is None:
        raise RuntimeError(f"Unable to load {library}/{name}")
    return item


def add(reference, value, library, name, x_mm, y_mm, rotation=0, hide_value=True):
    remove(reference)
    item = load(library, name)
    item.SetReference(reference)
    item.SetValue(value)
    item.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    item.SetOrientationDegrees(rotation)
    item.Value().SetVisible(not hide_value)
    board.Add(item)
    return item


def fp(reference):
    item = board.FindFootprintByReference(reference)
    if item is None:
        raise RuntimeError(f"Missing footprint {reference}")
    return item


def connect(reference, pads, net_name):
    item = fp(reference)
    net = get_net(net_name)
    for pad_number in pads:
        matched = False
        for pad in item.Pads():
            if pad.GetNumber() == str(pad_number):
                pad.SetNet(net)
                matched = True
        if not matched:
            raise RuntimeError(f"Missing pad {reference}.{pad_number}")


GND = "GND"
LOGIC_5V = "LOGIC_5V"
LOGIC_3V3 = "LOGIC_3V3"

# Stale references from previous iterations are rebuilt in fixed positions.
for reference in (
    "U230", "C236", "C237", "C238", "C239",
    "J240", "L240", "D240", "D241", "R240",
    "R250", "R251", "R252", "R253", "R254", "R255",
    "U250", "C250", "R260", "R261", "R262",
):
    remove(reference)

# Board-level 3.3 V rail for plug-in modules. It avoids loading or paralleling
# the small regulators on the socketed STM32 and ESP32 development boards.
add("U230", "AMS1117-3V3", "Package_TO_SOT_SMD.pretty", "SOT-223-3_TabPin2", 186, 88, 0)
add("C236", "10UF_10V_3V3_IN", "Capacitor_SMD.pretty", "C_1206_3216Metric", 178, 91, 0)
add("C237", "100NF_16V_3V3_IN", "Capacitor_SMD.pretty", "C_0603_1608Metric", 178, 86, 0)
add("C238", "10UF_10V_3V3_OUT", "Capacitor_SMD.pretty", "C_1206_3216Metric", 198, 91, 0)
add("C239", "100NF_16V_3V3_OUT", "Capacitor_SMD.pretty", "C_0603_1608Metric", 198, 86, 0)

# CAN trunk entry: CANH, CANL, GND, shield/drain. This compact group is placed
# on the lower board edge between CAN2 and MOD3: cable -> TVS -> CMC -> CAN2.
# Termination R240 is DNP by default and is populated only on the two physical
# ends of the CAN line.
add(
    "J240", "CANH_CANL_GND_SHIELD", "TerminalBlock_Phoenix.pretty",
    "TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal", 158, 152, 0,
)
add("L240", "CMC_CAN", "Inductor_SMD.pretty", "L_CommonModeChoke_Coilcraft_1812CAN", 158, 143, 0)
add("D240", "PESD1CAN_CANH", "Diode_SMD.pretty", "D_SOD-323", 147, 140, 90)
add("D241", "PESD1CAN_CANL", "Diode_SMD.pretty", "D_SOD-323", 169, 140, 90)
add("R240", "120R_CAN_TERM_DNP", "Resistor_SMD.pretty", "R_1206_3216Metric", 158, 135, 0)
for reference in ("L240", "D240", "D241", "R240"):
    fp(reference).Reference().SetVisible(False)

# Internal UART series resistors, one at each transmitter.
for index, (reference, x_mm, y_mm) in enumerate((
    ("R250", 74, 118), ("R251", 78, 118),
    ("R252", 104, 118), ("R253", 108, 118),
    ("R254", 134, 118), ("R255", 138, 118),
)):
    item = add(reference, "100R_UART_TX", "Resistor_SMD.pretty", "R_0603_1608Metric", x_mm, y_mm, 0)
    item.Reference().SetVisible(False)

# Protected MP1584 input and output.
connect("J230", (1,), "LOGIC_12V_IN")
connect("J230", (2,), GND)
connect("F230", (1,), "LOGIC_12V_IN")
connect("F230", (2,), "LOGIC_12V_FUSED")
connect("D230", (1,), "LOGIC_12V_FUSED")
connect("D230", (2,), "LOGIC_12V_PROTECTED")
connect("D231", (1,), "LOGIC_12V_PROTECTED")
connect("D231", (2,), GND)
for reference in ("C230", "C231", "C232"):
    connect(reference, (1,), "LOGIC_12V_PROTECTED")
    connect(reference, (2,), GND)
connect("DC1", (1,), "LOGIC_12V_PROTECTED")
connect("DC1", (2,), GND)
connect("DC1", (3,), LOGIC_5V)
connect("DC1", (4,), GND)
for reference in ("C233", "C234", "C235"):
    connect(reference, (1,), LOGIC_5V)
    connect(reference, (2,), GND)

# AMS1117-3.3 V regulator: pin 1 GND, pin 2/tab OUT, pin 3 IN.
connect("U230", (1,), GND)
connect("U230", (2,), LOGIC_3V3)
connect("U230", (3,), LOGIC_5V)
for reference in ("C236", "C237"):
    connect(reference, (1,), LOGIC_5V)
    connect(reference, (2,), GND)
for reference in ("C238", "C239"):
    connect(reference, (1,), LOGIC_3V3)
    connect(reference, (2,), GND)

# S1 service header: 3V3, SWDIO, SWCLK, NRST, GND.
connect("J220", (1,), "S1_3V3")
connect("J220", (2,), "S1_SWDIO")
connect("J220", (3,), "S1_SWCLK")
connect("J220", (4,), "S1_NRST")
connect("J220", (5,), GND)
connect("MOD1", (34,), "S1_SWDIO")
connect("MOD1", (25,), "S1_SWCLK")
connect("MOD1", (16,), "S1_NRST")

# CAN: photographed SN65HVD230 module order is 3V3, GND, CTX, CRX, CANH, CANL.
connect("J240", (1,), "CANH_ENTRY")
connect("J240", (2,), "CANL_ENTRY")
connect("J240", (3, 4), GND)
connect("L240", (1,), "CANH_ENTRY")
connect("L240", (2,), "CANL_ENTRY")
connect("L240", (4,), "CANH_BUS")
connect("L240", (3,), "CANL_BUS")
# TVS parts are deliberately on the connector side of the common-mode choke,
# with the shortest practical return path to the local GND plane.
connect("D240", (1,), "CANH_ENTRY")
connect("D240", (2,), GND)
connect("D241", (1,), "CANL_ENTRY")
connect("D241", (2,), GND)
connect("R240", (1,), "CANH_BUS")
connect("R240", (2,), "CANL_BUS")
for reference in ("CAN1", "CAN2"):
    connect(reference, (1,), LOGIC_3V3)
    connect(reference, (2,), GND)
    connect(reference, (5,), "CANH_BUS")
    connect(reference, (6,), "CANL_BUS")
connect("CAN1", (3,), "S1_CAN_TX")
connect("CAN1", (4,), "S1_CAN_RX")
connect("MOD1", (24,), "S1_CAN_TX")
connect("MOD1", (33,), "S1_CAN_RX")

# ESP32-S3 board power and optional CAN. ESP 3V3 pins are intentionally left
# unconnected to avoid tying its onboard regulator to the carrier regulator.
connect("ESP1", (21,), LOGIC_5V)
connect("ESP1", (22, 23, 24, 44), GND)
connect("ESP1", (36,), "ESP_CAN_TX_GPIO39")
connect("ESP1", (35,), "ESP_CAN_RX_GPIO38")
connect("CAN2", (3,), "ESP_CAN_TX_GPIO39")
connect("CAN2", (4,), "ESP_CAN_RX_GPIO38")

# CC1101 module from the supplied pin table:
# 1 GDO0, 2 3V3, 3 CSN, 4 GND, 5 SCK, 6 MOSI, 7 MISO/GDO1, 8 GDO2.
connect("RF1", (1,), "RF_GDO0")
connect("RF1", (2,), LOGIC_3V3)
connect("RF1", (3,), "RF_CSN")
connect("RF1", (4,), GND)
connect("RF1", (5,), "RF_SCK")
connect("RF1", (6,), "RF_MOSI")
connect("RF1", (7,), "RF_MISO")
connect("RF1", (8,), "RF_GDO2")
for pad, net in (
    (4, "RF_GDO0"), (5, "RF_GDO2"), (16, "RF_CSN"), (17, "RF_MOSI"),
    (18, "RF_SCK"), (19, "RF_MISO"), (15, "RF_LEARN_BUTTON_GPIO9"),
):
    connect("ESP1", (pad,), net)

# External SPI EEPROM on the carrier stores the cabinet identity. This is what
# makes the socketed STM32 modules field-replaceable without per-slot firmware.
add("U250", "25LC256_SOIC8_CARRIER_ID", "Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm", 82, 132, 0)
add("C250", "100NF_EEPROM", "Capacitor_SMD.pretty", "C_0603_1608Metric", 88, 128, 0)
add("R260", "10K_EEPROM_CS_PULLUP", "Resistor_SMD.pretty", "R_0603_1608Metric", 88, 132, 90)
add("R261", "10K_EEPROM_WP_PULLUP", "Resistor_SMD.pretty", "R_0603_1608Metric", 88, 136, 90)
add("R262", "10K_EEPROM_HOLD_PULLUP", "Resistor_SMD.pretty", "R_0603_1608Metric", 88, 140, 90)
connect("U250", (1,), "EEPROM_CS")
connect("U250", (2,), "CAP_MISO")
connect("U250", (3,), "EEPROM_WP")
connect("U250", (4,), GND)
connect("U250", (5,), "CAP_MOSI")
connect("U250", (6,), "CAP_SCK")
connect("U250", (7,), "EEPROM_HOLD")
connect("U250", (8,), LOGIC_3V3)
connect("C250", (1,), LOGIC_3V3)
connect("C250", (2,), GND)
connect("R260", (1,), "EEPROM_CS")
connect("R260", (2,), LOGIC_3V3)
connect("R261", (1,), "EEPROM_WP")
connect("R261", (2,), LOGIC_3V3)
connect("R262", (1,), "EEPROM_HOLD")
connect("R262", (2,), LOGIC_3V3)
connect("MOD1", (35,), "EEPROM_CS")

# CAP1188 SPI breakout matching the supplied photo. The controller and STM32
# both use 3.3 V logic, so VIN is intentionally supplied from the 3.3 V rail;
# 3Vo remains an unused local breakout output.
connect("CAP1", (1,), "CAP_MISO")
connect("CAP1", (2,), "CAP_SCK")
connect("CAP1", (3,), LOGIC_3V3)
connect("CAP1", (4,), GND)
connect("CAP1", (14,), "CAP_MOSI")
connect("CAP1", (15,), "CAP_CS")
connect("CAP1", (16,), "CAP_RESET")
connect("CAP1", (26,), GND)  # AD low, stable default address if I2C is ever tested.
connect("MOD1", (18,), "CAP_CS")
connect("MOD1", (8,), "CAP_SCK")
connect("MOD1", (17,), "CAP_MISO")
connect("MOD1", (7,), "CAP_MOSI")
connect("MOD1", (29,), "CAP_RESET")
connect("MOD1", (13,), "CAP_IRQ")
connect("R209", (1,), "CAP_RESET")
connect("R209", (2,), GND)
connect("R210", (1,), "CAP_IRQ")
connect("R210", (2,), "S1_3V3")
for channel in range(1, 9):
    cap_pin = 17 + channel
    raw = f"CAP_C{channel}_RAW"
    field = f"CAP_C{channel}_FIELD"
    connect("CAP1", (cap_pin,), raw)
    connect(f"R{200 + channel}", (1,), raw)
    connect(f"R{200 + channel}", (2,), field)
    connect(f"J{210 + channel}", (1,), field)
    connect(f"J{210 + channel}", (2,), GND)

# Reed sensors: first leaf on S1, second leaf on S2 for the double-door build.
reed_map = (
    ("J201", "S1_3V3", "REED_A_OPEN", "MOD1", 6),
    ("J202", "S1_3V3", "REED_A_CLOSED", "MOD1", 5),
    ("J203", "S1_3V3", "REED_A_IN_PLACE", "MOD1", 38),
    ("J204", "S2_3V3", "REED_B_OPEN", "MOD2", 6),
    ("J205", "S2_3V3", "REED_B_CLOSED", "MOD2", 5),
    ("J206", "S2_3V3", "REED_B_IN_PLACE", "MOD2", 38),
)
for connector, rail, signal, module, module_pad in reed_map:
    connect(connector, (1,), rail)
    connect(connector, (2,), signal)
    connect(connector, (3,), GND)
    connect(module, (module_pad,), signal)

# Internal point-to-point UART links. HardwareSerial(rx, tx) in firmware:
# S1 UART1 PB7/PB6 to S2 PB7/PB6, S1 UART2 PA3/PA2 to S3, S1 UART3 PB11/PB10 to S4.
uart_links = (
    ("MOD1", 37, "R250", "S1_UART1_TX", "S2_UART_RX", "MOD2", 28),
    ("MOD2", 37, "R251", "S2_UART_TX", "S1_UART1_RX", "MOD1", 28),
    ("MOD1", 19, "R252", "S1_UART2_TX", "S3_UART_RX", "MOD3", 28),
    ("MOD3", 37, "R253", "S3_UART_TX", "S1_UART2_RX", "MOD1", 9),
    ("MOD1", 4, "R254", "S1_UART3_TX", "S4_UART_RX", "MOD4", 28),
    ("MOD4", 37, "R255", "S4_UART_TX", "S1_UART3_RX", "MOD1", 14),
)
for tx_module, tx_pad, resistor, tx_net, rx_net, rx_module, rx_pad in uart_links:
    connect(tx_module, (tx_pad,), tx_net)
    connect(resistor, (1,), tx_net)
    connect(resistor, (2,), rx_net)
    connect(rx_module, (rx_pad,), rx_net)

pcbnew.SaveBoard(str(BOARD_PATH), board)
