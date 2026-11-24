"""Fixed-fit orthographic turntable of the fold70 installed CAD assembly."""
import ctypes as ct
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh
import fold70_cad_views as v

OUT=v.OUT/'orbit'
ANGLES=np.linspace(-55,55,15)
W,H=900,600

def basis(deg):
    a=np.radians(deg)
    eye=np.array([np.cos(a),np.sin(a),.8]); eye/=np.linalg.norm(eye)
    right=np.cross([0,0,1],eye); right/=np.linalg.norm(right)
    return eye,np.array([right,-np.cross(eye,right),eye])

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    chin=v.step_mesh(v.SRC); seal=v.step_mesh(v.SEAL)
    glass=trimesh.load_mesh(v.GLASS,process=False); hw=v.hardware()
    def color(name):
        if name.startswith(('outer_splitter_plates/','inboard_splitter_mounts/','supports_and_fasteners/','radiator_stays/')): return [118,165,71]
        if name.startswith(('charge_hoses/','overflow_line/')): return [54,67,78]
        return [164,171,177]
    parts=[('fiberglass',glass,[147,155,162]),*[(n,m,color(n)) for n,m in hw],('chin',chin,[225,136,55]),('seal',seal,[45,47,48])]
    mesh=trimesh.util.concatenate([p[1] for p in parts])
    colors=np.vstack([np.tile(c,(len(m.faces),1)) for _,m,c in parts])
    # The same car-frame center and scale are used for all viewpoints.
    center=(mesh.bounds[0]+mesh.bounds[1])/2
    points=mesh.vertices-center
    extents=np.array([np.max(np.abs(points@basis(a)[1].T),axis=0) for a in ANGLES])
    scale=min((W-60)/(2*max(extents[:,0])),(H-48)/(2*max(extents[:,1])))
    images=[]
    for i,angle in enumerate(ANGLES):
        eye,axes=basis(angle); p=points@axes.T
        xy=p[:,:2]*scale+[W/2,H/2]
        n=mesh.face_normals; n=n*np.where(n@eye<0,-1.,1.)[:,None]
        light=np.clip(.40+.46*np.maximum(0,n@[.56,-.35,.75])+.20*np.maximum(0,n@[.25,.91,.33])+.08*np.maximum(0,n@eye),.32,1.05)
        canvas=np.full((H,W,3),[33,36,39],np.uint8)
        buffers=[np.ascontiguousarray(x,dt) for x,dt in [(xy,float),(3000-p[:,2],float),(mesh.faces,np.int32),(np.clip(colors*light[:,None],0,255),np.uint8)]]+[canvas,np.zeros((H,W),float),np.full((H,W),-1,np.int32)]
        ct.CDLL('/tmp/fw_scan_raster.dylib').draw(W,H,len(mesh.faces),*[ct.c_void_p(x.ctypes.data) for x in buffers])
        filename=f'frame_{i:02}.webp'
        Image.fromarray(canvas).save(OUT/filename,format='WEBP',quality=82,method=5)
        images.append({'file':filename,'yaw_degrees':round(float(angle),6)})
        print(filename,flush=True)
    info={'projection':'orthographic','fixed_center_car_mm':center.tolist(),'pixels_per_mm':scale,'elevation_ratio':.8,'width':W,'height':H,'source_step_sha256':hashlib.sha256(v.SRC.read_bytes()).hexdigest(),'frames':images}
    (OUT/'manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    print('bytes',sum((OUT/f['file']).stat().st_size for f in images),flush=True)
if __name__=='__main__':main()
