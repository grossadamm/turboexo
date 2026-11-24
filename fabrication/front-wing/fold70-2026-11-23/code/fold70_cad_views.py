"""Render fold70 STEP and original car-frame V9 hardware in parallel projection."""
import ctypes as ct
import hashlib
import json
from pathlib import Path
import re
import zipfile
import numpy as np
from PIL import Image
import trimesh
from step_mesh import step_mesh

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'deliverables'
SRC = D / 'fold70/full_folded_chin_mm.step'
SEAL = D / 'full_folded_chin/seal_installed_mm.step'
GLASS = D / 'front_end_v9/fiberglass_v9_mm.stl'
HW = D / 'front_end_v9/front_end_v9_mm.3mf'
OUT = D / 'fold70/views'

def hardware():
    # V9 non-fiberglass meshes, including brackets, intercooler, radiator and hoses.
    with zipfile.ZipFile(HW) as z:
        xml = z.read('3D/3dmodel.model')
    result=[]
    for ident, name, data in re.findall(rb'<object id="(\d+)"[^>]* name="([^"]+)"[^>]*>(.*?)</object>', xml, re.S):
        if name == b'fiberglass':
            continue
        assert b'<item objectid="'+ident+b'"/>' in xml
        verts=np.asarray(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',data),dtype=float)
        tris=np.asarray(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',data),dtype=int)
        if len(tris):
            result.append((name.decode(),trimesh.Trimesh(verts,tris,process=False)))
    assert len(result)>=60, len(result)
    return result

def render(parts, eye, path):
    eye=np.asarray(eye,float); eye/=np.linalg.norm(eye)
    right=np.cross([0,0,1],eye); right/=np.linalg.norm(right)
    axes=np.array([right,-np.cross(eye,right),eye])
    meshes=[p[1] for p in parts]
    combined=trimesh.util.concatenate(meshes)
    colors=np.vstack([np.tile(color,(len(mesh.faces),1)) for _,mesh,color in parts])
    p=combined.vertices@axes.T
    w,h=1600,1000
    lo,hi=p.min(0),p.max(0)
    scale=min((w-108)/(hi[0]-lo[0]),(h-94)/(hi[1]-lo[1]))
    xy=(p[:,:2]-(lo+hi)[:2]*.5)*scale+[w/2,h/2]
    n=combined.face_normals
    n=n*np.where(n@eye<0,-1.,1.)[:,None]
    light=np.clip(.40+.46*np.maximum(0,n@[.56,-.35,.75])+.20*np.maximum(0,n@[.25,.91,.33])+.08*np.maximum(0,n@eye),.32,1.05)
    canvas=np.full((h,w,3),[33,36,39],np.uint8)
    buffers=[np.ascontiguousarray(x,dt) for x,dt in [(xy,float),(3000-p[:,2],float),(combined.faces,np.int32),(np.clip(colors*light[:,None],0,255),np.uint8)]]+[canvas,np.zeros((h,w),float),np.full((h,w),-1,np.int32)]
    ct.CDLL('/tmp/fw_scan_raster.dylib').draw(w,h,len(combined.faces),*[ct.c_void_p(x.ctypes.data) for x in buffers])
    Image.fromarray(canvas).save(path)

def main():
    assert SRC.is_file(), SRC
    OUT.mkdir(parents=True, exist_ok=True)
    chin=step_mesh(SRC); seal=step_mesh(SEAL)
    glass=trimesh.load_mesh(GLASS,process=False)
    hw=hardware()
    def color(name):
        if name.startswith(('outer_splitter_plates/', 'inboard_splitter_mounts/', 'supports_and_fasteners/', 'radiator_stays/')): return [118,165,71]
        if name.startswith(('charge_hoses/', 'overflow_line/')): return [54,67,78]
        return [164,171,177]
    parts=[('fiberglass',glass,[147,155,162]), *[(n,m,color(n)) for n,m in hw], ('chin',chin,[225,136,55]), ('seal',seal,[45,47,48])]
    for name,eye in [('installed_three_quarter',[1,.60,1.0]),('installed_top',[.00001,0,1]),('installed_low_front',[1,-.42,.12])]:
        render(parts,eye,OUT/(name+'.png'))
        print(name,flush=True)
    render([('chin',chin,[225,136,55])],[1,.52,1.35],OUT/'isolated_three_quarter.png')
    sources={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SRC,SEAL,GLASS,HW)}
    record={'projection':'Orthographic, common scale and original car coordinates for all components','source_sha256':sources,'hardware_component_names':[n for n,_ in hw],'chin_bounds_mm':chin.bounds.tolist(),'seal_bounds_mm':seal.bounds.tolist()}
    (OUT/'cad_render_sources.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2),flush=True)
if __name__=='__main__': main()
