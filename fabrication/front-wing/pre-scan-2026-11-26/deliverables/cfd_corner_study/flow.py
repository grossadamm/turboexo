"""Cell-centered conservative Cartesian potential-flow screen, millimetres.
Axes point rearward, car-right outward and up. Velocities normalized to U_infinity.
Solid faces carry zero flux; open far boundaries have zero potential perturbation;
ground and vehicle center plane are symmetry/slip boundaries.
"""
import argparse,json,time,gc
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import cg
from scipy.ndimage import label
import pyamg

OUT=Path(__file__).resolve().parent

def axis(lo,hi,a,b,step,cap):
    n=int(np.ceil((b-a)/step))
    main=np.linspace(a,b,n+1)
    def tail(start,end,sign):
        if start==end: return []
        p=start;h=step;pts=[]
        while sign*(end-p)>1.6*min(cap,h*1.17):
            h=min(cap,h*1.17);p+=sign*h;pts.append(p)
        return pts+[end]
    return np.array(tail(a,lo,-1)[::-1]+list(main)+tail(b,hi,1))

def grid(h,wide):
    return [axis(-1500*wide,2250*wide,110,250,h*1.5,55),
            axis(0,2200*wide,500,600,h,50),
            axis(0,2000*wide,135,220,h,45)]

def solve(edges, solid):
    x,y,z=[(a[1:]+a[:-1])/2 for a in edges]
    sizes=[np.diff(a) for a in edges]
    dims=solid.shape
    labels,_=label(~solid)
    fluid=labels==labels[0,0,-1]
    assert fluid[0,0,-1] and not solid[0,0,-1]
    ids=np.full(dims,-1,np.int32);ids[fluid]=np.arange(np.count_nonzero(fluid),dtype=np.int32)
    n=int(fluid.sum())
    diag=np.zeros(n);rhs=np.zeros(n)
    us=[];vs=[];ws=[]
    fluxes=[]
    def slab(a,i):
        return tuple(i if k==a else slice(None) for k in range(3))
    for a in range(3):
        i,j=slab(a,slice(None,-1)),slab(a,slice(1,None))
        f1,f2=ids[i],ids[j];ok=(f1>=0)&(f2>=0)
        area=np.ones((1,1,1))
        for b in range(3):
            if b!=a:
                sh=[1]*3;sh[b]=-1;area=area*sizes[b].reshape(sh)
        sh=[1]*3;sh[a]=-1
        ww=np.broadcast_to(area/np.diff([x,y,z][a]).reshape(sh),ok.shape)[ok]
        u=f1[ok];v=f2[ok];diag[u]+=ww;diag[v]+=ww
        if a==0:
            ar=np.broadcast_to(area,ok.shape)[ok]
            rhs[u]+=ar;rhs[v]-=ar
        us.append(u);vs.append(v);ws.append(-ww)
        for end in (0,-1):
            if a in (1,2) and end==0:continue
            face=ids[slab(a,end)];okface=face>=0
            ar=np.broadcast_to(area,dims)[slab(a,end)][okface]
            diag[face[okface]]+=ar/(sizes[a][end]*.5)
            if a==0:rhs[face[okface]]+=ar*(-1 if end==0 else 1)
    ii=np.concatenate(us);jj=np.concatenate(vs);ww=np.concatenate(ws)
    A=sp.coo_matrix((np.r_[diag,ww,ww],(np.r_[np.arange(n,dtype=np.int32),ii,jj],
                    np.r_[np.arange(n,dtype=np.int32),jj,ii])),shape=(n,n)).tocsr()
    del us,vs,ws,ii,jj,ww; gc.collect()
    t=time.time();ml=pyamg.ruge_stuben_solver(A,max_coarse=50)
    it=[]
    p,info=cg(A,rhs,M=ml.aspreconditioner(),rtol=1.e-8,maxiter=220,callback=lambda _:it.append(1))
    residual=np.linalg.norm(A@p-rhs)/max(1,np.linalg.norm(rhs))
    print('cells',n,'cg',info,len(it),'rel residual',residual,'seconds',time.time()-t,flush=True)
    if info or residual>1.1e-8: raise RuntimeError('linear convergence failed')
    phi=np.full(dims,np.nan);phi[fluid]=p
    ucell=[];bflux=[];xface=None
    for a in range(3):
        face_dims=list(dims);face_dims[a]+=1;vel=np.zeros(face_dims)
        interior=slab(a,slice(1,-1));i,j=slab(a,slice(None,-1)),slab(a,slice(1,None))
        sh=[1]*3;sh[a]=-1
        vi=(phi[j]-phi[i])/np.diff([x,y,z][a]).reshape(sh)+(a==0)
        vel[interior]=np.nan_to_num(vi)
        area=np.ones((1,1,1))
        for b in range(3):
            if b!=a:
                sh=[1]*3;sh[b]=-1;area=area*sizes[b].reshape(sh)
        for end,sgn in [(0,-1),(-1,1)]:
            sf=slab(a,end)
            if a==0 or end==-1:
                vel[sf]=np.nan_to_num(-sgn*phi[sf]/(.5*sizes[a][end])+(a==0))
            bflux.append(float(sgn*np.sum(vel[sf]*np.broadcast_to(area,dims)[sf])))
        if a==0:xface=vel
        vc=.5*(vel[i]+vel[j]);vc[~fluid]=np.nan;ucell.append(vc.astype('f4'))
    diag={'active_cells':n,'solver_iterations':len(it),'relative_linear_residual':float(residual),
          'net_exterior_flux_over_inlet':abs(sum(bflux))/abs(bflux[0]),'boundary_flux_mm2_U':bflux}
    return ucell,xface,diag

