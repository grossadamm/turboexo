#!/usr/bin/env python3
"""Generate Rev D editable DIYLC layout, connectivity report, and guide."""
import json, math, subprocess
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import simpleSplit

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs/hardware/ads1115/revD'; TMP=ROOT/'tmp/pdfs/ads1115-revD'; PDF=ROOT/'output/pdf/ADS1115_sensor_board_revD_soldering_guide.pdf'; JAR='/Applications/DIYLC.app/Contents/Java/diylc.jar'
spec=json.loads((OUT/'layout_spec.json').read_text()); parts=spec['parts']; wires=spec['wires']; buses=spec['buses']; COLS=24; ROWS=18
colors={'3V3':'C33D3D','GND':'354454','SCL':'B48119','SDA':'278858','FUEL':'3378C5','OIL':'9862B9','BRAKE':'CB6B28','WAKE_BTN':'CA4582','WAKE_RETURN':'A35275','TRIGGER_PLUS':'B55024','TRIGGER_RETURN':'75472C','CAP_MINUS':'D18429','OPTO_INPUT_PLUS':'9A4B15'}
def xy(p): return tuple(p)
def validate():
    pins={f"{p['ref']}.{i}":xy(v) for p in parts for i,v in enumerate(p['pins'])}
    assert len(pins)==len(set(pins.values()))
    assert all(1<=x<=24 and 1<=y<=18 for x,y in pins.values())
    coords=set(pins.values())|{xy(t) for b in buses for t in b['taps']}
    assert all(xy(w['path'][0]) in coords and xy(w['path'][-1]) in coords for w in wires)
    parent={p:p for p in coords}
    def root(x):
        while parent[x]!=x: x=parent[x]
        return x
    def join(a,b): parent[root(a)]=root(b)
    for b in buses:
        for a,z in zip(b['taps'],b['taps'][1:]):join(xy(a),xy(z))
    for w in wires:join(xy(w['path'][0]),xy(w['path'][-1]))
    actual={}
    for name,p in pins.items():actual.setdefault(root(p),set()).add(name)
    expected={'3V3':{'H1.0','U1.0','R1.0','R3.0','R5.0'},'GND':{'H1.8','U1.1','U1.4','J2.1','J3.1','J4.1','C1.1','C2.1'},'SCL':{'H1.4','U1.2'},'SDA':{'H1.2','U1.3'},'FUEL':{'J2.0','R1.1','F1.0','F1.1','C1.0','U1.6'},'OIL':{'J3.0','R3.1','F2.0','F2.1','C2.0','U1.7'},'BRAKE':{'H1.12','J4.0','R5.1'}}
    grouped={frozenset(v) for v in actual.values()}; assert sum(len(v)>1 for v in actual.values())==7; assert all(frozenset(v) in grouped for v in expected.values()),actual
    # Bare buses may contact intermediate pads: no other-net terminal may occupy them.
    terminal_coords=set(pins.values())|{xy(w['path'][k]) for w in wires for k in (0,-1)}
    for bus in buses:
        taps=list(map(xy,bus['taps'])); y=taps[0][1]; x1,x2=taps[0][0],taps[-1][0]
        assert all(root(q)==root(taps[0]) for q in terminal_coords if q[1]==y and x1<=q[0]<=x2), (bus['ref'],terminal_coords)
    reserved={k for k in pins if k.split('.')[0] in {'J5','J6','J7','R7','R8','C6','D1'}}; assert all(len(actual[root(pins[k])])==1 for k in reserved); assert all(xy(w['path'][i]) not in {pins[k] for k in reserved} for w in wires for i in (0,-1)); assert all(pins[k] not in {xy(w['path'][i]) for w in wires for i in (0,-1)} for k in ('H1.1','H1.3','H1.10')); expected_pins=set().union(*expected.values()); assert all(len(v)==1 for v in actual.values() if not (v&expected_pins))
    for w in wires:
        assert root(xy(w['path'][0]))==root(xy(w['path'][-1]))
        assert root(xy(w['path'][0]))==root(pins[next(iter(expected[w['net']]))])
    return {'schema_version':1,'electrical_connectivity_model_passed':True,'model_scope':'Endpoints and individual bus tap segments; insulated bends and crossings are not connections. Components do not electrically short their two terminals.','expected_nets':{k:sorted(v) for k,v in expected.items()},'unconnected_pins':sorted(set(pins)-expected_pins),'bus_segments':sum(len(b['taps'])-1 for b in buses),'fitted_resistors':['R1 1k bench','R5 10k'],'optional_parts_unfitted':['R3','F1','F2','C1','C2'],'reserved_wake_unfitted_unwired':['J5','J6','J7','R7','R8','C6','D1'],'fitted_links':['LK1','LK2'],'fuel_expected_V_at_110ohm_and_3_3V':3.3*110/1110,'physical_build_or_electrical_test_performed':False,'mechanical_fit_verified':False,'gpio27_availability_verified':False,'formal_hat_compliance':False}
