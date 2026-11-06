#!/usr/bin/env python3
"""Generate Rev G editable DIYLC layout, connectivity report, and guide."""
import json, math, subprocess
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import simpleSplit

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs/hardware/ads1115/revG'; TMP=ROOT/'tmp/pdfs/ads1115-revG'; PDF=ROOT/'output/pdf/ADS1115_sensor_board_revG_soldering_guide.pdf'; JAR='/Applications/DIYLC.app/Contents/Java/diylc.jar'
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
    expected={'3V3':{'H1.0','U1.0','R1.0','R3.0','R5.0'},'GND':{'H1.8','U1.1','U1.4','J2.1','J3.1','J4.1'},'SCL':{'H1.4','U1.2'},'SDA':{'H1.2','U1.3'},'FUEL':{'J2.0','R1.1','U1.6'},'OIL':{'J3.0','R3.1','U1.7'},'BRAKE':{'H1.12','J4.0','R5.1'},'WAKE_BTN':{'J5.0','J6.0'},'WAKE_RETURN':{'J5.1','J6.1'},'TRIGGER_PLUS':{'J7.0','C6.0','R7.0'},'TRIGGER_RETURN':{'J7.1','R7.1','D1.1','R9.1'},'CAP_MINUS':{'C6.1','R8.0'},'OPTO_INPUT_PLUS':{'R8.1','D1.0','R9.0'}}
    grouped={frozenset(v) for v in actual.values()}; assert all(frozenset(v) in grouped for v in expected.values()),actual
    # Bare buses may contact intermediate pads: no other-net terminal may occupy them.
    terminal_coords=set(pins.values())|{xy(w['path'][k]) for w in wires for k in (0,-1)}
    for bus in buses:
        taps=list(map(xy,bus['taps'])); y=taps[0][1]; x1,x2=taps[0][0],taps[-1][0]
        assert all(root(q)==root(taps[0]) for q in terminal_coords if q[1]==y and x1<=q[0]<=x2), (bus['ref'],terminal_coords)
    expected_pins=set().union(*expected.values()); assert all(len(v)==1 for v in actual.values() if not (v&expected_pins))
    for w in wires:
        assert root(xy(w['path'][0]))==root(xy(w['path'][-1]))
        assert root(xy(w['path'][0]))==root(pins[next(iter(expected[w['net']]))])
    oil=next(w for w in wires if w['ref']=='W18')
    for name,q in pins.items():
        if q in (xy(oil['path'][0]),xy(oil['path'][-1])): continue
        for a,b in zip(oil['path'],oil['path'][1:]):
            cross=(q[0]-a[0])*(b[1]-a[1])-(q[1]-a[1])*(b[0]-a[0])
            on_segment=(cross==0 and min(a[0],b[0])<=q[0]<=max(a[0],b[0]) and min(a[1],b[1])<=q[1]<=max(a[1],b[1]))
            assert not on_segment, ('W18 crosses component terminal',name,q)
    return {'schema_version':1,'electrical_connectivity_model_passed':True,'W18_intermediate_component_terminal_clearance_checked':True,'model_scope':'Endpoints and individual bus tap segments; insulated bends and crossings are not connections. Components do not electrically short their two terminals.','expected_nets':{k:sorted(v) for k,v in expected.items()},'unconnected_pins':sorted(set(pins)-expected_pins),'bus_segments':sum(len(b['taps'])-1 for b in buses),'fitted_resistors':['R1 1k bench','R5 10k','R7 10k 0.25W','R8 470 ohm >=0.5W','R9 4.7k >=0.25W'],'optional_parts_unfitted':['R3'],'fitted_links':[],'fuel_expected_V_at_110ohm_and_3_3V':3.3*110/1110,'physical_build_or_electrical_test_performed':False,'mechanical_fit_verified':False,'gpio27_availability_verified':False,'formal_hat_compliance':False}
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
static void resistor(String n,int v,int[] a){Resistor r=new Resistor();r.setName(n);r.setValue(new Resistance(v/1000.0,ResistanceUnit.K));r.setDisplay(n.equals("R7")||n.equals("R8")||n.equals("R9")?Display.NAME:Display.BOTH);if(n.equals("R8"))r.setLength(new Size(9.,SizeUnit.mm));if(n.equals("R9")){r.setPower(org.diylc.components.passive.Power.QUARTER);r.setLength(new Size(6.3,SizeUnit.mm));r.setWidth(new Size(2.5,SizeUnit.mm));}r.setControlPoint(p(a[0],a[1]),0);r.setControlPoint(p(a[2],a[3]),1);pr.getComponents().add(r);}
static void cap(String n,int[] a){RadialElectrolytic c=new RadialElectrolytic();c.setName(n);c.setValue(new Capacitance(220.,CapacitanceUnit.uF));c.setVoltageNew(new org.diylc.core.measures.Voltage(25.,org.diylc.core.measures.VoltageUnit.V));c.setPolarized(true);c.setInvert(false);c.setWidth(new Size(8.,SizeUnit.mm));c.setLength(new Size(8.,SizeUnit.mm));c.setControlPoint(p(a[0],a[1]),0);c.setControlPoint(p(a[2],a[3]),1);pr.getComponents().add(c);}
static void diode(String n,int[] a){DiodeGlass d=new DiodeGlass();d.setName(n);d.setValue("1N4148");d.setControlPoint(p(a[2],a[3]),0);d.setControlPoint(p(a[0],a[1]),1);pr.getComponents().add(d);}
static void pad(String n,int x,int y){SolderPad s=new SolderPad();s.setName(n);s.setControlPoint(p(x,y),0);pr.getComponents().add(s);}
static void wire(String n,int rgb,int[] a){HookupWire w=new HookupWire();w.setName(n);String[] en={"","","TWO","THREE","FOUR","FIVE","SIX","SEVEN"};w.setPointCount(org.diylc.components.AbstractCurvedComponent.PointCount.valueOf(en[a.length/2]));w.setSmooth(false);w.setValue(AWG._26);w.setLeadColor(new Color(rgb));w.setAlpha(new Percentage(70));for(int i=0;i<a.length/2;i++)w.setControlPoint(p(a[2*i],a[2*i+1]),i);pr.getComponents().add(w);}
public static void main(String[]a)throws Exception{org.diylc.appframework.miscutils.ConfigurationManager.getInstance().initialize(a[0]+"/config.xml");pr.setTitle("TurboExo ADS1115 compact carrier Rev G");pr.setFileVersion(new org.diylc.appframework.update.VersionNumber(6,9,0));pr.setAuthor("TurboExo");pr.setWidth(new Size(180.,SizeUnit.mm));pr.setHeight(new Size(115.,SizeUnit.mm));pr.setGridSpacing(new Size(.1,SizeUnit.in));pr.setDescription("REV G: external optocoupler and Pi J2 require separate pigtails. Charger trigger isolated from Pi rails. 24x18 individual pad board. TOP coordinate view. Colored wires are insulated underneath; bends/crossings are not soldered. P_BUS and G_BUS segments form bare continuous buses joined only at listed taps. Fuel/oil connect directly to A0/A1. R3 oil bias empty. J5/J6 passive isolated Pi J2 extension, separate two-wire lead. No formal HAT compliance. Physical fit and electrical tests not performed. See guide.");PerfBoard b=new PerfBoard();b.setName("B1");b.setCoordinateDisplay(AbstractBoard.CoordinateDisplay.None);b.setControlPoint(new Point2D.Double(X,Y),0);b.setControlPoint(new Point2D.Double(X+25*S,Y+19*S),1);pr.getComponents().add(b);
org.diylc.components.shapes.Rectangle wakeZone=new org.diylc.components.shapes.Rectangle();wakeZone.setName("Wake-area-outline");wakeZone.setControlPoint(p(13.6,3.7),0);wakeZone.setControlPoint(p(24.3,9.7),1);wakeZone.setColor(new Color(0xFFF2DF));wakeZone.setBorderColor(new Color(0xD7B37C));pr.getComponents().add(wakeZone);
WIRECALLS
org.diylc.components.shapes.Rectangle outline=new org.diylc.components.shapes.Rectangle();outline.setName("U1-envelope-approx");outline.setControlPoint(p(1.5,4.5),0);outline.setControlPoint(p(13.5,9.5),1);outline.setColor(new Color(0xE3EFF8));outline.setBorderColor(new Color(0x245C8D));pr.getComponents().add(outline);
PARTCALLS
for(int i=1;i<=24;i++)label(""+i,X+i*S-4,Y-10,9);for(int i=1;i<=18;i++)label(""+i,X-24,Y+i*S+3,9);
label("ADS1115 COMPACT CARRIER - REV G",90,43,20);label("TOP VIEW; wires underneath; coordinates = (column,row)",90,70,13);label("H1: pin 1 (2,3); female below, male stacking pins above",90,92,13);
String[] note={"COMPLETE CIRCUIT - REV G", "Full circuit + R9 input leakage shunt", "", "SENSORS / HEADER", "H1: female below, male pins above", "Pi: 1=3V3  3=SDA  5=SCL", "9=GND  13=GPIO27 brake", "R1 fuel 1k; R5 brake 10k", "R3 oil bias: empty pending curve", "Fuel/oil wired directly to A0/A1", "", "WAKE CIRCUIT - INCLUDED", "J5 -> Pi dedicated J2 (2 wires)", "J6 <- optocoupler OUT / GND", "J7 <- switched regulated trigger", "R7 10k bleed; R8 470 >=0.5W", "R9 4.7k across INPUT+ / INPUT-", "C6 220uF >=25V: + at (17,6)", "D1 1N4148: band at (21,5)", "External optocoupler VCC: unused", "", "ASSEMBLY", "Short red 3V3 / gray GND buses", "All other jumpers insulated underneath", "Only endpoints are solder joints", "Wake behavior still requires testing"};for(int i=0;i<note.length;i++)label(note[i],635,120+i*19,i==0?15:11);
label("J5 PI J2",365,211,9);label("J6 OPTO",365,334,9);label("J7 TRIGGER",515,211,8);
label("J2 FUEL",193,545,11);label("J3 OIL",353,545,11);label("J4 BRAKE",505,545,11);
label("1",X+S,Y+3*S+5,12);label("U1 ADS1115 module",X+2*S,Y+6*S,15);label("Approximate body; verify fit",X+2*S,Y+7*S,11);label("VDD left; A3 right",X+2*S,Y+8*S,11);
String xml=ProjectFileManager.xStreamSerializer.toXML(pr);Files.writeString(Path.of(a[1]),"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"+xml);Project copy=(Project)ProjectFileManager.xStreamSerializer.fromXML(xml);if(copy.getComponents().size()!=pr.getComponents().size())throw new Exception("roundtrip");try(var out=new PrintWriter(a[0]+"/native-endpoints.tsv")){for(var c:copy.getComponents())for(int i=0;i<c.getControlPointCount();i++)if(c.isControlPointSticky(i)){Point2D q=c.getControlPoint(i);out.printf(Locale.US,"%s\t%d\t%.4f\t%.4f\t%s%n",c.getName(),i,(q.getX()-X)/S,(q.getY()-Y)/S,c.getControlPointNodeName(i));}}
BufferedImage im=new BufferedImage(1050,650,BufferedImage.TYPE_INT_RGB);Graphics2D g=im.createGraphics();g.setColor(Color.WHITE);g.fillRect(0,0,1050,650);g.setClip(0,0,1050,650);g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON);IDrawingObserver o=new IDrawingObserver(){public void stopTracking(){}public void startTracking(){}public void startTrackingContinuityArea(boolean b){}public void stopTrackingContinuityArea(){}public boolean isTrackingContinuityArea(){return false;}public void setContinuityMarker(String s){}};for(var c:copy.getComponents())c.draw(g,ComponentState.NORMAL,false,copy,o);g.dispose();ImageIO.write(im,"png",new File(a[2]));}}
'''.replace('WIRECALLS','\n'.join(wc)).replace('PARTCALLS','\n'.join(calls))
    (TMP/'BuildHat.java').write_text(src);subprocess.run(['javac','-cp',JAR,str(TMP/'BuildHat.java')],check=True);subprocess.run(['java','-Djava.awt.headless=true','-cp',JAR+':'+str(TMP),'BuildHat',str(TMP),str(OUT/'ADS1115_sensor_board_revG.diy'),str(OUT/'ADS1115_native_preview.png')],check=True)
    obs={}
    for line in (TMP/'native-endpoints.tsv').read_text().splitlines():
        ref,i,x,y,*rest=line.split('\t');obs[(ref,int(i))]=(float(x),float(y),rest[0] if rest else '')
    for p in parts:
        for i,pos in enumerate(p['pins']):
            key=(p['ref'],1-i if p['kind']=='diode' else i) if p['kind'] not in ('reserved_resistor','reserved_capacitor') else (p['ref']+'.'+str(i),0)
            assert obs[key][:2]==tuple(pos),(key,obs[key],pos)
            if p['kind'] in ('electrolytic','diode'):assert obs[key][2]==p['names'][i],(key,obs[key])
            if p['kind']=='hat':assert obs[key][2]==str(i+1),(key,obs[key])
    for w in wires:
        keys=[k[1] for k in obs if k[0]==w['ref']];assert keys==[0,len(w['path'])-1],(w['ref'],keys)
    for b in buses:
        for i,(a,z) in enumerate(zip(b['taps'],b['taps'][1:])):
            ref=b['ref']+'_'+str(i+1);assert obs[(ref,0)][:2]==tuple(a) and obs[(ref,1)][:2]==tuple(z)
def pdf():
    W,H=landscape(A4); c=canvas.Canvas(str(PDF),pagesize=(W,H));navy=HexColor('#173a52');gray=HexColor('#394b58');c.setTitle('TurboExo ADS1115 compact carrier Rev G')
    def text(x,y,s,size=9,col=gray,bold=False):c.setFillColor(col);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,s)
    def para(x,y,s,width=245,size=9):
        for line in simpleSplit(s,'Helvetica',size,width):text(x,y,line,size);y-=size+3
        return y
    def head(n,title,sub):
        c.setFillColor(navy);c.rect(0,H-62,W,62,fill=1,stroke=0);text(26,H-28,title,18,white,True);text(26,H-47,sub,9,white);text(26,18,'TURBOEXO  /  ADS1115 CARRIER  /  REV G  /  2026-11-01',8);text(W-65,18,f'{n} / 6',8)
    def board(mirror=False,wireview=False):
        x0,y0,s=48,115,19
        def pt(q):x,y=q;return x0+(24-x if mirror else x-1)*s,y0+(18-y)*s
        c.setFillColor(HexColor('#f5f0e4'));c.setStrokeColor(HexColor('#d6c8ad'));c.roundRect(x0-10,y0-10,23*s+20,17*s+20,4,fill=1)
        for y in range(1,19):
            for x in range(1,25):
                a,b=pt((x,y));c.setFillColor(HexColor('#bca87c'));c.circle(a,b,2,fill=1,stroke=0)
        for x in range(1,25):a,b=pt((x,1));c.setFont('Helvetica',7);c.setFillColor(gray);c.drawCentredString(a,b+19,str(x))
        for y in range(1,19):a,b=pt((1,y));text(x0-23,b-2,str(y),7);text(x0+23*s+15,b-2,str(y),7)
        a,b=pt((1,1));c.setFillColor(navy);c.circle(a,b,5,fill=1,stroke=0)
        if wireview:
            for bus in buses:
                pts=list(map(pt,bus['taps']));c.setStrokeColor(HexColor('#'+colors[bus['net']]));c.setLineWidth(3);c.line(*pts[0],*pts[-1]);
                for a,b in pts:c.setFillColor(HexColor('#'+colors[bus['net']]));c.circle(a,b,3,fill=1,stroke=0)
            for w in wires:
                pts=list(map(pt,w['path']))
                for color,width in [(white,3.5),(HexColor('#'+colors[w['net']]),1.4)]:
                    c.setStrokeColor(color);c.setLineWidth(width);path=c.beginPath();path.moveTo(*pts[0]);
                    for q in pts[1:]:path.lineTo(*q)
                    c.drawPath(path)
                for a,b in (pts[0],pts[-1]):c.setFillColor(HexColor('#'+colors[w['net']]));c.circle(a,b,2.6,fill=1,stroke=0)
            for p in parts:
                for q in p['pins']:a,b=pt(q);c.setStrokeColor(navy);c.setLineWidth(.5);c.circle(a,b,3.5,stroke=1,fill=0)
            # Quiet pad labels on the mirrored solder view; no electrical changes.
            for p in parts:
                if p['kind'] not in ('resistor','reserved_resistor','electrolytic','diode'): continue
                for i,q in enumerate(p['pins']):
                    label=p['ref']
                    if p['kind'] in ('electrolytic','diode'): label+=' '+p['names'][i]
                    a,b=pt(q)
                    dx,dy = (-15,5) if p['ref']=='R7' and i==0 else ((-14,-9) if p['ref']=='R8' and i==0 else (5,5))
                    text(a+dx,b+dy,label,5.5,HexColor('#85898b'))
        else:
            a,b=pt((1.5,4.5));d,e=pt((13.5,9.5));c.setFillColor(HexColor('#e3eff8'));c.setStrokeColor(HexColor('#245c8d'));c.roundRect(a,e,d-a,b-e,3,fill=1)
            text(a+8,b-18,'U1 ADS1115 module',11,navy,True);text(a+8,b-33,'Approximate body / check actual fit',7);text(a+8,b-47,'VDD at left; A3 at right',8)
            for p in parts:
                pts=list(map(pt,p['pins']));xs,ys=zip(*pts)
                if p['kind'] in ('hat','header'):
                    c.setFillColor(HexColor('#324b5b'));c.setStrokeColor(navy);c.roundRect(min(xs)-6,min(ys)-6,max(xs)-min(xs)+12,max(ys)-min(ys)+12,2,fill=1)
                    for a,b in pts:c.setFillColor(HexColor('#e7bd58'));c.rect(a-2,b-2,4,4,fill=1,stroke=0)
                    if p['kind']=='hat':
                        a,b=pts[0];c.setFillColor(HexColor('#C33D3D'));c.rect(a-3,b-3,6,6,fill=1,stroke=0);text(a-13,b-3,'1',8,HexColor('#C33D3D'),True)
                elif p['kind']=='resistor':
                    (a,b),(d,e)=pts;c.setStrokeColor(gray);c.setLineWidth(1);c.line(a,b,d,e);c.setFillColor(HexColor('#e9d399'));c.saveState();c.translate((a+d)/2,(b+e)/2);c.rotate(math.degrees(math.atan2(e-b,d-a)));body_length = p.get('max_body_length_mm', 28 * 2.54 / s) * s / 2.54; body_width = p.get('max_body_diameter_mm', 12 * 2.54 / s) * s / 2.54;c.roundRect(-body_length/2,-body_width/2,body_length,body_width,3,fill=1);c.restoreState()
                elif p['kind']=='electrolytic':
                    (a,b),(d,e)=pts;c.setFillColor(HexColor('#b8d0d3'));c.setStrokeColor(navy);c.circle((a+d)/2,(b+e)/2,29.92,fill=1,stroke=1);text(a-3,b-3,'+',9,navy,True);text(d-3,e-3,'-',9,navy,True)
                elif p['kind']=='diode':
                    (a,b),(d,e)=pts;c.setStrokeColor(navy);c.setLineWidth(3);c.line(a,b,d,e);text(a+4,b,'K',7,navy,True);text(d+4,e,'A',7,navy,True)
                else:
                    for a,b in pts:c.setStrokeColor(HexColor('#a75544'));c.setLineWidth(1.5);c.circle(a,b,4,stroke=1,fill=0)
            # compact labels positioned away from component bodies
            for q,label in [((2,1.3),'H1: pin 1 is inner row 3'),((6.5,12.7),'R1'),((14,12.7),'R3 EMPTY'),((22.5,12.7),'R5'),((6,18.0),'J2'),((14,18.0),'J3'),((22,18.0),'J4'),((14,5.2),'J5'),((14,8.3),'J6'),((22,5.2),'J7'),((17,7.6),'C6'),((23,7.5),'R7'),((14,6.7),'R9'),((18,9.8),'R8'),((21,7.1),'D1')]:
                a,b=pt(q);text(a,b,label,7,navy,True)
        return pt
    head(1,'Placement - TOP side','24 x 18 individual pads, 2.54 mm pitch. Coordinates are (column,row) from the marked corner.')
    board();x,y=535,H-87
    for title,body in [('STACKING HEADER','H1 female socket below; male stacking pins above for existing UPS jumpers. Odd pins lie on row 3, even on row 2. Pin 1 = (2,3); pin 2 = (2,2). Verify Pi pin 1 and actual fit before mating.'),('ADS1115','U1 socket (3,10) to (12,10): VDD, GND, SCL, SDA, ADDR, ALRT, A0, A1, A2, A3. Check your module pin order and body clearance before soldering.'),('FITTED / EMPTY','R1 = removable 1k fuel bench bias; R5 = 10k brake pull-up. Wake: R7 10k, R8 470 ohm, R9 4.7k, C6 220uF, D1 1N4148. R3 oil bias stays EMPTY. W12 connects fuel directly to A0; W18 connects oil directly to A1.'),('CONNECTORS','J2 fuel, J3 oil temperature, J4 brake: left signal, right ground. Leave J3 unplugged. J5/J6 are the isolated Pi J2 extension. J7 is the switched regulated charger trigger. External optocoupler stays offboard. See page 5.'),('MECHANICAL','Hole span 58.42 x 43.18 mm. Dry-fit header height, UPS jumpers, cooler, module and standoffs. Dry-fit J5 beside H1 and the R1 sockets beside U1. R9 leaves only 0.66 mm per end for bends at its maximum body size; do not force leads. This is not a formally compliant HAT.')]:
        text(x,y,title,9,navy,True);y=para(x,y-14,body,275,8.4)-12
    c.showPage();head(2,'Wiring - SOLDER side','Mirrored left/right. Flip like a book with the top edge held at the top; the marked corner moves to the upper right.')
    board(True,True);x,y=535,H-88
    for title,body in [('BARE BUSES','3V3 row 11: continuous bare wire from (3,11) to (22,11); solder only taps (3,11), (6,11), (14,11), (22,11). GND row 16: continuous bare wire (4,16) to (23,16); solder only taps (4,16), (7,16), (15,16), (23,16).'),('INSULATED JUMPERS','All colored routes except the buses are insulated. Strip and solder only the endpoints listed on page 3. Attach wire ends beside component leads at underside pads, not all through the holes. Bends and crossings are not connections. Keep signal jumper insulation intact where it crosses a bare bus. Keep non-rail component leads off the bus rows; solder the listed taps.'),('SENSOR CONNECTIONS','W12 runs from fuel bias/signal (6,15) directly to A0 (9,10). W18 route: (14,15) -> (18,15) -> (18,12) -> (10,12) -> A1 (10,10). Keep insulation intact over the 3V3 bus at (10,11). R3 stays empty; J3 stays unplugged.'),('WAKE PAIR','W23 and W24 are separate isolated circuits. J5 connects by a separate lead to Pi 5 J2; J6 accepts the isolated external optocoupler OUT/GND contact. No 3.3 V, 5 V, 12 V or carrier ground to this pair. Inspect any existing J2 circuit before connecting this parallel contact.')]:
        text(x,y,title,9,navy,True);y=para(x,y-14,body,275,8.5)-14
    c.showPage();head(3,'Wire and bus checklist','Coordinates retain TOP-view numbering. Endpoints only are electrical joints; route bends as needed with insulation intact.')
    def fmt(p):return '('+','.join(map(str,p))+')'
    for block,subset in enumerate((wires[:16],wires[16:])):
        x=28+block*400;y=H-90;text(x,y,'REF / NET',9,navy,True);text(x+140,y,'FROM',9,navy,True);text(x+230,y,'TO',9,navy,True);y-=22
        for w in subset:
            c.setStrokeColor(HexColor('#c9d2d8'));c.line(x,y-7,x+370,y-7);c.rect(x,y-1,7,7,fill=0);text(x+14,y,w['ref']+'  '+w['net'],8,HexColor('#'+colors[w['net']]));text(x+140,y,fmt(w['path'][0]),9);text(x+230,y,fmt(w['path'][-1]),9);y-=18
    text(28,142,'BARE BUS TAP CHECKLIST',10,navy,True)
    for i,b in enumerate(buses):text(28,122-i*18,b['ref']+'  '+b['net']+'   '+ ' - '.join(map(fmt,b['taps'])),9)
    text(28,70,'W12 and W18 are direct sensor-to-ADC wires. Do not connect Pi 5 V pins 2 or 4.',9,navy,True)
    text(28,52,'GPIO17 / physical pin 11 is not wired. GPIO27 / physical pin 13 is proposed; verify availability first.',9)
    c.showPage();head(4,'Checks, limits and power','Calculated expectations only. No physical build, electrical measurement, software configuration or vehicle test has been performed.')
    columns=[(28,395,[('1  INSPECT / CONTINUITY','With the carrier unplugged from the Pi, J2 wake circuit, UPS and sensors, check all wires and buses. Confirm no 3V3-to-GND short and no J5/J6 continuity to carrier rails or H1. Verify header pin 1; no board wires on pins 2/4 or 11.'),('2  FIRST POWER','Disconnect ALL Pi power before fitting/removing H1 or U1. With sensors and U1 unplugged, fit the carrier and power the Pi; check 3.3 V at U1. Power OFF to insert U1. No external 3.3 V when stacked. ADC: 0x48, +/-4.096 V range.'),('3  FUEL BENCH CHECK','R1 = 1k, supply 3.3 V and 110 ohms across J2 predicts 3.3 x 110 / (1000 + 110) = 0.327 V at A0. Open approaches 3.3 V; short approaches 0 V. This is a bench starting point, not tank calibration.'),('4  BRAKE / OIL','With GPIO27 confirmed free and configured as input, isolated brake contact open gives about 3.3 V; closed about 0 V. An unplugged contact also reads open. R3 stays empty and J3 disconnected until its resistance-temperature curve and bias are established.')]),(445,365,[('POWER BUTTON / WAKE','The Pi 5 power button connects separately at its J2 pads. J5/J6 only extend a dry momentary contact; a 40-pin GPIO is not a Pi 5 wake input. The proposed charger-edge network uses an external optocoupler. See wake circuit page; automatic wake remains unverified.'),('OPERATING LIMITS','Use isolated sender/switch circuits only, not powered gauges or 12 V signals. No automotive fault or transient protection is claimed. No additional supply capacitors, I2C pull-ups or EEPROM are fitted. The module bypass is relied on; its value is unverified. Pi 5V remains passthrough only.'),('SOURCES','TI ADS1115 datasheet; Raspberry Pi power button, bootloader and GPIO documentation; Mazda 1999-2001 workshop manual. R9 leakage/current calculations are in scripts/analyze_wake_pulse.py. Full URLs are in layout_spec.json.')])]
    for x,width,blocks in columns:
        y=H-88
        for title,body in blocks:text(x,y,title,9,navy,True);y=para(x,y-14,body,width,8.7)-15
    text(28,181,'NOMINAL MATH AT 3.300 V',9,navy,True)
    math_rows=['Fuel at 110 ohms: 0.327 V; 2.973 mA through sender.',
               'Power: 0.972 mW in sender; 8.84 mW in the 1k resistor.',
               'Shorted fuel: 3.30 mA; 10.89 mW in the 1k resistor.',
               'Closed brake: 0.330 mA; 1.089 mW in the 10k resistor.',
               'Divider: Vout = Vs x Rs / (Rpull + Rs); I = Vs / (Rpull + Rs).',
               'These are ideal circuit calculations, not measured results.']
    for i,line in enumerate(math_rows):text(28,165-16*i,line,8.4)
    text(445,181,'DATA STILL NEEDED',9,navy,True)
    para(445,166,'Fuel factory points: full 7 ohms, half 32.5 ohms, empty 95 ohms (09-22-7); initial gauge calibration, not liters. User observed 110 ohms when VERY empty. Oil is Dweekiy B07ZYWMV89, one stud with thread/body ground; its resistance-temperature curve is still missing.',365,8.3)
    para(445,120,'Electrical: measured 3.3 V at the board, actual resistor values, module bypass/pull-up details. Fit: stacking-header height, cooler clearance and GPIO27 availability.',365,8.3)
    para(445,74,'Wake: exact UPS and PC817 module, existing schematic/resistors, charger-on voltage step, Pi 5 V in standby, and J2 pulse voltage/duration. Pi was unreachable for EEPROM/GPIO readback.',365,8.3)
    c.showPage();head(5,'Wake circuit and external leads','Complete proposed wake circuit is included. Physical fit and wake behavior have not been verified.')
    x,y=30,H-90
    blocks=[('CHARGER-SIDE NETWORK', 'J7 TRIG+ (22,4) -> C6 + (17,6); C6 - (19,6) -> R8 (16,9 to 21,9) -> external module INPUT+. J7 TRIG- (23,4) -> external module INPUT-. R7 10k 1/4W spans J7 TRIG+ and TRIG- BEFORE C6.'),('DIODE AND CAPACITOR POLARITY', 'C6 is 220uF, >=25V electrolytic, + at (17,6), - at (19,6), maximum 8mm diameter. D1 1N4148 banded cathode K at (21,5) connects INPUT+; anode A at (21,8) connects INPUT-. R8 is 470 ohms >=0.5W, body <=9mm. R9 is 4.7k >=1/4W from (15,5) to (15,8), parallel with D1 across INPUT+/INPUT-. R9 body <=6.3 x 2.5mm. Dry-fit before soldering.'),('EXTERNAL MODULE: SEPARATE PIGTAILS', 'From D1 K (21,5) run a lead to INPUT+; from D1 A (21,8) run a lead to INPUT-. OUT -> J6 BTN (14,9), GND -> J6 RETURN (15,9), VCC -> NO CONNECTION. J5 BTN (14,4) and RETURN (15,4) go by a separate two-wire lead to the Pi 5 dedicated J2 button signal and ground.'),('ISOLATION AND POWER', 'There is no intentional connection from charger trigger or return to H1 power, Pi rails or J2 return. Signal crosses only the external optocoupler. Charger and UPS may share a return elsewhere; no rated isolation claim. J7 is for a switched regulated nominal 12.6V charger trigger, NOT raw automotive power or a continuously live battery output.')]
    for title,body in blocks:text(x,y,title,10,navy,True);y=para(x,y-16,body,770,9.5)-18
    # Electrical sketch: separate domains are joined only by the external optocoupler.
    text(30,250,'ELECTRICAL SKETCH  /  arrows denote wired connections, not wire routing',10,navy,True)
    c.setStrokeColor(navy);c.setLineWidth(1)
    for yy,ss in [(224,'J7 + --+-- (+ C6 -) -- R8 470 --+------------+--> opto INPUT+'),(207,'       |                      |            |'),(190,'     R7 10k                 D1 K (band)   R9 4.7k'),(173,'       |                   D1 A            |'),(156,'J7 - --+----------------------+------------+--> opto INPUT-'),(128,'opto OUT ---- J6 BTN ---- J5 BTN ---- Pi J2 signal'),(110,'opto GND ---- J6 RETURN - J5 RETURN - Pi J2 ground'),(92,'opto VCC: NO CONNECTION')]:
        c.setFillColor(gray);c.setFont('Courier',10);c.drawString(40,yy,ss)
    c.showPage();head(6,'Wake build, test and BOM','Do not connect the Pi J2 lead until the isolated output pulse has been measured and released.')
    x,y=30,H-90
    blocks=[('BOM - CARRIER', 'H1 2x20 stacking header; U1 1x10 ADS1115 socket; J2/J3/J4/J5/J6/J7 two-pin connectors; R1 1k removable fuel bias, R5 10k brake pull-up, R7 10k 1/4W bleed, R8 470 ohm >=0.5W limiter; R9 4.7k >=1/4W input shunt; C6 220uF >=25V radial electrolytic; D1 1N4148. Leave R3 oil bias empty. Fuel/oil signal paths use direct insulated wires W12/W18.'),('EXTERNAL PART', 'Existing optocoupler module remains OFFBOARD. Its onboard R1 is a different part from carrier fuel-bias R1. A matching vendor image suggests module R1 is 1k, but the installed value, module input rating and exact chip marking have not been measured or confirmed.'),('BENCH SEQUENCE', 'Disconnect Pi J2 and module OUT/GND. Replace the old capacitor/diode pulse network; do not cascade it. Check polarity, insulation, continuity and separation of J7 from H1 and J5/J6 with power removed. Confirm the supplied Pi can wake from its own button/manual J2 closure. For a disconnected-output bench test, provide a temporary 10k pull-up from OUT to a regulated 3.3 V test supply and connect that supply return to module GND; leave module VCC unused. Observe OUT with an oscilloscope or edge logger while applying the regulated trigger: it must go low and release. A floating OUT has no valid HIGH reading. Remove the temporary pull-up before connecting J2, then verify real wake and repeat behavior.'),('OPERATING LIMITS', 'R9 diverts input leakage but reduces LED drive (nominal 5.78mA initially, 2.58mA at 200ms); this is not a guaranteed J2 pulse duration. A charger edge while the Pi is already running also presses its power button: this circuit does not sense Pi state. Confirm software handling and operating policy before unattended use. Pulse duration depends on the load, optocoupler transfer, LED drops, capacitor tolerance, source edge and previous charge; it is not simply the RC time constant. No automatic wake or physical fit is verified.')]
    for title,body in blocks:text(x,y,title,10,navy,True);y=para(x,y-16,body,770,9.5)-18
    c.save()
def main():
    OUT.mkdir(parents=True,exist_ok=True);TMP.mkdir(parents=True,exist_ok=True);PDF.parent.mkdir(parents=True,exist_ok=True)
    report=validate();native();report['native_roundtrip_pin_order_and_wire_endpoints_verified']=True
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');pdf();print(json.dumps(report,indent=2))
if __name__=='__main__':main()