def overlap(edges,lo,hi): return np.maximum(0.,np.minimum(edges[1:],hi)-np.maximum(edges[:-1],lo))
def measure(edges,ucell,uf):
    # Interpolate plane x within staggered face velocities; area-weighted
    # lateral and vertical velocities averaged using positive rearward mass flux.
    e,y,z=edges
    xc=(e[1:]+e[:-1])*.5
    def at(arr,coord,q):
        i=np.searchsorted(coord,q)-1;f=(q-coord[i])/(coord[i+1]-coord[i])
        return arr[i]*(1-f)+arr[i+1]*f
    ans={}
    for name,q,ya,yb,za,zb in [
            ('inside_slot',205.,550.,568.,187.5,194.5),
            ('exit_patch',228.,547.,576.,197.,220.),
            ('upstream_of_tire',395.,550.,635.,175.,265.)]:
        u=at(uf,e,q);v=at(ucell[1],xc,q);w=at(ucell[2],xc,q)
        area=overlap(y,ya,yb)[:,None]*overlap(z,za,zb)[None,:]
        ok=(area>0)&np.isfinite(u+v+w);A=area[ok];ux=u[ok];vy=v[ok];wz=w[ok]
        weights=A*np.maximum(0,ux);Q=sum(A*ux)
        if weights.sum()==0: continue
        mean=np.array([np.average(a,weights=weights) for a in (ux,vy,wz)])
        ans[name]=dict(station_mm=q,outward_mm=[ya,yb],height_mm=[za,zb],area_mm2=float(A.sum()),
            signed_flux_mm2_U=float(Q),forward_flux_mm2_U=float(weights.sum()),velocity_over_U=mean.tolist(),
            up_deg=float(np.degrees(np.arctan2(mean[2],mean[0]))),
            outward_deg=float(np.degrees(np.arctan2(mean[1],mean[0]))))
    return ans

def run(h,wide):
    from geometry import build_masks
    edges=grid(h,wide);coords=[(a[1:]+a[:-1])/2 for a in edges]
    print('grid',list(map(len,coords)),flush=True)
    off,on=build_masks(*coords)
    assert np.all(~off|on) and np.any(on!=off)
    for name,solid in [('off',off),('on',on)]:
        u,uf,diag=solve(edges,solid)
        diag['windows']=measure(edges,u,uf)
        diag['blade_only_cells']=int((off!=on).sum());diag['local_spacing_mm']=[h*1.5,h,h];diag['domain_multiplier']=wide
        tag=f'{h:g}_{wide:g}_{name}'
        (OUT/f'{tag}.json').write_text(json.dumps(diag,indent=2)+'\n')
        if wide==1:
            s,y,z=coords
            slices=[np.where((s>=-50)&(s<=510))[0],np.where((y>=450)&(y<=720))[0],np.where((z>=80)&(z<=330))[0]]
            region=np.ix_(*slices)
            np.savez_compressed(OUT/f'{tag}.npz',s=s[slices[0]],y=y[slices[1]],z=z[slices[2]],u=u[0][region],v=u[1][region],w=u[2][region])
        print(name,[(k,round(v['up_deg'],2),round(v['outward_deg'],2),v['area_mm2']) for k,v in diag['windows'].items()],flush=True)
        del u,uf;gc.collect()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--spacing',type=float,default=2);p.add_argument('--wide',type=float,default=1)
    a=p.parse_args();run(a.spacing,a.wide)