def j(s):return json.dumps(s)
def native():
    calls=[]
    for p in parts:
        arr=','.join(str(t) for q in p['pins'] for t in q)
        if p['kind']=='hat':calls.append(f'header({j(p["ref"])},{j(",".join(p["names"]))},2,20,new int[]{{{arr}}});')
        elif p['kind']=='header':calls.append(f'header({j(p["ref"])},{j(",".join(p["names"]))},1,{len(p["pins"])},new int[]{{{arr}}});')
        elif p['kind']=='electrolytic':calls.append(f'cap({j(p["ref"])},new int[]{{{arr}}});')
        elif p['kind']=='diode':calls.append(f'diode({j(p["ref"])},new int[]{{{arr}}});')
        elif p['kind']=='resistor':calls.append(f'resistor({j(p["ref"])},{p["ohms"]},new int[]{{{arr}}});')
        else:
            for i,(x,y) in enumerate(p['pins']):calls.append(f'pad({j(p["ref"]+"."+str(i))},{x},{y});')
    wc=[]
    for b in buses:
        for i,(a,z) in enumerate(zip(b['taps'],b['taps'][1:])):wc.append(f'wire({j(b["ref"]+"_"+str(i+1))},0x{colors[b["net"]]},new int[]{{{a[0]},{a[1]},{z[0]},{z[1]}}});')
    for w in wires:wc.append(f'wire({j(w["ref"])},0x{colors[w["net"]]},new int[]{{{",".join(str(t) for q in w["path"] for t in q)}}});')
    src=r'''import java.awt.*;import java.awt.geom.*;import java.awt.image.*;import java.io.*;import java.nio.file.*;import java.util.*;import javax.imageio.ImageIO;
import org.diylc.core.*;import org.diylc.core.measures.*;import org.diylc.common.*;import org.diylc.components.boards.*;import org.diylc.components.electromechanical.*;import org.diylc.components.passive.*;import org.diylc.components.connectivity.*;import org.diylc.serialization.*;import org.diylc.components.semiconductors.*;
public class BuildHat {static Project pr=new Project();static double X=90,Y=140,S=20;static Point2D p(double x,double y){return new Point2D.Double(X+x*S,Y+y*S);}
static void label(String s,double x,double y,int n){org.diylc.components.misc.Label l=new org.diylc.components.misc.Label();l.setValue(s);l.setFontSize(n);l.setColor(Color.DARK_GRAY);l.setHorizontalAlignment(HorizontalAlignment.LEFT);l.setControlPoint(new Point2D.Double(x,y),0);pr.getComponents().add(l);}
static void header(String n,String names,int rows,int cols,int[] a){PinHeader h=new PinHeader();h.setName(n);h.setRowCount(rows);h.setColumnCount(cols);h.setOrientation(Orientation._270);for(int i=0;i<a.length/2;i++)h.setControlPoint(p(a[i*2],a[i*2+1]),i);h.setNodeNames(names);pr.getComponents().add(h);}
static void resistor(String n,int v,int[] a){Resistor r=new Resistor();r.setName(n);r.setValue(new Resistance(v/1000.0,ResistanceUnit.K));r.setDisplay(n.equals("R7")||n.equals("R8")?Display.NAME:Display.BOTH);if(n.equals("R8"))r.setLength(new Size(9.,SizeUnit.mm));r.setControlPoint(p(a[0],a[1]),0);r.setControlPoint(p(a[2],a[3]),1);pr.getComponents().add(r);}
static void cap(String n,int[] a){RadialElectrolytic c=new RadialElectrolytic();c.setName(n);c.setValue(new Capacitance(220.,CapacitanceUnit.uF));c.setVoltageNew(new org.diylc.core.measures.Voltage(25.,org.diylc.core.measures.VoltageUnit.V));c.setPolarized(true);c.setInvert(false);c.setWidth(new Size(8.,SizeUnit.mm));c.setLength(new Size(8.,SizeUnit.mm));c.setControlPoint(p(a[0],a[1]),0);c.setControlPoint(p(a[2],a[3]),1);pr.getComponents().add(c);}
static void diode(String n,int[] a){DiodeGlass d=new DiodeGlass();d.setName(n);d.setValue("1N4148");d.setControlPoint(p(a[2],a[3]),0);d.setControlPoint(p(a[0],a[1]),1);pr.getComponents().add(d);}
static void pad(String n,int x,int y){SolderPad s=new SolderPad();s.setName(n);s.setControlPoint(p(x,y),0);pr.getComponents().add(s);}
static void wire(String n,int rgb,int[] a){HookupWire w=new HookupWire();w.setName(n);String[] en={"","","TWO","THREE","FOUR","FIVE","SIX","SEVEN"};w.setPointCount(org.diylc.components.AbstractCurvedComponent.PointCount.valueOf(en[a.length/2]));w.setSmooth(false);w.setValue(AWG._26);w.setLeadColor(new Color(rgb));for(int i=0;i<a.length/2;i++)w.setControlPoint(p(a[2*i],a[2*i+1]),i);pr.getComponents().add(w);}
public static void main(String[]a)throws Exception{org.diylc.appframework.miscutils.ConfigurationManager.getInstance().initialize(a[0]+"/config.xml");pr.setTitle("TurboExo ADS1115 compact carrier Rev D");pr.setFileVersion(new org.diylc.appframework.update.VersionNumber(6,9,0));pr.setAuthor("TurboExo");pr.setWidth(new Size(180.,SizeUnit.mm));pr.setHeight(new Size(115.,SizeUnit.mm));pr.setGridSpacing(new Size(.1,SizeUnit.in));pr.setDescription("REV D SENSOR FIRST: reserved wake pads EMPTY and UNWIRED. Do not fit wake parts or leads. 24x18 individual pad board. TOP coordinate view. Colored wires are insulated underneath; bends/crossings are not soldered. P_BUS and G_BUS segments form bare continuous buses joined only at listed taps. F1/F2 pads are bypassed with fitted removable links; R3, C1, C2 empty. J5/J6/J7/R7/R8/C6/D1 are bare reserved pads, unwired; no wake function or external wake leads. No formal HAT compliance. Physical fit and electrical tests not performed. See guide.");PerfBoard b=new PerfBoard();b.setName("B1");b.setCoordinateDisplay(AbstractBoard.CoordinateDisplay.None);b.setControlPoint(new Point2D.Double(X,Y),0);b.setControlPoint(new Point2D.Double(X+25*S,Y+19*S),1);pr.getComponents().add(b);
org.diylc.components.shapes.Rectangle reserve=new org.diylc.components.shapes.Rectangle();reserve.setName("RESERVED-WAKE-EMPTY-UNWIRED");reserve.setControlPoint(p(13.5,3.5),0);reserve.setControlPoint(p(23.5,9.5),1);reserve.setColor(new Color(0xE4D5D5));reserve.setBorderColor(new Color(0xA75544));pr.getComponents().add(reserve);
WIRECALLS
org.diylc.components.shapes.Rectangle outline=new org.diylc.components.shapes.Rectangle();outline.setName("U1-envelope-approx");outline.setControlPoint(p(1.5,4.5),0);outline.setControlPoint(p(13.5,9.5),1);outline.setColor(new Color(0xE3EFF8));outline.setBorderColor(new Color(0x245C8D));pr.getComponents().add(outline);
PARTCALLS
for(int i=1;i<=24;i++)label(""+i,X+i*S-4,Y-10,9);for(int i=1;i<=18;i++)label(""+i,X-24,Y+i*S+3,9);
label("ADS1115 COMPACT CARRIER - REV D",90,43,20);label("TOP VIEW; wires underneath; coordinates = (column,row)",90,70,13);label("H1: pin 1 (2,3); female below, male stacking pins above",90,92,13);
String[] note={"ASSEMBLY NOTES", "24 x 18 separate pads, 2.54 mm", "H1 2x20: 1 at (2,3), 2 at (2,2)","U1: VDD to A3 left to right", "R1 1k bench; R5 10k fitted", "R3, F1, F2, C1, C2 EMPTY", "LK1/LK2 fitted across F1/F2", "Red row11 = bare 3V3 bus", "Gray row16 = bare GND bus", "Keep signal crossings insulated", "RESERVED WAKE - EMPTY", "DO NOT FIT / DO NOT WIRE", "J5 J6 J7 R7 R8 C6 D1 bare pads", "No charger/opto/Pi J2 leads", "J3 oil temp unplugged", "GPIO27 proposed: verify unused", "No Pi 5V or GPIO17 wiring", "NOT formal HAT; fit unverified", "See guide for complete wiring"};for(int i=0;i<note.length;i++)label(note[i],635,120+i*21,i==0?15:12);
label("J2 FUEL",193,545,11);label("J3 OIL",353,545,11);label("J4 BRAKE",505,545,11);
label("1",X+S,Y+3*S+5,12);label("U1 ADS1115 module",X+2*S,Y+6*S,15);label("Approximate body; verify fit",X+2*S,Y+7*S,11);label("VDD left; A3 right",X+2*S,Y+8*S,11);
String xml=ProjectFileManager.xStreamSerializer.toXML(pr);Files.writeString(Path.of(a[1]),"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"+xml);Project copy=(Project)ProjectFileManager.xStreamSerializer.fromXML(xml);if(copy.getComponents().size()!=pr.getComponents().size())throw new Exception("roundtrip");try(var out=new PrintWriter(a[0]+"/native-endpoints.tsv")){for(var c:copy.getComponents())for(int i=0;i<c.getControlPointCount();i++)if(c.isControlPointSticky(i)){Point2D q=c.getControlPoint(i);out.printf(Locale.US,"%s\t%d\t%.4f\t%.4f\t%s%n",c.getName(),i,(q.getX()-X)/S,(q.getY()-Y)/S,c.getControlPointNodeName(i));}}
BufferedImage im=new BufferedImage(1050,650,BufferedImage.TYPE_INT_RGB);Graphics2D g=im.createGraphics();g.setColor(Color.WHITE);g.fillRect(0,0,1050,650);g.setClip(0,0,1050,650);g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON);IDrawingObserver o=new IDrawingObserver(){public void stopTracking(){}public void startTracking(){}public void startTrackingContinuityArea(boolean b){}public void stopTrackingContinuityArea(){}public boolean isTrackingContinuityArea(){return false;}public void setContinuityMarker(String s){}};for(var c:copy.getComponents())c.draw(g,ComponentState.NORMAL,false,copy,o);g.dispose();ImageIO.write(im,"png",new File(a[2]));}}
'''.replace('WIRECALLS','\n'.join(wc)).replace('PARTCALLS','\n'.join(calls))
    (TMP/'BuildHat.java').write_text(src);subprocess.run(['javac','-cp',JAR,str(TMP/'BuildHat.java')],check=True);subprocess.run(['java','-Djava.awt.headless=true','-cp',JAR+':'+str(TMP),'BuildHat',str(TMP),str(OUT/'ADS1115_sensor_board_revD.diy'),str(OUT/'ADS1115_native_preview.png')],check=True)
    obs={}
    for line in (TMP/'native-endpoints.tsv').read_text().splitlines():
        ref,i,x,y,*rest=line.split('\t');obs[(ref,int(i))]=(float(x),float(y),rest[0] if rest else '')
    for p in parts:
        for i,pos in enumerate(p['pins']):
            key=(p['ref'],1-i if p['kind']=='diode' else i) if p['kind'] not in ('reserved_resistor','reserved_capacitor','reserved_wake') else (p['ref']+'.'+str(i),0)
            assert obs[key][:2]==tuple(pos),(key,obs[key],pos)
            if p['kind'] in ('electrolytic','diode'):assert obs[key][2]==p['names'][i],(key,obs[key])
            if p['kind']=='hat':assert obs[key][2]==str(i+1),(key,obs[key])
    for w in wires:
        keys=[k[1] for k in obs if k[0]==w['ref']];assert keys==[0,len(w['path'])-1],(w['ref'],keys); assert obs[(w['ref'],0)][:2]==tuple(w['path'][0]) and obs[(w['ref'],keys[-1])][:2]==tuple(w['path'][-1]), w['ref']
    for b in buses:
        for i,(a,z) in enumerate(zip(b['taps'],b['taps'][1:])):
            ref=b['ref']+'_'+str(i+1);assert obs[(ref,0)][:2]==tuple(a) and obs[(ref,1)][:2]==tuple(z)
