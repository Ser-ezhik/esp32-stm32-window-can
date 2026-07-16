"""Generate flat and multisheet KiCad schematics from the routed DOOR-8CH PCB."""

from __future__ import annotations

import copy
import os
import re
import sys
import uuid
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "tools" / "_vendor" / "kiutils_runtime"
sys.path.insert(0, str(VENDOR))

import pcbnew
from kiutils.items.common import ColorRGBA, Effects, Fill, Font, PageSettings, Position, Property, Stroke
from kiutils.items.schitems import (
    GlobalLabel,
    HierarchicalSheet,
    HierarchicalSheetProjectInstance,
    HierarchicalSheetProjectPath,
    LocalLabel,
    NoConnect,
    SchematicSymbol,
    SymbolInstance,
    Text,
)
from kiutils.items.syitems import SyRect
from kiutils.schematic import Schematic
from kiutils.symbol import Symbol, SymbolLib, SymbolPin


PROJECT = ROOT / "hardware" / "DOOR-8CH" / "kicad"
BOARD_PATH = Path(os.environ.get("BOARD_PATH", PROJECT / "DOOR-8CH.kicad_pcb"))
FLAT_PATH = PROJECT / "DOOR-8CH.kicad_sch"
MULTISHEET_PATH = PROJECT / "DOOR-8CH-multisheet.kicad_sch"
SYMBOL_LIBRARY_PATH = PROJECT / "DOOR-8CH-generated.kicad_sym"

GRID = 1.27
PIN_PITCH = 2.54
PIN_LENGTH = 2.54
BODY_HALF_WIDTH = 5.08

GROUP_ORDER = (
    "POWER",
    "CONTROL / CAN",
    "CAP1188",
    "REEDS",
    "CHANNEL 1",
    "CHANNEL 2",
    "CHANNEL 3",
    "CHANNEL 4",
    "CHANNEL 5",
    "CHANNEL 6",
    "CHANNEL 7",
    "CHANNEL 8",
    "OTHER / MECHANICAL",
)

GROUP_FILES = {
    "POWER": "DOOR-8CH-power.kicad_sch",
    "CONTROL / CAN": "DOOR-8CH-control-can.kicad_sch",
    "CAP1188": "DOOR-8CH-cap1188.kicad_sch",
    "REEDS": "DOOR-8CH-reeds.kicad_sch",
    **{f"CHANNEL {n}": f"DOOR-8CH-channel-{n}.kicad_sch" for n in range(1, 9)},
    "OTHER / MECHANICAL": "DOOR-8CH-other.kicad_sch",
}


def uid():
    return str(uuid.uuid4())


def snap(value):
    return round(round(value / GRID) * GRID, 3)


def natural_key(value):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


def text_effect(size=1.0, hidden=False):
    return Effects(font=Font(width=size, height=size), hide=hidden)


def pad_map(footprint):
    result = {}
    for pad in footprint.Pads():
        number = str(pad.GetNumber())
        if not number:
            continue
        net_name = pad.GetNetname() or ""
        if number in result and result[number] != net_name:
            raise RuntimeError(
                f"{footprint.GetReference()} pad {number} has conflicting nets: "
                f"{result[number]} and {net_name}"
            )
        result[number] = net_name
    return dict(sorted(result.items(), key=lambda item: natural_key(item[0])))


def pin_layout(numbers):
    split = (len(numbers) + 1) // 2
    left = numbers[:split]
    right = numbers[split:]
    rows = max(len(left), len(right), 1)
    body_height = max(5.08, (rows - 1) * PIN_PITCH + 5.08)
    layout = {}
    for side, items in (("left", left), ("right", right)):
        for index, number in enumerate(items):
            y = (index - (len(items) - 1) / 2) * PIN_PITCH
            if side == "left":
                layout[number] = (-BODY_HALF_WIDTH - PIN_LENGTH, y, 0)
            else:
                layout[number] = (BODY_HALF_WIDTH + PIN_LENGTH, y, 180)
    return layout, body_height


def symbol_id(numbers):
    # KiCad reserves a trailing _<unit>_<body-style> suffix in symbol names.
    # Prefix every pad token so a generated name can never be parsed as that suffix.
    token = "_".join(f"P{re.sub(r'[^A-Za-z0-9]', 'X', number)}" for number in numbers)
    return f"GEN_{token or 'NOPINS'}"


def make_library_symbol(numbers):
    entry_name = symbol_id(numbers)
    parent = Symbol.create_new(id=f"DOOR8CH:{entry_name}", reference="U", value="PCB component")
    parent.pinNames = True
    parent.pinNamesOffset = 0.5
    unit = Symbol()
    unit.libId = f"{entry_name}_1_1"
    layout, body_height = pin_layout(numbers)
    unit.graphicItems.append(
        SyRect(
            start=Position(X=-BODY_HALF_WIDTH, Y=-body_height / 2),
            end=Position(X=BODY_HALF_WIDTH, Y=body_height / 2),
            stroke=Stroke(width=0.254, type="default"),
            fill=Fill(type="background"),
        )
    )
    for number in numbers:
        x, y, angle = layout[number]
        unit.pins.append(
            SymbolPin(
                electricalType="passive",
                graphicalStyle="line",
                position=Position(X=x, Y=y, angle=angle),
                length=PIN_LENGTH,
                name=f"P{number}",
                number=number,
            )
        )
    parent.units.append(unit)
    return parent, layout, body_height


