"""Check that the focused PCB repair did not change connector or MCU mappings."""
import pathlib
import subprocess
import tempfile
import pcbnew

rel = 'hardware/UNIVERSAL-2CH-F103-IC/kicad/UNIVERSAL-2CH-F103-IC.kicad_pcb'
baseline = pathlib.Path(tempfile.gettempdir()) / 'two-channel-audit-baseline.kicad_pcb'
baseline.write_bytes(subprocess.check_output(['git', 'show', '7606dc24930b113c63ee8d6200549ff06856821e:' + rel]))
old = pcbnew.LoadBoard(str(baseline))
new = pcbnew.LoadBoard(rel)
old_fps = {f.GetReference(): f for f in old.GetFootprints()}
new_fps = {f.GetReference(): f for f in new.GetFootprints()}
assert old_fps.keys() == new_fps.keys(), 'Unexpected added/removed footprint'
changes = {('C340', '1'): 'S1_3V3', ('U270', '5'): 'POWER_MONITOR_12V',
           ('C270', '1'): 'POWER_MONITOR_12V', ('R270', '1'): 'POWER_MONITOR_12V'}
for ref, old_fp in old_fps.items():
    new_fp = new_fps[ref]
    if ref != 'C340':
        assert old_fp.GetPosition().x == new_fp.GetPosition().x and old_fp.GetPosition().y == new_fp.GetPosition().y, ref
        assert old_fp.GetOrientationDegrees() == new_fp.GetOrientationDegrees(), ref
        assert old_fp.GetLayer() == new_fp.GetLayer(), ref
    old_pads, new_pads = list(old_fp.Pads()), list(new_fp.Pads())
    assert len(old_pads) == len(new_pads), ref
    for a, c in zip(old_pads, new_pads):
        assert a.GetNumber() == c.GetNumber(), ref
        assert c.GetNetname() == changes.get((ref, a.GetNumber()), a.GetNetname()), (ref, a.GetNumber())
        if ref != 'C340':
            assert a.GetPosition().x == c.GetPosition().x and a.GetPosition().y == c.GetPosition().y, ref
power_nets = {'CH1_OUTA', 'CH1_OUTB', 'CH2_OUTA', 'CH2_OUTB', 'FUSED_12V_CH1', 'FUSED_12V_CH2'}
def power_tracks(board):
    return sorted((t.GetNetname(), t.GetLayer(), t.GetStart().x, t.GetStart().y,
                   t.GetEnd().x, t.GetEnd().y, t.GetWidth())
                  for t in board.GetTracks() if type(t) == pcbnew.PCB_TRACK and t.GetNetname() in power_nets)
assert power_tracks(old) == power_tracks(new), 'Unexpected motor copper edit'
assert new_fps['C340'].GetLayer() == pcbnew.F_Cu
print('PASS: all %d footprints checked; only four intended net assignments and C340 placement changed.' % len(new_fps))
print('PASS: both motor-channel track sets and all connector/MCU pad mappings preserved.')
