"""Route local IN_A, IN_B and PWM chains for VNH channels 5 through 8."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = PROJECT / "DOOR-8CH.kicad_pcb"
LOCK_PATH = PROJECT / "~DOOR-8CH.kicad_pcb.lck"
CHANNELS = range(5, 9)
NETS = {f"CH{channel}_{signal}" for channel in CHANNELS for signal in ("INA", "INB", "PWM")}

if LOCK_PATH.exists():
    raise SystemExit("Close DOOR-8CH in KiCad before routing channels 5-8")

board = pcbnew.LoadBoard(str(BOARD_PATH))


def point(x_mm, y_mm):
    return pcbnew.VECTOR2I_MM(x_mm, y_mm)


def pad_position(reference, pad_number):
    footprint = board.FindFootprintByReference(reference)
    pad = next(pad for pad in footprint.Pads() if pad.GetNumber() == str(pad_number))
    position = pad.GetPosition()
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def add_track(net_name, layer, start, end):
    item = pcbnew.PCB_TRACK(board)
    item.SetLayer(layer)
    item.SetNet(board.FindNet(net_name))
    item.SetWidth(pcbnew.FromMM(0.25))
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    board.Add(item)


def add_via(net_name, position):
    item = pcbnew.PCB_VIA(board)
    item.SetNet(board.FindNet(net_name))
    item.SetPosition(point(*position))
    item.SetWidth(pcbnew.FromMM(0.80))
    item.SetDrill(pcbnew.FromMM(0.35))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(item)


def route(net_name, layer, front_start, inner_points, front_end):
    add_track(net_name, pcbnew.F_Cu, front_start, inner_points[0])
    add_via(net_name, inner_points[0])
    for start, end in zip(inner_points, inner_points[1:]):
        add_track(net_name, layer, start, end)
    add_via(net_name, inner_points[-1])
    add_track(net_name, pcbnew.F_Cu, inner_points[-1], front_end)


for item in list(board.GetTracks()):
    if item.GetNetname() in NETS:
        board.Delete(item)

for channel in range(5, 8):
    ina_pin = pad_position(f"U{channel}", 4)
    pwm_pin = pad_position(f"U{channel}", 7)
    inb_pin = pad_position(f"U{channel}", 10)
    ina_resistor = pad_position(f"R{1000 + channel * 100 + 1}", 2)
    inb_resistor = pad_position(f"R{1000 + channel * 100 + 2}", 2)
    pwm_resistor = pad_position(f"R{1000 + channel * 100 + 3}", 2)

    ina_x = ina_pin[0] - 7.945
    pwm_x = pwm_pin[0] - 7.200
    inb_x = inb_pin[0] - 1.875

    route(
        f"CH{channel}_INA", pcbnew.In2_Cu, ina_pin,
        ((ina_x, 31.00), (ina_x, 70.00), (ina_resistor[0] + 1.675, 70.00), (ina_resistor[0] + 1.675, 66.00)),
        ina_resistor,
    )
    route(
        f"CH{channel}_PWM", pcbnew.In1_Cu, pwm_pin,
        ((pwm_x, 34.00), (pwm_x, 72.00), (pwm_resistor[0] + 1.675, 72.00), (pwm_resistor[0] + 1.675, 66.00)),
        pwm_resistor,
    )
    if channel == 5:
        inb_points = ((inb_x, 37.00), (inb_x, 65.20), (142.00, 65.20), (142.00, 67.50))
    else:
        inb_points = ((inb_x, 37.00), (inb_x, 65.20), (inb_resistor[0] + 1.675, 65.20))
    route(f"CH{channel}_INB", pcbnew.In2_Cu, inb_pin, inb_points, inb_resistor)

# Channel 8 sits closer to the previous channel's power vias and needs its own
# doglegs around C1801 and the CH7/CH8 fused-12 V backbone.
channel = 8
ina_pin = pad_position("U8", 4)
pwm_pin = pad_position("U8", 7)
inb_pin = pad_position("U8", 10)
ina_resistor = pad_position("R1801", 2)
inb_resistor = pad_position("R1802", 2)
pwm_resistor = pad_position("R1803", 2)

route(
    "CH8_INA", pcbnew.In2_Cu, ina_pin,
    ((226.50, 31.00), (226.50, 70.00), (ina_resistor[0] + 1.675, 70.00), (ina_resistor[0] + 1.675, 66.00)),
    ina_resistor,
)

add_track("CH8_PWM", pcbnew.F_Cu, pwm_pin, (222.00, 34.00))
add_track("CH8_PWM", pcbnew.F_Cu, (222.00, 34.00), (219.50, 30.00))
add_via("CH8_PWM", (219.50, 30.00))
for start, end in zip(
    ((219.50, 30.00), (219.50, 50.00), (214.00, 50.00), (214.00, 72.00), (pwm_resistor[0] + 1.675, 72.00)),
    ((219.50, 50.00), (214.00, 50.00), (214.00, 72.00), (pwm_resistor[0] + 1.675, 72.00), (pwm_resistor[0] + 1.675, 66.00)),
):
    add_track("CH8_PWM", pcbnew.In1_Cu, start, end)
add_via("CH8_PWM", (pwm_resistor[0] + 1.675, 66.00))
add_track("CH8_PWM", pcbnew.F_Cu, (pwm_resistor[0] + 1.675, 66.00), pwm_resistor)

add_track("CH8_INB", pcbnew.F_Cu, inb_pin, (225.50, 37.00))
add_via("CH8_INB", (225.50, 37.00))
add_track("CH8_INB", pcbnew.In2_Cu, (225.50, 37.00), (225.50, 61.50))
add_via("CH8_INB", (225.50, 61.50))
add_track("CH8_INB", pcbnew.F_Cu, (225.50, 61.50), (233.50, 61.50))
add_track("CH8_INB", pcbnew.F_Cu, (233.50, 61.50), (233.50, 63.30))
add_track("CH8_INB", pcbnew.F_Cu, (233.50, 63.30), inb_resistor)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), board)