def channel_from_nets(nets):
    channels = set()
    for net in nets:
        match = re.search(r"(?:^|_)CH([1-8])(?:_|$)", net)
        if match:
            channels.add(int(match.group(1)))
        match = re.match(r"FUSED_12V_CH([1-8])$", net)
        if match:
            channels.add(int(match.group(1)))
    return next(iter(channels)) if len(channels) == 1 else None


def group_for(reference, nets):
    if reference == "CAP1" or re.fullmatch(r"(?:R20[1-8]|J21[1-8])", reference):
        return "CAP1188"
    if re.fullmatch(r"J20[1-6]", reference) or any(net.startswith("REED_") for net in nets):
        return "REEDS"
    channel = channel_from_nets(nets)
    if channel is not None:
        return f"CHANNEL {channel}"
    if reference.startswith(("MOD", "CAN", "ESP", "RF")):
        return "CONTROL / CAN"
    if any(token in net for net in nets for token in ("UART", "SWD", "NRST", "SLOT_ID", "EEPROM", "CAN_TX", "CAN_RX")):
        return "CONTROL / CAN"
    if reference.startswith(("DC", "F", "L")) or any(
        net.startswith(("LOGIC_", "12V_", "S1_3V3", "S2_3V3", "S3_3V3", "S4_3V3")) for net in nets
    ):
        return "POWER"
    return "OTHER / MECHANICAL"


def read_board():
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    definitions = {}
    groups = defaultdict(list)
    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        pads = pad_map(footprint)
        numbers = tuple(pads.keys())
        if numbers not in definitions:
            definitions[numbers] = make_library_symbol(numbers)
        _, layout, body_height = definitions[numbers]
        footprint_name = str(footprint.GetFPID().GetLibItemName())
        item = {
            "reference": reference,
            "value": footprint.GetValue() or "",
            "pcb_footprint": footprint_name,
            "pads": pads,
            "numbers": numbers,
            "layout": layout,
            "height": body_height,
        }
        groups[group_for(reference, set(pads.values()))].append(item)
    return definitions, groups


def write_symbol_library(definitions):
    symbols = []
    for parent, _, _ in definitions.values():
        library_symbol = copy.deepcopy(parent)
        library_symbol.libId = library_symbol.libId.split(":", 1)[-1]
        symbols.append(library_symbol)
    SymbolLib(generator="door8ch_pcb_sync", symbols=symbols).to_file(str(SYMBOL_LIBRARY_PATH), encoding="utf-8")
    (PROJECT / "sym-lib-table").write_text(
        '(sym_lib_table\n  (lib (name "DOOR8CH")(type "KiCad")(uri "${KIPRJMOD}/DOOR-8CH-generated.kicad_sym")(options "")(descr "Generated DOOR-8CH symbols"))\n)\n',
        encoding="utf-8",
    )


def pack_items(items, origin_x, origin_y, width=255.0, columns=3):
    column_width = width / columns
    cursors = [origin_y + 16.0] * columns
    placements = []
    for item in sorted(items, key=lambda value: (-value["height"], natural_key(value["reference"]))):
        column = min(range(columns), key=lambda index: cursors[index])
        x = snap(origin_x + column_width * (column + 0.5))
        y = snap(cursors[column] + item["height"] / 2)
        cursors[column] = y + item["height"] / 2 + 6.35
        placements.append((item, x, y))
    return placements


