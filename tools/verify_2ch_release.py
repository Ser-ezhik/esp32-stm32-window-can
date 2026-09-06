"""Check archive contents and placement coordinates against the released PCB."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import pcbnew

root = Path(__file__).resolve().parents[1]
project = root / "hardware/UNIVERSAL-2CH-F103-IC"
release = project / "fabrication" / sys.argv[1]
source = project / "kicad/UNIVERSAL-2CH-F103-IC.kicad_pcb"
board = pcbnew.LoadBoard(str(source))
prefix = "UNIVERSAL-2CH-F103-IC"
with zipfile.ZipFile(release / (prefix + "_GERBER.zip")) as archive:
    for name in archive.namelist():
        assert archive.read(name) == (release / "gerbers" / name).read_bytes(), name
    for suffix in ("-F_Cu.gbr", "-B_Cu.gbr", "-F_Mask.gbr", "-B_Mask.gbr",
                   "-Edge_Cuts.gbr", "-PTH.drl", "-NPTH.drl"):
        assert len(archive.read(prefix + suffix)) > 100, suffix

def read_csv(suffix):
    with (release / (prefix + suffix)).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

cpl = read_csv("_CPL_JLCPCB_SMD_EXCEPT_VNH.csv")
bom = read_csv("_BOM_JLCPCB_SMD_EXCEPT_VNH.csv")
refs = {r for row in bom for r in row["Designator"].split(",")}
assert refs == {row["Designator"] for row in cpl}
assert len(cpl) == len(refs) == 75
assert not {"U1", "U2"} & refs
for row in cpl:
    fp = board.FindFootprintByReference(row["Designator"])
    assert fp is not None
    pos = fp.GetPosition()
    assert abs(float(row["Mid X"].removesuffix("mm")) - pcbnew.ToMM(pos.x)) < .000002
    assert abs(float(row["Mid Y"].removesuffix("mm")) + pcbnew.ToMM(pos.y)) < .000002
    assert row["Layer"] == ("Bottom" if fp.IsFlipped() else "Top")
assert next(r for r in cpl if r["Designator"] == "C340")["Layer"] == "Top"
manifest = {"board_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "files": {str(p.relative_to(release)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(release.rglob("*")) if p.is_file()
                      and p.name != "SHA256.json"}}
(release / "SHA256.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
print("PASS: Gerber ZIP matches exported files; required layers and drills present.")
print("PASS: all 75 BOM/CPL references, coordinates and board sides match PCB.")
print("Vendor model rotation is not proven by this coordinate check.")