def pdf():
    W,H=landscape(A4); c=canvas.Canvas(str(PDF),pagesize=(W,H)); navy=HexColor('#173a52'); gray=HexColor('#394b58')
    c.setTitle('TurboExo ADS1115 sensor-first carrier Rev D')
    def text(x,y,s,size=9,col=gray,bold=False):
        c.setFillColor(col); c.setFont('Helvetica-Bold' if bold else 'Helvetica',size); c.drawString(x,y,s)
    def para(x,y,s,width=275,size=8.4):
        for line in simpleSplit(s,'Helvetica',size,width): text(x,y,line,size); y-=size+3
        return y
    def head(n,title,sub):
        c.setFillColor(navy); c.rect(0,H-62,W,62,fill=1,stroke=0); text(26,H-28,title,18,white,True); text(26,H-47,sub,9,white); text(26,18,'TURBOEXO  /  ADS1115 SENSOR-FIRST CARRIER  /  REV D  /  2026-10-31',8); text(W-65,18,f'{n} / 4',8)
    def board(mirror=False,wireview=False):
        x0,y0,s=48,112,19
        def pt(q):
            x,y=q; return x0+(24-x if mirror else x-1)*s,y0+(18-y)*s
        c.setFillColor(HexColor('#f5f0e4')); c.setStrokeColor(HexColor('#d6c8ad')); c.roundRect(x0-10,y0-10,23*s+20,17*s+20,4,fill=1)
        # Reserved region overlay is a visual warning, not a copper zone.
        a,b=pt((13.5,3.5)); d,e=pt((23.5,9.5)); c.setFillColor(HexColor('#e4d5d5')); c.rect(min(a,d),min(b,e),abs(d-a),abs(e-b),fill=1,stroke=0)
        for y in range(1,19):
            for x in range(1,25):
                a,b=pt((x,y)); c.setFillColor(HexColor('#bca87c')); c.circle(a,b,2,fill=1,stroke=0)
        for x in range(1,25):
            a,b=pt((x,1)); c.setFont('Helvetica',7); c.setFillColor(gray); c.drawCentredString(a,b+19,str(x))
        for y in range(1,19):
            a,b=pt((1,y)); text(x0-23,b-2,str(y),7); text(x0+23*s+15,b-2,str(y),7)
        if wireview:
            for bus in buses:
                pts=list(map(pt,bus['taps'])); c.setStrokeColor(HexColor('#'+colors[bus['net']])); c.setLineWidth(3); c.line(*pts[0],*pts[-1])
                for a,b in pts: c.setFillColor(HexColor('#'+colors[bus['net']])); c.circle(a,b,3,fill=1,stroke=0)
            for w in wires:
                pts=list(map(pt,w['path']))
                for color,width in [(white,3.5),(HexColor('#'+colors[w['net']]),1.4)]:
                    c.setStrokeColor(color); c.setLineWidth(width); path=c.beginPath(); path.moveTo(*pts[0])
                    for q in pts[1:]: path.lineTo(*q)
                    c.drawPath(path)
                for a,b in (pts[0],pts[-1]): c.setFillColor(HexColor('#'+colors[w['net']])); c.circle(a,b,2.6,fill=1,stroke=0)
            for p in parts:
                for q in p['pins']: a,b=pt(q); c.setStrokeColor(navy); c.setLineWidth(.5); c.circle(a,b,3.5,stroke=1,fill=0)
        else:
            a,b=pt((1.5,4.5)); d,e=pt((13.2,9.5)); c.setFillColor(HexColor('#e3eff8')); c.setStrokeColor(HexColor('#245c8d')); c.roundRect(min(a,d),min(b,e),abs(d-a),abs(e-b),3,fill=1)
            text(min(a,d)+8,max(b,e)-18,'U1 ADS1115 module',11,navy,True); text(min(a,d)+8,max(b,e)-33,'Approximate body - verify fit',7)
            for p in parts:
                pts=list(map(pt,p['pins'])); xs,ys=zip(*pts)
                if p['kind'] in ('hat','header'):
                    c.setFillColor(HexColor('#324b5b')); c.setStrokeColor(navy); c.roundRect(min(xs)-6,min(ys)-6,max(xs)-min(xs)+12,max(ys)-min(ys)+12,2,fill=1)
                    for a,b in pts: c.setFillColor(HexColor('#e7bd58')); c.rect(a-2,b-2,4,4,fill=1,stroke=0)
                    if p['kind']=='hat':
                        a,b=pts[0]; c.setFillColor(HexColor('#c33d3d')); c.rect(a-3,b-3,6,6,fill=1,stroke=0)
                elif p['kind']=='resistor':
                    (a,b),(d,e)=pts; c.setStrokeColor(gray); c.line(a,b,d,e); c.setFillColor(HexColor('#e9d399')); c.saveState(); c.translate((a+d)/2,(b+e)/2); c.rotate(math.degrees(math.atan2(e-b,d-a))); c.roundRect(-14,-6,28,12,3,fill=1); c.restoreState()
                else:
                    for a,b in pts: c.setStrokeColor(HexColor('#a75544')); c.setLineWidth(1.2); c.circle(a,b,4,stroke=1,fill=0)
            for q,label in [((2,1.3),'H1: pin 1 inner row 3'),((6,12.7),'R1'),((14,12.7),'R3 EMPTY'),((22,12.7),'R5'),((7,14.2),'F1 / LK1'),((15,14.2),'F2 / LK2'),((6,18),'J2 FUEL'),((14,18),'J3 OIL'),((21,18),'J4 BRAKE'),((14,5.2),'J5'),((14,8.3),'J6'),((22,5.2),'J7'),((17,7.6),'C6'),((23,7.5),'R7'),((18,9.8),'R8'),((21,7.1),'D1')]:
                a,b=pt(q); text(a,b,label,7,navy,True)
        return pt
    head(1,'Placement - TOP side','24 x 18 individual pads, 2.54 mm pitch. Coordinates are (column,row) from the marked corner.')
    board(); x,y=535,H-87
    for title,body in [('STACKING HEADER','H1 female socket below; male stacking pins above for existing UPS jumpers. Odd pins row 3, even row 2. Pin 1 = (2,3); pin 2 = (2,2). Verify actual Pi pin 1 and fit before mating.'),('ADS1115','U1 socket (3,10) to (12,10): VDD, GND, SCL, SDA, ADDR, ALRT, A0, A1, A2, A3. Check module pin order and clearance.'),('FIT / LEAVE EMPTY','Fit R1 1k removable fuel bench bias, R5 10k brake pull-up and LK1/LK2. Leave R3, F1, F2, C1 and C2 empty. J2 fuel, J3 oil, J4 brake: left signal, right ground. Leave J3 unplugged.'),('RESERVED WAKE','Shaded corner: J5, J6, J7, R7, R8, C6 and D1 are bare pads only. DO NOT FIT OR WIRE. No charger, optocoupler or Pi J2 leads.'),('MECHANICAL','Hole span 58.42 x 43.18 mm. Dry-fit header height, UPS jumpers, cooler, module and standoffs. Fit unverified; not a formally compliant HAT.')]:
        text(x,y,title,9,navy,True); y=para(x,y-14,body)-10
    c.showPage(); head(2,'Wiring - SOLDER side','Mirrored left/right; flip like a book with top edge held at top. Coordinates retain TOP-view numbering.')
    board(True,True); x,y=535,H-87
    for title,body in [('BARE BUSES','3V3 row 11: bare wire (3,11) to (22,11); solder taps (3,11), (6,11), (14,11), (22,11). GND row 16: bare wire (4,16) to (23,16); solder taps (4,16), (7,16), (12,16), (15,16), (20,16), (23,16).'),('INSULATED JUMPERS','All other routes are insulated. Strip and solder only endpoints on page 3, beside component leads at underside pads. Bends and crossings are not connections. Keep insulation intact over buses and other pads.'),('LINKS / EMPTY PADS','Fit removable insulated wire links LK1 and LK2 across F1 and F2. C1/C2 and R3 are empty. No contact to unused pads at wire bends or crossings.'),('RESERVED WAKE','Shaded area identifies reserved pads, not a copper zone. No wake parts or wake wires are fitted; insulated sensor wires may pass across the area without electrical contact. No 12.6 V, opto or Pi J2 leads.'),('PASS THROUGH','No carrier wires to H1 5 V pins 2/4 or GPIO17 physical pin 11. GPIO27 physical pin 13 is proposed for brake; verify availability first.')]:
        text(x,y,title,9,navy,True); y=para(x,y-14,body)-10
    c.showPage(); head(3,'Wire and bus checklist','Coordinates are TOP-view numbering. Only endpoints are solder joints; bends and crossings remain insulated.')
    def fmt(p): return '('+','.join(map(str,p))+')'
    for block,subset in enumerate((wires[:11],wires[11:])):
        x=28+block*400; y=H-90; text(x,y,'REF / NET',9,navy,True); text(x+140,y,'FROM',9,navy,True); text(x+230,y,'TO',9,navy,True); y-=22
        for w in subset:
            c.setStrokeColor(HexColor('#c9d2d8')); c.line(x,y-7,x+370,y-7); c.rect(x,y-1,7,7,fill=0); text(x+14,y,w['ref']+'  '+w['net'],8,HexColor('#'+colors[w['net']])); text(x+140,y,fmt(w['path'][0]),9); text(x+230,y,fmt(w['path'][-1]),9); y-=20
    text(28,190,'BARE BUS TAP CHECKLIST',10,navy,True)
    for i,b in enumerate(buses): text(28,170-i*18,b['ref']+'  '+b['net']+'   '+ ' - '.join(map(fmt,b['taps'])),9)
    text(28,110,'F1/F2 empty; LK1/LK2 fitted. R3, C1, C2 empty. Reserved wake pads remain empty and unwired.',9,navy,True)
    text(28,90,'W23-W30 omitted. No carrier connection to Pi 5 V pins 2/4 or GPIO17 physical pin 11.',9)
    c.showPage(); head(4,'BOM and bench checks','Calculated expectations only. No physical build, electrical measurement or vehicle test has been performed.')
    columns=[(28,390,[('BOM / BUILD NOW','24 x 18 individual-pad board; H1 2x20 stacking header; U1 1x10 ADS1115 socket; J2/J3/J4 two-pin connectors; R1 1k removable fuel bias; R5 10k brake pull-up; LK1/LK2 insulated links; insulated jumpers and two bare buses. J3 may be omitted.'),('1  INSPECT / CONTINUITY','With Pi power and all connections removed, check every endpoint, buses and reserved pads. Confirm no 3V3-to-GND short, no unintended bridges, no wiring to H1 pins 2/4 or 11, and no connection to reserved wake pads. Verify pin 1.'),('2  FIRST POWER','Disconnect all Pi power before fitting/removing carrier or U1. With sensors and U1 unplugged, fit carrier, power Pi and check 3.3 V at U1. Power off before inserting U1. No external 3.3 V when stacked.')]),(440,370,[('3  FUEL / BRAKE BENCH','At 3.3 V, 110 ohms across J2 predicts 0.327 V at A0 with 1k R1; open approaches 3.3 V, short 0 V. Original gauge must be disconnected. GPIO27 input: brake switch open about 3.3 V, closed about 0 V; a disconnected wire also reads normal.'),('4  OIL AND CALIBRATION','Dweekiy B07ZYWMV89 is one-wire, body-grounded; its curve and bias are unknown. Keep R3 empty and sensor unplugged. Fuel 110 ohms was observed VERY empty; factory 7/32.5/95 ohm float inspection points do not establish a volume curve.'),('LIMITS / DATA','No validated automotive transient or overvoltage protection. Confirm sensor ground reference before vehicle use. Module bypass and I2C pull-ups are relied upon but values unverified. GPIO27 availability and numeric TSDash ingestion unverified. Automatic shutdown remains disabled; this build changes no power policy.')])]
    for x,width,blocks in columns:
        y=H-88
        for title,body in blocks: text(x,y,title,9,navy,True); y=para(x,y-14,body,width,8.6)-16
    c.save()
def main():
    OUT.mkdir(parents=True,exist_ok=True);TMP.mkdir(parents=True,exist_ok=True);PDF.parent.mkdir(parents=True,exist_ok=True)
    report=validate();native();report['native_roundtrip_pin_order_and_wire_endpoints_verified']=True
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');pdf();print(json.dumps(report,indent=2))
if __name__=='__main__':main()
