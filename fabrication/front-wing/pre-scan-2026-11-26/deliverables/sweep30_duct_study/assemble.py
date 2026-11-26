"""Append progressive scoop(s) to the existing sweep study's unchanged GLB meshes."""
import base64,copy,gzip,hashlib,json,re,struct,sys
from pathlib import Path
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent
D=HERE.parent
ORIG=D/'sweep30_study'
SOURCE=D.parent/'duct_progressive_turn/TurboExo_brake_scoop_progressive_turn_mm.stl'
sha=lambda b:hashlib.sha256(b).hexdigest()

def decode(b):
    n=struct.unpack_from('<I',b,12)[0]
    j=json.loads(b[20:20+n])
    return j,b[28+n:28+n+j['buffers'][0]['byteLength']]

def build(matrix=None):
    orig,bb=decode((ORIG/'render_front.glb').read_bytes())
    j=copy.deepcopy(orig);buf=bytearray(bb)
    for side,xf in ([('left',None),('right',matrix)] if matrix is not None else [('left',None)]):
        mesh=trimesh.load_mesh(SOURCE)
        if xf is not None:mesh.apply_transform(xf)
        assert mesh.is_volume
        mesh.vertices=mesh.vertices[:,[1,2,0]]*.001
        mesh.visual.vertex_colors=[91,152,150,255]
        name=f'progressive_scoop_{side}'
        sub=trimesh.Scene();sub.add_geometry(mesh,geom_name=name,node_name=name)
        sj,sb=decode(sub.export(file_type='glb',include_normals=True))
        sm=sj['meshes'][0]
        def add_acc(idx):
            a=sj['accessors'][idx].copy()
            v=sj['bufferViews'][a['bufferView']].copy()
            off=v.get('byteOffset',0)
            buf.extend(b'\x00'*(-len(buf)%4));v['byteOffset']=len(buf)
            buf.extend(sb[off:off+v['byteLength']])
            a['bufferView']=len(j['bufferViews']);j['bufferViews'].append(v)
            j['accessors'].append(a);return len(j['accessors'])-1
        for p in sm['primitives']:
            p['indices']=add_acc(p['indices'])
            p['attributes']={k:add_acc(i) for k,i in p['attributes'].items()}
        j['scenes'][0]['nodes'].append(len(j['nodes']))
        j['nodes'].append({'name':name,'mesh':len(j['meshes'])});j['meshes'].append(sm)
    assert buf[:len(bb)]==bb
    for k in ('bufferViews','accessors','meshes','nodes'):
        assert j[k][:len(orig[k])]==orig[k]
    buf.extend(bytes(-len(buf)%4));j['buffers'][0]['byteLength']=len(buf)
    jb=json.dumps(j,separators=(',',':')).encode();jb+=b' '*(-len(jb)%4)
    glb=struct.pack('<4sIII4s',b'glTF',2,28+len(jb)+len(buf),len(jb),b'JSON')+jb+struct.pack('<I4s',len(buf),b'BIN\0')+buf
    (HERE/'render_front.glb').write_bytes(glb)
    (HERE/'assembly.json').write_text(json.dumps({'base':str(ORIG/'render_front.glb'),'source_scoop':str(SOURCE),'source_scoop_sha256':sha(SOURCE.read_bytes()),'original_meshes_validated':len(orig['meshes']),'assembled_meshes':len(j['meshes']),'transform_car_to_gltf':'(Y,Z,X)/1000','right_fit_car_mm':None if matrix is None else matrix.tolist(),'glb_sha256':sha(glb)},indent=2))

