from pathlib import Path
import struct,json,copy,re,gzip,base64,hashlib
import numpy as np,trimesh as tm
P=Path(__file__).resolve().parent;ROOT=P.parent
A=ROOT/'scoop_green_roof/on_car'
def parse(b):
 n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
orig,b0=parse((A/'TurboExo_approved_front_with_scoop.glb').read_bytes())
j=copy.deepcopy(orig);data=bytearray(b0)
ref=next(x for x in j['meshes'] if x['name']=='wing_left')
def add(label):
 m=tm.load_mesh((P if label=='progressive' else ROOT/'duct_outboard_study')/'added_duct_geometry_mm.stl')
 m.vertices=m.vertices[:,[1,2,0]]*.001
 m.visual.vertex_colors=[91,152,150,255]
 s=tm.Scene();s.add_geometry(m,geom_name=label,node_name=label)
 jj,bb=parse(s.export(file_type='glb',include_normals=True));item=jj['meshes'][0]
 def acc(k):
  a=copy.deepcopy(jj['accessors'][k]);v=copy.deepcopy(jj['bufferViews'][a['bufferView']]);o=v.get('byteOffset',0);raw=bb[o:o+v['byteLength']]
  data.extend(b'\0'*(-len(data)%4));v['byteOffset']=len(data);data.extend(raw)
  a['bufferView']=len(j['bufferViews']);j['bufferViews'].append(v);k=len(j['accessors']);j['accessors'].append(a);return k
 for q in item['primitives']:
  q['indices']=acc(q['indices']);q['attributes']={k:acc(x) for k,x in q['attributes'].items()}
 j['scenes'][0]['nodes'].append(len(j['nodes']));j['nodes'].append({'mesh':len(j['meshes']),'name':label})
 j['meshes'].append(item)
add('progressive');add('previous')
for k in ['bufferViews','accessors','meshes','nodes']:assert j[k][:len(orig[k])]==orig[k]
assert data[:len(b0)]==b0
data.extend(b'\0'*(-len(data)%4));j['buffers'][0]['byteLength']=len(data)
jb=json.dumps(j,separators=(',',':')).encode();jb+=b' '*(-len(jb)%4)
glb=struct.pack('<4sIII4s',b'glTF',2,28+len(jb)+len(data),len(jb),b'JSON')+jb+struct.pack('<I4s',len(data),b'BIN\0')+data
a=np.frombuffer(glb,'<u4');d=a.copy();d[3:]^=a[:-3];packed=d.view('u1').reshape(-1,4).T.copy().tobytes()
txt=(A/'TurboExo_front_wing_and_brake_scoop.html').read_text()
txt=re.sub("const MODEL='[^']+'","const MODEL='"+base64.b64encode(gzip.compress(packed,6)).decode()+"'",txt,count=1)
txt=txt.replace('draws.push({vao,','draws.push({name:mesh.name,vao,')

txt=txt.replace('for(const d of draws){gl.bindVertexArray(d.vao);', """for(const d of draws){if((d.name==='progressive'||d.name==='previous') && d.name!==choice)continue;gl.bindVertexArray(d.vao);""")
txt=txt.replace('let center=home,az,el,dist;',"""let choice='progressive';let center=home,az,el,dist;
for(const btn of document.querySelectorAll('[data-choice]'))btn.onclick=()=>{choice=btn.dataset.choice;for(const b of document.querySelectorAll('[data-choice]'))b.setAttribute('aria-pressed',b===btn);render()};""")
camera='center=[.468,.155,-.221];az=.045;el=.91;dist=.405;render()'
txt=txt.replace("center=[.388,.185,-.115];az=.41;el=.17;dist=.435;render();",camera+';')
txt=txt.replace('<body><main>','<body><nav><button data-choice="progressive" aria-pressed="true">Progressive turn</button><button data-choice="previous">Previous extension</button></nav><main>')
txt=txt.replace('</style>','nav{display:flex;gap:6px;margin:0 0 7px}nav button{font:inherit;border:1px solid var(--border);background:var(--secondary);color:var(--foreground);border-radius:5px;padding:5px 8px}nav button[aria-pressed=true]{background:var(--primary);color:var(--primary-foreground)}#joint,#rightJoint,#scoop,#underside,.panel{display:none}</style>')
txt=txt.replace('>Full front</button>','>Full front</button><button id="corner">Corner</button><button id="outlet">Look into outlet</button>').replace("window.addEventListener('resize',render);","document.getElementById('outlet').onclick=()=>{center=[.465,.162,-.266];az=2.89;el=.37;dist=.31;render()};document.getElementById('corner').onclick=()=>{"+camera+"};window.addEventListener('resize',render);")
if (P/'duct_preview.jpg').exists():
 txt=re.sub('src="data:image/png;base64,[^"]+"','src="data:image/jpeg;base64,'+base64.b64encode((P/'duct_preview.jpg').read_bytes()).decode()+'"',txt,count=1)
(P/'Progressive_brake_scoop.html').write_text(txt)
