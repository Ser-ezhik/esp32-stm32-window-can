import pathlib
import subprocess
import tempfile
import pcbnew

REL = 'hardware/UNIVERSAL-2CH-F103-IC/kicad/UNIVERSAL-2CH-F103-IC.kicad_pcb'
OUT = pathlib.Path(tempfile.gettempdir()) / 'two-channel-repair-candidate.kicad_pcb'
# The worktree PCB was clean before this repair started. Preserve its committed
# state as the baseline and generate an isolated candidate on every execution.
BASE = '7606dc24930b113c63ee8d6200549ff06856821e'
OUT.write_bytes(subprocess.check_output(['git', 'show', BASE + ':' + REL]))
b = pcbnew.LoadBoard(str(OUT))
tracks = b.GetTracks()
fps = {f.GetReference(): f for f in b.GetFootprints()}
nets = {n.GetNetname(): n for n in b.GetNetInfo().NetsByNetcode().values()}
def pos(x,y): return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def near(p,x,y): return abs(p.x/1e6-x)<0.01 and abs(p.y/1e6-y)<0.01
def track(net,layer,a,c,w=0.2):
    t=pcbnew.PCB_TRACK(b);t.SetNet(nets[net]);t.SetLayer(layer)
    t.SetStart(pos(*a));t.SetEnd(pos(*c));t.SetWidth(pcbnew.FromMM(w));b.Add(t)
def via(net,p):
    v=pcbnew.PCB_VIA(b);v.SetNet(nets[net]);v.SetPosition(pos(*p))
    v.SetWidth(pcbnew.FromMM(0.6));v.SetDrill(pcbnew.FromMM(0.3))
    v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)

# An explicit hand-installed link connects D230 cathode to C270 positive.
# Keep its net separate so the PCB does not falsely claim routed connectivity.
n=pcbnew.NETINFO_ITEM(b,'POWER_MONITOR_12V');b.Add(n);nets[n.GetNetname()]=n
for ref,pad in [('U270','5'),('C270','1'),('R270','1')]:fps[ref].FindPadByNumber(pad).SetNet(n)
for t in tracks:
    if type(t)!=pcbnew.PCB_TRACK or t.GetNetname()!='LOGIC_12V_FUSED':continue
    if near(t.GetStart(),65.825,75.521) and near(t.GetEnd(),66.785,75.521):
        b.Remove(t);continue
    if t.GetLayer()==pcbnew.B_Cu and all(64.9<p.x/1e6<69.1 and 70.5<p.y/1e6<77.1 for p in [t.GetStart(),t.GetEnd()]):t.SetNet(n)
# Remove the now-unused supply branch to avoid dangling copper.
for t in tracks:
    if t.GetNetname()=='LOGIC_12V_FUSED' and (type(t)==pcbnew.PCB_VIA or t.GetLayer()==pcbnew.F_Cu):
        if type(t)==pcbnew.PCB_TRACK and near(t.GetStart(),75.8,98) and near(t.GetEnd(),75.8,93):continue
        b.Remove(t)

# Relocate the existing bypass capacitor after the CAP supply jumper.
f=fps['C340']; f.Flip(f.GetPosition(),False);f.SetPosition(pos(83.5,54.8));f.SetOrientationDegrees(90)
f.FindPadByNumber('1').SetNet(nets['S1_3V3'])
for t in tracks:
    if type(t)!=pcbnew.PCB_TRACK:continue
    if (near(t.GetEnd(),75.775,57.0) or near(t.GetEnd(),74.225,57.0)):b.Remove(t)
cap=f.FindPadByNumber('1').GetPosition();gnd=f.FindPadByNumber('2').GetPosition()
cp=(cap.x/1e6,cap.y/1e6);gp=(gnd.x/1e6,gnd.y/1e6)
via('S1_3V3',(83.5636,55.3526));track('S1_3V3',pcbnew.F_Cu,cp,(83.5636,55.3526))
via('GND',(84,52.5));track('GND',pcbnew.F_Cu,gp,(84,52.5))
b.BuildConnectivity();pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(OUT),b)
print(OUT)
