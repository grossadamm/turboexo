#!/usr/bin/env python3
"""Generate the reviewed, editable DIYLC perfboard layout and soldering guide.

Requires DIYLC 6.9's JAR, Java/Javac, and reportlab. This is a low-voltage
interface, not a qualified automotive-input protection design. Native file
creation uses DIYLC's serializer and component classes rather than guessed XML.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/hardware/ads1115"
TMP = ROOT / "tmp/pdfs/ads1115"
PDF = ROOT / "output/pdf/ADS1115_sensor_board_soldering_guide.pdf"
JAR = Path("/Applications/DIYLC.app/Contents/Java/diylc.jar")
COLS, ROWS = 30, 24
COLORS = {"3V3": "C33D3D", "GND": "394957", "SCL": "B48119", "SDA": "278858",
          "FUEL_RAW": "3378C5", "FUEL_ADC": "3378C5", "OIL_RAW": "9862B9",
          "OIL_ADC": "9862B9", "BRAKE_RAW": "CB6B28", "BRAKE_GPIO": "CB6B28"}

# Each electrical endpoint is (column,row), viewed from component side.
# Component leads have separate holes. Insulated wires attach to the solder
# pads occupied by leads; only their endpoints are stripped and soldered.
parts = [
    dict(ref="U1", kind="header", value="ADS1115 1x10 socket", pins=[(c,7) for c in range(11,21)],
         names=["VDD","GND","SCL","SDA","ADDR","ALRT","A0","A1","A2","A3"]),
    dict(ref="J1", kind="header", value="HOST 1x5", pins=[(3,r) for r in range(2,7)],
         names=["3V3","GND","SCL","SDA","BRAKE"]),
    dict(ref="J2", kind="header", value="FUEL 1x2", pins=[(3,13),(3,14)], names=["SIGNAL","GND"]),
    dict(ref="J3", kind="header", value="OIL TEMP 1x2 - DO NOT CONNECT YET", pins=[(3,20),(3,21)], names=["SIGNAL","GND"]),
    dict(ref="J4", kind="header", value="BRAKE 1x2", pins=[(28,18),(28,19)], names=["SWITCH","GND"]),
    dict(ref="R1", kind="resistor", value="1k - removable BENCH bias", ohms=1000, pins=[(6,9),(6,13)]),
    dict(ref="R2", kind="resistor", value="1k fuel series", ohms=1000, pins=[(10,13),(14,13)]),
    dict(ref="R3A", kind="header", value="Oil bias socket +3V3", pins=[(6,16)], names=["3V3"]),
    dict(ref="R3B", kind="header", value="Oil bias socket SIGNAL", pins=[(6,20)], names=["SIGNAL"]),
    dict(ref="R4", kind="resistor", value="1k oil series", ohms=1000, pins=[(10,20),(14,20)]),
    dict(ref="R5", kind="resistor", value="10k brake pull-up", ohms=10000, pins=[(24,11),(24,15)]),
    dict(ref="R6", kind="resistor", value="1k brake series", ohms=1000, pins=[(24,17),(24,21)]),
    dict(ref="C1", kind="capacitor", value="100nF fuel filter", pins=[(17,13),(17,15)]),
    dict(ref="C2", kind="capacitor", value="100nF oil filter", pins=[(17,20),(17,22)]),
    dict(ref="C3", kind="capacitor", value="100nF brake filter", pins=[(24,23),(26,23)]),
    dict(ref="C4", kind="capacitor", value="100nF supply bypass", pins=[(7,6),(9,6)]),
    dict(ref="C5", kind="electrolytic", value="10uF >=10V; + at (7,3)", pins=[(7,3),(9,3)]),
    dict(ref="TP1", kind="header", value="Ground junction", pins=[(28,9)], names=["GND"]),
]
wire_specs = [
 ("3V3",[(3,2),(5,2),(5,3),(7,3)]),
 ("3V3",[(7,3),(7,6)]),
 ("3V3",[(7,6),(7,7),(11,7)]),
 ("3V3",[(11,7),(11,9),(6,9)]),
 ("3V3",[(6,9),(8,9),(8,16),(6,16)]),
 ("3V3",[(6,16),(8,16),(8,10),(24,10),(24,11)]),
 ("GND",[(3,3),(3,1),(9,1),(9,3)]),
 ("GND",[(9,3),(9,6)]),
 ("GND",[(9,6),(9,8),(12,8),(12,7)]),
 ("GND",[(12,7),(12,8),(15,8),(15,7)]),
 ("GND",[(15,7),(15,9),(28,9)]),
 ("GND",[(28,9),(30,9),(30,19),(28,19)]),
 ("GND",[(28,19),(28,23),(26,23)]),
 ("GND",[(26,23),(26,22),(17,22)]),
 ("GND",[(17,22),(19,22),(19,15),(17,15)]),
 ("GND",[(17,15),(17,17),(2,17),(2,21),(3,21)]),
 ("GND",[(3,21),(2,21),(2,14),(3,14)]),
 ("SCL",[(3,4),(4,4),(4,10),(13,10),(13,7)]),
 ("SDA",[(3,5),(5,5),(5,11),(14,11),(14,7)]),
 ("FUEL_RAW",[(3,13),(6,13)]),
 ("FUEL_RAW",[(6,13),(10,13)]),
 ("FUEL_ADC",[(14,13),(17,13)]),
 ("FUEL_ADC",[(17,13),(17,7)]),
 ("OIL_RAW",[(3,20),(6,20)]),
 ("OIL_RAW",[(6,20),(10,20)]),
 ("OIL_ADC",[(14,20),(17,20)]),
 ("OIL_ADC",[(17,20),(20,20),(20,9),(18,9),(18,7)]),
 ("BRAKE_RAW",[(24,15),(24,17)]),
 ("BRAKE_GPIO",[(24,21),(24,23)]),
 ("BRAKE_GPIO",[(24,23),(24,24),(1,24),(1,6),(3,6)]),
 ("BRAKE_RAW",[(28,18),(27,18),(27,15),(24,15)]),
]
wires = [dict(ref=f"W{i:02}",net=n,path=path) for i,(n,path) in enumerate(wire_specs,1)]
expected = {
 "3V3": ["J1.0","U1.0","R1.0","R3A.0","R5.0","C4.0","C5.0"],
 "GND": ["J1.1","U1.1","U1.4","J2.1","J3.1","J4.1","C1.1","C2.1","C3.1","C4.1","C5.1","TP1.0"],
 "SCL": ["J1.2","U1.2"], "SDA": ["J1.3","U1.3"],
 "FUEL_RAW": ["J2.0","R1.1","R2.0"], "FUEL_ADC": ["R2.1","C1.0","U1.6"],
 "OIL_RAW": ["J3.0","R3B.0","R4.0"], "OIL_ADC": ["R4.1","C2.0","U1.7"],
 "BRAKE_RAW": ["J4.0","R5.1","R6.0"], "BRAKE_GPIO": ["R6.1","C3.0","J1.4"],
}

def validate():
    pins = {f"{p['ref']}.{i}":tuple(xy) for p in parts for i,xy in enumerate(p['pins'])}
    assert len(set(pins.values())) == len(pins), 'Two component leads share a hole'
    assert all(1<=c<=COLS and 1<=r<=ROWS for c,r in pins.values())
    roots = {xy:xy for xy in pins.values()}
    def root(x):
        while roots[x]!=x:
            roots[x]=roots[roots[x]]; x=roots[x]
        return x
    for w in wires:
        a,b=map(tuple,(w['path'][0],w['path'][-1]))
        assert a in roots and b in roots, (w['ref'],'wire endpoint has no terminal')
        roots[root(a)]=root(b)
    actual={}
    for name,xy in pins.items(): actual.setdefault(root(xy),set()).add(name)
    wanted=list(map(set,expected.values())) + [{f"U1.{i}"} for i in (5,8,9)]
    assert {frozenset(x) for x in actual.values()} == {frozenset(x) for x in wanted}, actual
    # Verify printed wire color/net labels independently of their geometry.
    declared={pin:net for net,ps in expected.items() for pin in ps}
    coord_net={pins[k]:v for k,v in declared.items()}
    for w in wires:
        assert coord_net[tuple(w['path'][0])]==coord_net[tuple(w['path'][-1])]==w['net']
    endpoint_counts={}
    for w in wires:
        for xy in (w['path'][0],w['path'][-1]):
            key=tuple(xy);endpoint_counts[key]=endpoint_counts.get(key,0)+1
    assert max(endpoint_counts.values())<=2, 'Avoid crowding more than two wire ends onto one component pad'
    # Nominal electrical acceptance calculations; not physical measurements.
    v=3.3*110/(1000+110)
    assert abs(v-0.327027)<0.000001
    return {'component_leads':len(pins),'wires':len(wires),'electrical_nets':len(actual),
            'distinct_pads':True,'shorts_or_missing_links':False,'fuel_110ohm_expected_V':v,
            'brake_closed_expected_V':0.0,'brake_open_expected_V':3.3,
            'physical_test_performed':False,'oil_bias_installed':False,
            'max_jumper_ends_per_component_pad':max(endpoint_counts.values()),
            'body_clearance_physical_check_performed':False}

def java_string(s): return json.dumps(s)

def build_native():
    calls=[]
    for p in parts:
        xy=','.join(f"{c},{r}" for c,r in p['pins'])
        ref=java_string(p['ref'])
        if p['kind']=='header':
            calls.append(f"header({ref},{java_string(','.join(p['names']))},new int[]{{{xy}}});")
        elif p['kind']=='resistor': calls.append(f"resistor({ref},{p['ohms']},new int[]{{{xy}}});")
        else: calls.append(f"capacitor({ref},{str(p['kind']=='electrolytic').lower()},new int[]{{{xy}}});")
    wire_calls=[]
    for w in wires:
        xy=','.join(f"{c},{r}" for c,r in w['path'])
        wire_calls.append(f"wire({java_string(w['ref'])},0x{COLORS[w['net']]},new int[]{{{xy}}});")
    source=r'''
import java.awt.*; import java.awt.geom.*; import java.awt.image.*; import java.io.*;
import java.nio.file.*; import javax.imageio.ImageIO; import java.util.*;
import org.diylc.core.*; import org.diylc.core.measures.*; import org.diylc.common.*;
import org.diylc.components.boards.*; import org.diylc.components.electromechanical.*;
import org.diylc.components.passive.*; import org.diylc.components.misc.*;
import org.diylc.components.connectivity.*; import org.diylc.serialization.*;
public class BuildSensorBoard {
 static Project pr=new Project(); static double X=120,Y=140,S=20;
 static Point2D p(double c,double r){return new Point2D.Double(X+c*S,Y+r*S);}
 static void label(String text,double x,double y,int size,Color color){
  org.diylc.components.misc.Label l=new org.diylc.components.misc.Label();l.setValue(text);
  l.setFontSize(size);l.setColor(color);l.setHorizontalAlignment(HorizontalAlignment.LEFT);
  l.setControlPoint(new Point2D.Double(x,y),0);pr.getComponents().add(l);
 }
 static void header(String name,String names,int[]xy){
  PinHeader h=new PinHeader();h.setName(name);h.setRowCount(1);h.setColumnCount(xy.length/2);
  if(xy.length>2 && xy[0]!=xy[2])h.setOrientation(Orientation._270);
  for(int i=0;i<xy.length/2;i++)h.setControlPoint(p(xy[2*i],xy[2*i+1]),i);
  h.setNodeNames(names);pr.getComponents().add(h);
 }
 static void resistor(String name,int ohms,int[]xy){
  Resistor r=new Resistor();r.setName(name);r.setValue(new Resistance(ohms/1000.0,ResistanceUnit.K));
  r.setDisplay(Display.BOTH);r.setControlPoint(p(xy[0],xy[1]),0);r.setControlPoint(p(xy[2],xy[3]),1);
  pr.getComponents().add(r);
 }
 static void capacitor(String name,boolean bulk,int[]xy){
  if(bulk){RadialElectrolytic c=new RadialElectrolytic();c.setName(name);c.setValue(new Capacitance(10.0,CapacitanceUnit.uF));
   c.setControlPoint(p(xy[0],xy[1]),0);c.setControlPoint(p(xy[2],xy[3]),1);pr.getComponents().add(c);
  }else{RadialCeramicDiskCapacitor c=new RadialCeramicDiskCapacitor();c.setName(name);c.setValue(new Capacitance(100.0,CapacitanceUnit.nF));
   c.setControlPoint(p(xy[0],xy[1]),0);c.setControlPoint(p(xy[2],xy[3]),1);pr.getComponents().add(c);}
 }
 static void wire(String name,int rgb,int[]xy){
  HookupWire w=new HookupWire();w.setName(name);String[] en={"","","TWO","THREE","FOUR","FIVE","","SEVEN"};
  w.setPointCount(org.diylc.components.AbstractCurvedComponent.PointCount.valueOf(en[xy.length/2]));
  w.setSmooth(false);w.setValue(AWG._26);w.setLeadColor(new Color(rgb));
  for(int i=0;i<xy.length/2;i++)w.setControlPoint(p(xy[2*i],xy[2*i+1]),i);
  pr.getComponents().add(w);
 }
 public static void main(String[]args)throws Exception{
  org.diylc.appframework.miscutils.ConfigurationManager.getInstance().initialize(args[0]+"/generator-config.xml");
  pr.setTitle("TurboExo ADS1115 sensor interface - Rev A / low-voltage bench build");
  pr.setFileVersion(new org.diylc.appframework.update.VersionNumber(6,9,0));
  pr.setAuthor("TurboExo");pr.setWidth(new Size(170.0,SizeUnit.mm));pr.setHeight(new Size(110.0,SizeUnit.mm));
  pr.setGridSpacing(new Size(0.1,SizeUnit.in));
  pr.setDescription("30x24 individual-pad perfboard. Coordinates are TOP view (column,row), 2.54mm pitch. All colored wires are INSULATED underside jumpers: solder endpoints only; crossings and bends are not connections. Socket U1 and R1. R1=1k bench candidate; leave R3 sockets EMPTY and J3 unplugged until oil-temperature sender is identified. Not 12V tolerant or automotive-transient-qualified. See companion soldering guide and wiring manifest. Do not connect ECU oil-pressure sensor to J3.");
  PerfBoard b=new PerfBoard();b.setName("B1");b.setCoordinateDisplay(AbstractBoard.CoordinateDisplay.None);b.setControlPoint(new Point2D.Double(X,Y),0);
  b.setControlPoint(new Point2D.Double(X+31*S,Y+25*S),1);pr.getComponents().add(b);
  // Draw jumper wiring before the top components in the saved component list.
  WIRE_CALLS
  org.diylc.components.shapes.Rectangle module=new org.diylc.components.shapes.Rectangle();
  module.setName("U1-body-outline");module.setControlPoint(p(9.4,1.5),0);module.setControlPoint(p(21.6,6.35),1);
  module.setColor(new Color(0xE3EFF8));module.setBorderColor(new Color(0x2C6793));pr.getComponents().add(module);
  PART_CALLS
  for(int rr:new int[]{9,13}){
   org.diylc.components.shapes.Rectangle socket=new org.diylc.components.shapes.Rectangle();
   socket.setName("R1-socket-"+rr);socket.setControlPoint(p(5.7,rr-0.3),0);socket.setControlPoint(p(6.3,rr+0.3),1);
   socket.setColor(new Color(0x344A5A));socket.setBorderColor(new Color(0xE7BB58));pr.getComponents().add(socket);
  }
  for(int c=1;c<=30;c++)label(""+c,X+c*S-5,Y-14,10,Color.DARK_GRAY);
  for(int r=1;r<=24;r++)label(""+r,X-25,Y+r*S+3,10,Color.DARK_GRAY);
  label("ADS1115 SENSOR INTERFACE | REV A",120,50,22,new Color(0x183A54));
  label("TOP / COMPONENT VIEW - colored jumpers go UNDERNEATH",120,82,14,Color.DARK_GRAY);
  label("30 x 24 separate pads | 2.54 mm pitch | coords = (column,row)",120,108,13,Color.DARK_GRAY);
  label("U1: ADS1115 module",320,190,17,new Color(0x245C8D));
  label("Body above socket; VDD at left",320,215,12,new Color(0x245C8D));
  label("Approximate outline; dry-fit",320,240,12,new Color(0x245C8D));
  String[] pins={"VDD","GND","SCL","SDA","ADDR","ALRT","A0","A1","A2","A3"};
  for(int i=0;i<10;i++)label(pins[i],X+(11+i)*S-9,Y+7*S+24+(i%2)*13,8,Color.BLACK);
  label("J1 HOST",130,163,12,new Color(0x183A54));
  label("J2 FUEL",133,379,12,new Color(0x3378C5));
  label("J3 OIL TEMP",130,519,12,new Color(0x9862B9));
  label("R3 EMPTY",222,505,12,new Color(0x9862B9));
  label("J4 BRAKE",635,475,12,new Color(0xCB6B28));
  label("C5 + at (7,3)",248,169,11,Color.BLACK);
  String[] notes={"ASSEMBLY NOTES","J1 top to bottom:","1  3.3 V ONLY","2  Ground","3  SCL","4  SDA","5  Brake GPIO","","J2/J3/J4: upper = signal", "lower = ground", "", "R1: 1k in two single-pin sockets", "R3: two EMPTY sockets", "R2/R4/R6: 1k series", "R5: 10k pull-up", "C1-C4: 100nF ceramic", "C5: 10uF, >=10V", "", "All jumpers: insulated wire", "Solder ONLY at endpoints", "No stripboard / shared rows", "", "Use isolated sensors only", "NO 5 V / 12 V inputs", "J3 disconnected until identified", "ALRT / A2 / A3 unused", "", "See PDF: mirrored solder side", "and wire-by-wire checklist"};
  for(int i=0;i<notes.length;i++)label(notes[i],800,150+18*i,i==0?16:12,Color.DARK_GRAY);
  label("R1 is a bench starting value, not a verified tank calibration. Oil section is unpopulated at R3.",120,683,12,new Color(0x9D4B13));
  label("A0=fuel | A1=oil temp (disabled until configured) | ADDR=GND -> 0x48 | power=3.3 V",120,708,12,Color.DARK_GRAY);
  String xml=ProjectFileManager.xStreamSerializer.toXML(pr);
  Files.writeString(Path.of(args[1]),"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"+xml);
  Project copy=(Project)ProjectFileManager.xStreamSerializer.fromXML(xml);
  if(copy.getComponents().size()!=pr.getComponents().size())throw new Exception("round-trip mismatch");
  // Record the real, deserialized sticky endpoints for independent inspection.
  try(var out=new PrintWriter(args[0]+"/native-endpoints.tsv")){
   for(var c:copy.getComponents())for(int i=0;i<c.getControlPointCount();i++)if(c.isControlPointSticky(i)){
    Point2D a=c.getControlPoint(i);out.printf(Locale.US,"%s\t%d\t%.4f\t%.4f\t%s%n",c.getName(),i,(a.getX()-X)/S,(a.getY()-Y)/S,c.getControlPointNodeName(i));}
  }
  BufferedImage img=new BufferedImage(1340,800,BufferedImage.TYPE_INT_RGB);Graphics2D g=img.createGraphics();
  g.setColor(Color.WHITE);g.fillRect(0,0,1340,800);g.setClip(0,0,1340,800);
  g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON);
  IDrawingObserver obs=new IDrawingObserver(){public void stopTracking(){}public void startTracking(){}public void startTrackingContinuityArea(boolean b){}public void stopTrackingContinuityArea(){}public boolean isTrackingContinuityArea(){return false;}public void setContinuityMarker(String s){}};
  for(var c:copy.getComponents())c.draw(g,ComponentState.NORMAL,false,copy,obs);
  g.dispose();ImageIO.write(img,"png",new File(args[2]));
  System.out.println("Native .diy round-trip OK: "+copy.getComponents().size()+" components");
 }
}
'''.replace('WIRE_CALLS','\n'.join(wire_calls)).replace('PART_CALLS','\n'.join(calls))
    (TMP/'BuildSensorBoard.java').write_text(source)
    subprocess.run(['javac','-cp',str(JAR),str(TMP/'BuildSensorBoard.java')],check=True)
    subprocess.run(['java','-Djava.awt.headless=true','-cp',f'{JAR}:{TMP}','BuildSensorBoard',str(TMP),
                    str(OUT/'ADS1115_sensor_board_revA.diy'),str(OUT/'ADS1115_native_preview.png')],check=True)
    # Confirm native serialization did not move pin-header endpoints.
    observed={}
    for line in (TMP/'native-endpoints.tsv').read_text().splitlines():
        ref,idx,x,y,*_=line.split('\t'); observed[(ref,int(idx))]=(float(x),float(y))
    for p in parts:
        for i,xy in enumerate(p['pins']): assert observed[(p['ref'],i)]==tuple(xy),(p['ref'],i,observed)
    for w in wires:
        # Only ends should be electrical nodes, never insulated routing bends.
        keys=[k[1] for k in observed if k[0]==w['ref']]
        assert keys==[0,len(w['path'])-1], (w['ref'],keys)

def make_pdf():
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor, Color, white
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.utils import simpleSplit
    W,H=landscape(A4); c=canvas.Canvas(str(PDF),pagesize=(W,H))
    c.setTitle('TurboExo ADS1115 sensor board - soldering guide Rev A')
    navy=HexColor('#183A54'); gray=HexColor('#425363')
    def text(x,y,s,size=9,color=gray,font='Helvetica'):
        c.setFillColor(color);c.setFont(font,size);c.drawString(x,y,s)
    def para(x,y,s,width=218,size=9,leading=12,color=gray):
        for ln in simpleSplit(s,'Helvetica',size,width):text(x,y,ln,size,color);y-=leading
        return y
    def heading(num,title,sub):
        c.setFillColor(navy);c.rect(0,H-64,W,64,fill=1,stroke=0)
        text(25,H-29,title,19,white,'Helvetica-Bold');text(25,H-48,sub,9,white)
        text(25,18,'TURBOEXO  /  ADS1115  /  REV A  /  2026-10-30',8)
        text(W-85,18,f'{num} / 4',8)
    def board(mirror=False,show_wires=False):
        x0,y0,pitch=43,70,16.0
        def pt(xy):
            col,row=xy;return x0+(COLS-col if mirror else col-1)*pitch,y0+(ROWS-row)*pitch
        c.setFillColor(HexColor('#F5F0E4'));c.setStrokeColor(HexColor('#D8CEB9'))
        c.roundRect(x0-12,y0-12,(COLS-1)*pitch+24,(ROWS-1)*pitch+24,5,fill=1)
        for row in range(1,ROWS+1):
            for col in range(1,COLS+1):
                x,y=pt((col,row));c.setFillColor(HexColor('#CDB98D'));c.circle(x,y,1.8,fill=1,stroke=0)
        for col in range(1,COLS+1):
            x,y=pt((col,1));c.setFont('Helvetica',6);c.setFillColor(gray);c.drawCentredString(x,y+20,str(col))
        for row in range(1,ROWS+1):
            _,y=pt((1,row));text(x0-27,y-2,str(row),7);text(x0+(COLS-1)*pitch+17,y-2,str(row),7)
        # Permanent orientation mark: physical top-left becomes top-right from solder side.
        x,y=pt((1,1));c.setFillColor(navy);c.circle(x,y,5,fill=1,stroke=0)
        if not mirror:
            xa,ya=pt((9.4,1.5));xb,yb=pt((21.6,6.35))
            c.setFillColor(HexColor('#E3EFF8'));c.setStrokeColor(HexColor('#2C6793'))
            c.roundRect(xa,yb,xb-xa,ya-yb,4,fill=1)
            text(xa+10,ya-22,'U1  ADS1115',13,navy,'Helvetica-Bold')
            text(xa+10,ya-38,'Module body / keep clear',8)
            text(xa+10,ya-52,'Socket pins along row 7',8)
            text(xa+10,ya-66,'Outline approximate; check fit',7)
        if show_wires:
            for w in wires:
                pts=[pt(xy) for xy in w['path']]
                # White underlay makes crossings distinct; crossings are never junctions.
                for width,col in [(3.8,white),(1.5,HexColor('#'+COLORS[w['net']]))]:
                    c.setStrokeColor(col);c.setLineWidth(width);path=c.beginPath();path.moveTo(*pts[0])
                    for p in pts[1:]:path.lineTo(*p)
                    c.drawPath(path)
                for x,y in (pts[0],pts[-1]):
                    c.setFillColor(HexColor('#'+COLORS[w['net']]));c.circle(x,y,2.5,stroke=0,fill=1)
        for p in parts:
            pts=[pt(xy) for xy in p['pins']]
            if not mirror:
                if p['kind']=='header':
                    xs,ys=zip(*pts);c.setFillColor(HexColor('#344A5A'));c.setStrokeColor(navy)
                    c.roundRect(min(xs)-5,min(ys)-5,max(xs)-min(xs)+10,max(ys)-min(ys)+10,2,fill=1)
                    for x,y in pts:c.setFillColor(HexColor('#E7BB58'));c.rect(x-1.5,y-1.5,3,3,fill=1,stroke=0)
                else:
                    (x1,y1),(x2,y2)=pts;dx,dy=x2-x1,y2-y1
                    angle=math.degrees(math.atan2(dy,dx));L=math.hypot(dx,dy)
                    c.saveState();c.translate((x1+x2)/2,(y1+y2)/2);c.rotate(angle)
                    c.setStrokeColor(gray);c.setLineWidth(1);c.line(-L/2,0,L/2,0)
                    c.setFillColor(HexColor('#EAD49C') if p['kind']=='resistor' else HexColor('#E1AE6A'))
                    if p['kind']=='resistor':c.roundRect(-19,-5,38,10,3,fill=1)
                    else:c.ellipse(-10,-7,10,7,fill=1)
                    c.restoreState()
                    mx,my=(x1+x2)/2,(y1+y2)/2
                    if p['ref']=='C5':text(x1-4,y1+10,'+',9,navy,'Helvetica-Bold')
                    if p['kind']=='resistor' and dx==0:
                        text(mx+9,my+3,p['ref'],8,navy,'Helvetica-Bold');text(mx+9,my-8,'10k' if p['ohms']==10000 else '1k',7)
                    elif p['kind']=='resistor':text(mx-17,my+10,p['ref']+' 1k',8,navy,'Helvetica-Bold')
                    else:text(mx+10,my+7,p['ref'],8,navy,'Helvetica-Bold')
                    if p['ref']=='R1':
                        for x,y in pts:
                            c.setFillColor(HexColor('#344A5A'));c.rect(x-4,y-4,8,8,fill=1,stroke=0)
                            c.setFillColor(HexColor('#E7BB58'));c.circle(x,y,1.4,fill=1,stroke=0)
            else:
                for x,y in pts:
                    c.setStrokeColor(navy);c.setLineWidth(.6);c.circle(x,y,3.5,stroke=1,fill=0)
        if not mirror:
            for ref,xy in [('J1',(2,1.1)),('J2',(2,11.8)),('J3',(2,18.8)),('J4',(26.9,16.9))]:
                x,y=pt(xy);text(x-3,y,ref,9,navy,'Helvetica-Bold')
            x,y=pt((5,18));text(x,y,'R3',8,HexColor('#9862B9'),'Helvetica-Bold');text(x,y-11,'EMPTY',7,HexColor('#9862B9'))
            for i,n in enumerate(parts[0]['names']):
                x,y=pt((11+i,7));c.saveState();c.translate(x,y-12);c.rotate(-55);text(0,0,n,6);c.restoreState()
        return pt
    heading(1,'Component placement - TOP side','Individual-pad perfboard only. All coordinates are (column,row), starting at the marked corner.')
    board()
    x,y=560,H-90
    for title,body in [
        ('BOARD','30 x 24 usable holes, 2.54 mm pitch. First-to-last hole span: 73.66 x 58.42 mm. Choose a board with margins beyond these holes; a typical 7 x 9 cm board may fit after checking hole count.'),
        ('SOCKET U1','10-pin female socket at (11,7) through (20,7). Module body points UP. VDD is LEFT; A3 is RIGHT. Dry-fit the actual module before soldering.'),
        ('HOST J1','Top to bottom: 3.3 V, GND, SCL, SDA, brake GPIO. This is a custom interface, NOT the Pi header pin order.'),
        ('SENSOR CONNECTORS','J2 fuel; J3 oil TEMPERATURE; J4 brake. Upper pin = signal/contact. Lower pin = ground. Use matching 2.54 mm connectors or soldered pigtails.'),
        ('REMOVABLE BIAS','R1 plugs into two single-pin machined sockets at (6,9) and (6,13), 10.16 mm apart. 1k is an INITIAL BENCH value. Leave R3A/R3B EMPTY and J3 disconnected until the oil-temperature sensor is identified.'),
    ]:
        text(x,y,title,9,navy,'Helvetica-Bold');y=para(x,y-15,body)-18
    c.showPage()
    heading(2,'Jumper wiring - SOLDER side','MIRRORED left/right. Flip the board like a book; keep the top edge at the top. Marked corner is now at upper right.')
    board(mirror=True,show_wires=True)
    x,y=560,H-90
    for title,body in [
        ('INSULATED WIRE','Use 26-28 AWG insulated hookup wire. Strip and solder ONLY the two endpoints of each W-number. Routing bends are not solder joints. Crossing lines must remain insulated.'),
        ('DO NOT BRIDGE ROWS','Every perfboard pad is separate. Colored lines are wires, not copper traces or continuous solder bridges. The table on page 3 is authoritative for endpoints.'),
        ('ORIENTATION','Column numbers run 30 to 1 in this bottom view. Coordinates retain their TOP-view names; (11,7) is the same physical hole on both pages.'),
        ('NO-CONNECT PINS','U1 ALRT=(16,7), A2=(19,7), A3=(20,7) have NO jumpers. ADDR=(15,7) connects to ground for address 0x48.'),
        ('LOW-VOLTAGE ONLY','3.3 V power and isolated sender/switch circuits only. Series resistors and capacitors provide filtering; this board is NOT 5/12 V tolerant or verified against automotive transients.'),
    ]:
        text(x,y,title,9,navy,'Helvetica-Bold');y=para(x,y-15,body)-19
    for net in ['3V3','GND','SCL','SDA','FUEL_ADC','OIL_ADC','BRAKE_GPIO']:
        c.setStrokeColor(HexColor('#'+COLORS[net]));c.setLineWidth(3);c.line(x,y,x+20,y);text(x+28,y-3,net.replace('_ADC','').replace('_GPIO',''),8);y-=15
    c.showPage()
    heading(3,'Wire-by-wire solder checklist','All coordinates use the TOP-view numbering, including when working from the bottom. Tick each link after continuity testing.')
    def coord(xy):return f'({xy[0]},{xy[1]})'
    for block,ws in enumerate([wires[:16],wires[16:]]):
        x=28+block*402;y=H-91
        text(x,y,'WIRE / NET',9,navy,'Helvetica-Bold');text(x+145,y,'FROM',9,navy,'Helvetica-Bold');text(x+225,y,'TO',9,navy,'Helvetica-Bold')
        y-=23
        for w in ws:
            c.setStrokeColor(HexColor('#C8D1D8'));c.setLineWidth(.4);c.line(x,y-9,x+378,y-9)
            c.rect(x,y-1,7,7,stroke=1,fill=0)
            text(x+14,y,w['ref']+'  '+w['net'],8,HexColor('#'+COLORS[w['net']]))
            text(x+145,y,coord(w['path'][0]),9);text(x+225,y,coord(w['path'][-1]),9)
            y-=23
    para(28,91,'Install the ground wires first (W07-W17), then 3.3 V (W01-W06), I2C (W18-W19), and sensor links. The suggested bends on page 2 can change; endpoints cannot.',780,10,14)
    para(28,56,'A visible crossing is never a junction. At a shared endpoint pad, solder the wire ends to the same pad as the component lead. Keep the insulation intact over all intervening pads.',780,9,12)
    c.showPage()
    heading(4,'Parts, limits, and first power-up','Electrically checked from the generated connectivity model. No physical board or vehicle test has been performed.')
    x,y=28,H-88
    rows=[
      ('U1','ADS1115 breakout + 1x10 female socket','(11,7) to (20,7)'),
      ('J1','1x5 host header / keyed pigtail','(3,2) to (3,6)'),
      ('J2 / J3','2-pin fuel / oil-temp connectors','(3,13)-(3,14) / (3,20)-(3,21)'),
      ('J4','2-pin brake switch connector','(28,18)-(28,19)'),
      ('R1','1k, 1%, 1/4W + two single-pin sockets','(6,9)-(6,13); removable BENCH bias'),
      ('R2 / R4','1k, 1%, 1/4W series resistors','(10,13)-(14,13) / (10,20)-(14,20)'),
      ('R3A / R3B','2 separate sockets; NO resistor fitted','(6,16) / (6,20)'),
      ('R5','10k, 1%, 1/4W brake pull-up','(24,11)-(24,15)'),
      ('R6','1k, 1%, 1/4W brake series','(24,17)-(24,21)'),
      ('C1 / C2','100nF ceramic, >=10V; 5.08mm leads','(17,13)-(17,15) / (17,20)-(17,22)'),
      ('C3 / C4','100nF ceramic, >=10V; 5.08mm leads','(24,23)-(26,23) / (7,6)-(9,6)'),
      ('C5','10uF electrolytic, >=10V; <=6mm body','PLUS (7,3); MINUS (9,3); form leads to 5.08mm'),
      ('TP1','Ground junction pad / test pin','(28,9)'),
    ]
    for ref,val,where in rows:
        text(x,y,ref,8,navy,'Helvetica-Bold');text(x+82,y,val,8);text(x+82,y-12,where,8);y-=29
    x,y=475,H-88
    checks=[
      ('1. BEFORE POWER','Dry-fit U1, sockets and C5 first; actual body clearance has not been physically tested. Leave U1 unplugged. Check the wire list, connector order and C5 polarity. Confirm no sustained 3.3 V-to-GND short (C5 can charge briefly).'),
      ('2. MEASURE SUPPLY','With sensors and host data lines disconnected, apply only regulated 3.3 V and GND. Measure U1 VDD to GND before inserting the module. Power off to insert it.'),
      ('3. FUEL BENCH CHECK','With R1=1k and a known 110-ohm resistor across J2, expect about 0.327 V at A0 for a measured 3.300 V supply. Open J2 approaches 3.3 V; short J2 approaches 0 V. These are electrical checks, not tank calibration.'),
      ('4. BRAKE CHECK','Configure the host pin as a digital INPUT. J4 open gives about 3.3 V; J4 closed gives about 0 V. Normal fluid is open; low fluid closes the switch. An unplugged switch also looks normal: no broken-wire detection.'),
      ('5. SOFTWARE / OIL','ADS1115 address 0x48; use +/-4.096 V range for 0-3.3 V inputs. Leave oil channel unused and J3 unplugged until its actual sensor type and curve are known. Do not connect the ECU oil-pressure transducer here.'),
    ]
    for title,body in checks:
        text(x,y,title,9,navy,'Helvetica-Bold');y=para(x,y-14,body,337,8.5,11)-16
    text(28,52,'References: TI ADS1115 datasheet; Mazda 1999-2001 workshop manual 04-11-8; Raspberry Pi GPIO documentation.',7)
    text(28,40,'Circuit basis: 3.3 V independent bias, isolated senders, common reference ground. No changes to ECU inputs or Pi wake circuit.',7)
    c.save()

def main():
    OUT.mkdir(parents=True,exist_ok=True);TMP.mkdir(parents=True,exist_ok=True);PDF.parent.mkdir(parents=True,exist_ok=True)
    report=validate()
    manifest={'revision':'A','date':'2026-10-30','board':{'columns':COLS,'rows':ROWS,'pitch_mm':2.54,
              'coordinates':'component-side (column,row), 1-based','type':'individual-pad perfboard'},
              'parts':parts,'wires':wires,'expected_nets':expected,'validation':report}
    (OUT/'ADS1115_sensor_board_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    build_native();make_pdf()
    report['native_roundtrip_and_endpoint_check']=True
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));print(PDF)

if __name__=='__main__':main()
