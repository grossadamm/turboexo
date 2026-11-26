"""Track corresponding steady velocity-field seeds on the rear half of the channel.
Coordinates and distances in millimetres, vectors saved as multiples of freestream.
"""
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import RegularGridInterpolator
HERE=Path(__file__).resolve().parent

def trace(path):
    q=np.load(path)
    interp=RegularGridInterpolator(tuple(q[k] for k in ('s','y','z')),np.stack([q[k] for k in ('u','v','w')],axis=-1),bounds_error=False,fill_value=np.nan)
    y,z=np.meshgrid(np.arange(552,567,.75),np.arange(186.4,187.9,.25))
    start=np.column_stack([y.ravel(),z.ravel()])
    def velocity(x,points):
        return interp(np.column_stack([np.full(len(points),x),points]))
    def deriv(x,points):
        v=velocity(x,points)
        return np.where(v[:,:1]>.12,v[:,1:]/v[:,:1],np.nan)
    coords=start.copy()
    allpos=[];allvel=[]
    dist=np.arange(200,396,.5)
    for x in dist:
        allpos.append(coords.copy());allvel.append(velocity(x,coords))
        h=.5
        k=deriv(x,coords);l=deriv(x+h/2,coords+h*k/2);m=deriv(x+h/2,coords+h*l/2);n=deriv(x+h,coords+h*m)
        coords=coords+h/6*(k+2*l+2*m+n)
    return dist,np.array(allpos),np.array(allvel)

if __name__=='__main__':
    study={}
    for h in (3,2,1.5,1):
        stem=f'{h:g}_1'
        if not (HERE/f'{stem}_on.npz').exists():continue
        runs=[trace(HERE/f'{stem}_{name}.npz') for name in ('off','on')]
        s=runs[0][0];ok=np.logical_and.reduce([np.isfinite(pos[-1,:,0]) for _,pos,_ in runs])
        report={'seed_count':int(ok.size),'paired_survivors':int(ok.sum())}
        for idx,(x,pos,v) in enumerate(runs):
            nm=('off','on')[idx];report[nm]={}
            for station in (200,215,225,260,320,395):
                j=np.argmin(abs(s-station))
                if not ok.any(): continue
                uv=v[j,ok].mean(0)
                report[nm][station]={'mean_yz_mm':pos[j,ok].mean(0).tolist(),'out_deg':float(np.degrees(np.arctan2(uv[1],uv[0]))),'up_deg':float(np.degrees(np.arctan2(uv[2],uv[0])))}
            np.savez_compressed(HERE/f'trace_{stem}_{nm}.npz',s=s,pos=pos,v=v,paired=ok)
        study[h]=report
        print(h,report['paired_survivors'],report['seed_count'],report['off'].get(395),report['on'].get(395))
    (HERE/'traces.json').write_text(json.dumps(study,indent=2))