def add_component(schematic, definitions, item, x, y, global_labels):
    parent, layout, body_height = definitions[item["numbers"]]
    symbol_uuid = uid()
    symbol = SchematicSymbol()
    symbol.libId = parent.libId
    symbol.position = Position(X=x, Y=y, angle=0)
    symbol.unit = 1
    symbol.inBom = True
    symbol.onBoard = True
    symbol.uuid = symbol_uuid
    symbol.properties = [
        Property(key="Reference", value=item["reference"], id=0, position=Position(X=x, Y=snap(y - body_height / 2 - 2.54), angle=0), effects=text_effect()),
        Property(key="Value", value=item["value"], id=1, position=Position(X=x, Y=snap(y + body_height / 2 + 2.54), angle=0), effects=text_effect(0.9)),
        Property(key="Footprint", value="", id=2, position=Position(X=x, Y=y, angle=0), effects=text_effect(0.8, hidden=True)),
        Property(key="Datasheet", value="", id=3, position=Position(X=x, Y=y, angle=0), effects=text_effect(0.8, hidden=True)),
        Property(key="PCB_Footprint", value=item["pcb_footprint"], id=4, position=Position(X=x, Y=y, angle=0), effects=text_effect(0.8, hidden=True)),
    ]
    for number in item["numbers"]:
        symbol.pins[number] = uid()
        relative_x, relative_y, _ = layout[number]
        pin_x, pin_y = snap(x + relative_x), snap(y + relative_y)
        net_name = item["pads"][number]
        if net_name:
            label = GlobalLabel if global_labels else LocalLabel
            kwargs = {"text": net_name, "position": Position(X=pin_x, Y=pin_y, angle=180 if relative_x < 0 else 0), "effects": text_effect(0.8), "uuid": uid()}
            if global_labels:
                kwargs["shape"] = "passive"
                schematic.globalLabels.append(label(**kwargs))
            else:
                schematic.labels.append(label(**kwargs))
        else:
            schematic.noConnects.append(NoConnect(position=Position(X=pin_x, Y=pin_y), uuid=uid()))
    schematic.schematicSymbols.append(symbol)
    schematic.symbolInstances.append(SymbolInstance(path=f"/{symbol_uuid}", reference=item["reference"], unit=1, value=item["value"], footprint=""))


def new_schematic(definitions, paper="A2"):
    schematic = Schematic.create_new()
    schematic.uuid = uid()
    schematic.generator = "door8ch_pcb_sync"
    schematic.paper = PageSettings(paperSize=paper, portrait=False)
    schematic.libSymbols = [copy.deepcopy(parent) for parent, _, _ in definitions.values()]
    return schematic


def add_title(schematic, title):
    schematic.texts.append(Text(text=title, position=Position(X=20.32, Y=12.7, angle=0), effects=Effects(font=Font(width=2.0, height=2.0, bold=True)), uuid=uid()))


def generate_flat(definitions, groups):
    schematic = new_schematic(definitions, "A0")
    add_title(schematic, "DOOR-8CH | generated from routed PCB | pad numbers and net labels are authoritative")
    cell_width, cell_height = 285.75, 254.0
    for index, group_name in enumerate(GROUP_ORDER):
        row, column = divmod(index, 4)
        cell_x = snap(20.32 + column * cell_width)
        cell_y = snap(25.4 + row * cell_height)
        schematic.texts.append(Text(text=group_name, position=Position(X=cell_x, Y=cell_y, angle=0), effects=Effects(font=Font(width=1.8, height=1.8, bold=True)), uuid=uid()))
        for item, x, y in pack_items(groups[group_name], cell_x, cell_y, cell_width - 7.62):
            add_component(schematic, definitions, item, x, y, global_labels=True)
    schematic.to_file(str(FLAT_PATH), encoding="utf-8")


def generate_child(definitions, group_name, items, path):
    schematic = new_schematic(definitions, "A2")
    add_title(schematic, f"DOOR-8CH | {group_name}")
    for item, x, y in pack_items(items, 20.32, 25.4, 530.0, columns=4):
        add_component(schematic, definitions, item, x, y, global_labels=True)
    schematic.to_file(str(path), encoding="utf-8")


def generate_multisheet(definitions, groups):
    child_entries = []
    for group_name in GROUP_ORDER:
        child_path = PROJECT / GROUP_FILES[group_name]
        generate_child(definitions, group_name, groups[group_name], child_path)
        child_entries.append((group_name, child_path.name))

    root = new_schematic({}, "A3")
    add_title(root, "DOOR-8CH | multisheet principle schematic")
    for index, (group_name, filename) in enumerate(child_entries):
        row, column = divmod(index, 4)
        x, y = snap(25.4 + column * 99.06), snap(30.48 + row * 53.34)
        sheet_uuid = uid()
        root.sheets.append(
            HierarchicalSheet(
                position=Position(X=x, Y=y), width=88.9, height=38.1,
                stroke=Stroke(width=0.254, type="default"), fill=ColorRGBA(R=1, G=1, B=1, A=0), uuid=sheet_uuid,
                sheetName=Property(key="Sheetname", value=group_name, id=0, position=Position(X=x, Y=snap(y - 1.27), angle=0), effects=text_effect()),
                fileName=Property(key="Sheetfile", value=filename, id=1, position=Position(X=x, Y=snap(y + 39.37), angle=0), effects=text_effect(0.9)),
                instances=[HierarchicalSheetProjectInstance(name="", paths=[HierarchicalSheetProjectPath(sheetInstancePath=f"/{sheet_uuid}", page=str(index + 2))])],
            )
        )
    root.to_file(str(MULTISHEET_PATH), encoding="utf-8")


def main():
    definitions, groups = read_board()
    write_symbol_library(definitions)
    generate_flat(definitions, groups)
    generate_multisheet(definitions, groups)
    print(f"Generated flat schematic: {FLAT_PATH}")
    print(f"Generated multisheet root: {MULTISHEET_PATH}")
    print(f"Generated child sheets: {len(GROUP_ORDER)}")


if __name__ == "__main__":
    main()
