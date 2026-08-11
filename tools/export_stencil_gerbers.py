"""Export solder-paste and outline Gerbers for a standalone stencil order."""

from __future__ import annotations

import sys
from pathlib import Path

import pcbnew


def plot_layer(
    controller: pcbnew.PLOT_CONTROLLER,
    layer: int,
    suffix: str,
    description: str,
) -> Path:
    controller.SetLayer(layer)
    if not controller.OpenPlotfile(suffix, pcbnew.PLOT_FORMAT_GERBER, description):
        raise RuntimeError(f"Cannot open Gerber output for {description}")
    if not controller.PlotLayer():
        raise RuntimeError(f"Cannot plot {description}")
    controller.ClosePlot()
    return Path(controller.GetPlotFileName())


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: export_stencil_gerbers.py BOARD.kicad_pcb OUTPUT_DIR")

    board_path = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    board = pcbnew.LoadBoard(str(board_path))
    controller = pcbnew.PLOT_CONTROLLER(board)
    options = controller.GetPlotOptions()
    options.SetOutputDirectory(str(output_dir))
    options.SetPlotFrameRef(False)
    options.SetAutoScale(False)
    options.SetScale(1.0)
    options.SetMirror(False)
    options.SetUseGerberAttributes(True)
    options.SetUseGerberProtelExtensions(False)
    options.SetCreateGerberJobFile(False)

    files = [
        plot_layer(controller, pcbnew.F_Paste, "F_Paste", "Front solder paste"),
        plot_layer(controller, pcbnew.B_Paste, "B_Paste", "Back solder paste"),
        plot_layer(controller, pcbnew.Edge_Cuts, "Edge_Cuts", "Board outline"),
    ]

    nonempty_paste = [path for path in files[:2] if path.exists() and path.stat().st_size > 300]
    if not nonempty_paste:
        raise RuntimeError("Both paste Gerbers are empty")
    for path in files:
        print(f"{path.name}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