def page(include_right, fallback):
    raw=(HERE/'render_front.glb').read_bytes()
    s=(ORIG/'rotate.html').read_text()
    a=np.frombuffer(raw,dtype='<u4');d=a.copy();d[3:]^=a[:-3]
    packed=d.view('u1').reshape(-1,4).T.copy().tobytes()
    s=re.sub("const MODEL='[^']+'","const MODEL='"+base64.b64encode(gzip.compress(packed,3)).decode()+"'",s,count=1)
    s=s.replace("try {\nconst gl","(async()=>{try {\nconst gl").replace('console.error(e)}',"canvas.style.display='none';console.error(e)}})()")
    s=s.replace('const dv=new DataView(bytes.buffer);','''const packed=new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());const plain=new Uint8Array(packed.length),N=packed.length/4;
for(let i=0;i<N;i++)for(let c=0;c<4;c++)plain[4*i+c]=packed[c*N+i];const words=new Uint32Array(plain.buffer);for(let i=3;i<N;i++)words[i]^=words[i-3];const dv=new DataView(plain.buffer);''').replace('while(off<bytes.length)','while(off<plain.length)').replace('bytes.subarray(off,off+n)','plain.subarray(off,off+n)')
    s=re.sub('src="data:image/png;base64,[^"]+"','src="data:image/png;base64,'+base64.b64encode(fallback.read_bytes()).decode()+'"',s,count=1)
    s=s.replace('30° outward-sweep study','30° sweep and progressive brake scoop').replace('>Trial corner</button>','>Passenger corner</button>').replace('>Right joint</button>','>Driver duct</button>').replace('center=[-.323,.222,-.091];az=Math.atan2(-.62,1);el=Math.atan2(.49,Math.hypot(.62,1));dist=.17','center=[.455,.17,-.227];az=.40;el=.70;dist=.48')
    s=s.replace('center=[-.530,.165,-.12]','center=[-.469,.165,-.212]')
    s=s.replace('dist=radius*2.65','dist=radius*1.98')
    if not include_right:s=s.replace('az=Math.atan2(-.62,1);el=Math.atan2(.51','az=Math.atan2(.62,1);el=Math.atan2(.51')
    s=s.replace('az=Math.atan2(-.62,1);el=Math.atan2(.51','az=Math.atan2(.62,1);el=Math.atan2(.51')
    s=s.replace('>Driver duct</button>','>Driver duct</button><button id="outlet" type="button">Duct outlet</button><button id="mirror" type="button" aria-pressed="false">Passenger mirror: off</button>')
    s=s.replace('draws.push({vao,','draws.push({name:mesh.name,vao,')
    s=s.replace('let center=home,az,el,dist;', 'let showMirror=false;let center=home,az,el,dist;')
    s=s.replace('for(const d of draws){gl.bindVertexArray', "for(const d of draws){if(d.name==='progressive_scoop_right'&&!showMirror) continue;gl.bindVertexArray")
    s=s.replace("window.addEventListener('resize',render)", """document.getElementById('outlet').onclick=()=>{center=[.465,.162,-.266];az=2.89;el=.37;dist=.40;render()};document.getElementById('mirror').onclick=e=>{showMirror=!showMirror;e.currentTarget.textContent='Passenger mirror: '+(showMirror?'on':'off');e.currentTarget.setAttribute('aria-pressed',String(showMirror));if(showMirror){document.getElementById('joint').click()}render()};window.addEventListener('resize',render)""")
    s=s.replace('Passenger side · 30° sweep · 42° upper blade','Driver-side progressive scoop · passenger-side 30° wing')
    (HERE/'rotate.html').write_text(s)
    s=re.sub('<style>.*?</style>','''<style>main{position:relative}canvas{display:block;width:100%;height:420px;touch-action:none;cursor:grab}.panel{display:none}.controls{display:flex;flex-wrap:wrap;align-items:center;gap:5px;margin-top:6px}button{font:inherit;padding:4px 8px;color:var(--foreground);background:var(--secondary);border:1px solid var(--border);border-radius:var(--radius);cursor:pointer}.controls span{font-size:12px}#fallback{display:none}#fallback img{width:100%;height:auto}#status{font-size:12px}</style>''',s,flags=re.S)
    (HERE/'inline.html').write_text(s)
if __name__=='__main__':
    xf=np.loadtxt(sys.argv[1]) if len(sys.argv)>1 else None
    build(xf)
    fallback=HERE/'views/full.png'
    page(xf is not None, fallback if fallback.exists() else ORIG/'views/installed_30_front_three_quarter.png')
