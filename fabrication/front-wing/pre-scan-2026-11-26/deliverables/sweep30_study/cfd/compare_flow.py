"""Run the original 3D inviscid corner screen with either installed crest geometry.
Both models include the upper blade. All common obstacle triangles and BCs match.
"""
from pathlib import Path
import argparse,gc,hashlib,json,sys
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]/'cfd_corner_study'
sys.path.insert(0,str(BASE))
import geometry
from flow import grid,solve,measure

def solid_triangles(path):
    with path.open('rb') as f:
        f.seek(80)
        count=int.from_bytes(f.read(4),'little')
        dtype=np.dtype([('normal','<f4',(3,)),('pts','<f4',(3,3)),('attr','<u2')])
        raw=np.fromfile(f,dtype=dtype,count=count)
        assert len(raw)==count and len(f.read(1))==0, path
    return raw['pts']*np.array([-1.,-1.,1.])

def run(args):
    edges=grid(args.h,1.)
    coords=[(a[1:]+a[:-1])/2 for a in edges]
    selected=geometry._packed()
    inputs={}
    if args.angle==30:
        for key,path in [('wing_control',args.control),('upper_blade',args.blade)]:
            selected[key]=solid_triangles(path)
            inputs[key]={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    mask=geometry.solid_mask(*coords,blade=True)
    u,uf,diag=solve(edges,mask)
    diag['windows']=measure(edges,u,uf)
    diag['sweep_deg']=args.angle;diag['stl_inputs']=inputs
    diag['geometry_cache_sha256']=hashlib.sha256((BASE/'geometry_meshes.npz').read_bytes()).hexdigest()
    diag['grid_mm']=[args.h*1.5,args.h,args.h]
    tag=f'{args.h:g}_1_{args.angle}'
    (HERE/f'{tag}.json').write_text(json.dumps(diag,indent=2)+'\n')
    slices=[np.flatnonzero((p>=lo)&(p<=hi)) for p,lo,hi in zip(coords,[-50,450,80],[510,720,330])]
    region=np.ix_(*slices)
    np.savez_compressed(HERE/f'{tag}.npz',s=coords[0][slices[0]],y=coords[1][slices[1]],z=coords[2][slices[2]],
                        u=u[0][region],v=u[1][region],w=u[2][region])
    print(tag,diag['windows'],flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('angle',type=int,choices=[16,30]);a.add_argument('h',type=float)
    a.add_argument('--control',type=Path);a.add_argument('--blade',type=Path)
    run(a.parse_args())
