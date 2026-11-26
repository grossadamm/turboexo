"""Read dimensionless solver output and compare standardized locations in both cases."""
from pathlib import Path
import json, warnings, struct, re, os
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import distance_transform_edt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

HERE=Path(__file__).resolve().parent
FLOW_DIR=Path(os.environ.get("FLOW_DIR",HERE))
profiles=json.loads((HERE/"section_profiles.json").read_text())
L=211.761
U=.065
base,blade=(np.array(profiles[key]) for key in ("base","blade"))

def ranges_at_x(outline, x):
    a,b=outline[:-1],outline[1:]
    good=((a[:,0]<=x)&(b[:,0]>x))|((b[:,0]<=x)&(a[:,0]>x))
    t=(x-a[good,0])/(b[good,0]-a[good,0])
    p=a[good,1]+t*(b[good,1]-a[good,1])
    return sorted(p)

slots = {}
for x0 in (167.,183.,199.,210.):
    lower=max(ranges_at_x(base,x0))
    upper=min(ranges_at_x(blade,x0))
    assert upper>lower
    slots[x0]=(lower,upper)

def read_grid(path):
    nx,nz,dx,xmin,zmin,nlinks=struct.unpack("<iidddi",path.read_bytes()[:36])
    return xmin+(np.arange(nx)+.5)*dx,zmin+(np.arange(nz)+.5)*dx,dx

def read_log(f):
    regex=r"step=(\d+) t\*=([0-9.]+) mean_rho=([0-9.]+) min=([0-9.]+) max=([0-9.]+) maxMach=([0-9.]+) mass_flux_imbalance_pct=(-?[0-9.]+) bad=(\d+)"
    keys=("step","tstar","mean_rho","min_rho","max_rho","max_mach","mass_flux_imbalance_pct","nonfinite")
    return [dict(zip(keys,map(float,m),strict=True)) for m in re.findall(regex,f.read_text())]

def fields(stem, grid):
    xs,zs,d=read_grid(HERE/f"{grid}.grid")
    log=read_log(HERE/f"{stem}.log")
    out=[]
    for l in log:
        f=FLOW_DIR/f"{stem}_{int(l['step']):05d}.flow"
        if f.exists() and f.stat().st_size==3*len(xs)*len(zs)*4:
            out.append((l,np.fromfile(f,dtype="<f4").reshape(3,len(zs),len(xs))))
    return xs,zs,d,out

def mean_safe(f):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore",RuntimeWarning)
        return np.nanmean(f,axis=0,dtype=float)

def measured(flow,x,z):
    u,v,r=(RegularGridInterpolator((z,x),f,bounds_error=True) for f in flow)
    def vline(x0,z0,z1,n=65):
        zz=np.linspace(z0,z1,n)
        coords=np.column_stack((zz,np.full(n,x0)))
        uu,vv=u(coords),v(coords)
        assert np.isfinite(uu).all() and np.isfinite(vv).all(), (x0,z0,z1)
        pos=np.maximum(uu,0)
        u0=float(uu.mean()); v0=float(vv.mean())
        return {"u_mean_Uinf":u0,"w_mean_Uinf":v0,"vertical_angle_deg":float(np.degrees(np.arctan2(v0,u0))),"positive_flow_weighted_vertical_angle_deg":float(np.degrees(np.arctan2(np.sum(pos*vv),np.sum(pos*uu))))}
    d={}
    for k,(lo,hi) in slots.items():
        h=hi-lo
        d[f"slot_{k:g}"]=vline(k,lo+.32*h,lo+.68*h)
    for k in (225.,245.,270.):
        d[f"exit_{k:g}"]=vline(k,180,220)
    xs=np.arange(160.,221.,.5)
    zz=np.arange(165.,216.,.5)
    pz,px=np.meshgrid(zz,xs,indexing="ij")
    zz0=np.column_stack((pz.ravel(),px.ravel()))
    uu=u(zz0)
    d["reversed_X_160_220_Z_165_215_flux_screen"]={"area_of_u_below_minus_0.05U_mm2":float(np.count_nonzero(uu<-.05)*.25)}
    return d

def draw(results, res, reynolds, phase_count):
    fig, ax=plt.subplots(2,2,figsize=(13.7,8), gridspec_kw={"width_ratios":[1.15,1]}, layout="constrained")
    for row,name in enumerate(("on","off")):
        x,z,f=results[name,res,reynolds]
        for col,limits in enumerate(((-18,315,102,245),(148,257,156,224))):
            a=ax[row,col]
            xmin,xmax,zmin,zmax=limits
            ix=(xmin-3<=x)&(x<=xmax+3)
            iz=(zmin-3<=z)&(z<=zmax+3)
            xw,zw=x[ix],z[iz]
            uw,vw=f[:2,iz,:][:,:,ix]
            speed=np.hypot(uw,vw)
            mask=~np.isfinite(speed)
            filled=speed[tuple(distance_transform_edt(mask, return_distances=False, return_indices=True))]
            hm=a.pcolormesh(xw,zw,filled,vmin=0,vmax=1.55,cmap="viridis",shading="nearest",rasterized=True)
            a.streamplot(xw,zw,uw,vw,color="#fff",density=(1.22,.73) if col==0 else (1.43,.94),linewidth=.50,arrowsize=.65,broken_streamlines=True)
            for p in (base,blade) if name=="on" else (base,):
                a.add_patch(Polygon(p,facecolor="#151b22",edgecolor="#f4f7fa",lw=.55,zorder=5))
            if col==1:
                lo,hi=slots[210.0]
                a.plot([210,210], [lo+.32*(hi-lo),lo+.68*(hi-lo)], color="#ffd79c", lw=1.9, zorder=6)
            a.set(xlim=(xmin,xmax),ylim=(zmin,zmax),aspect="equal",xlabel="Aft distance −car X (mm)" if row else None,ylabel="Height car Z (mm)" if col==0 else None)
            if row==0: a.set_title("Full section" if col==0 else "Upper passage and exit",loc="left",fontweight="semibold")
            a.text(.02,.95,"42° BLADE" if name=="on" else "BLADE REMOVED",transform=a.transAxes,va="top",color="white",fontweight="bold",fontsize=9,bbox=dict(facecolor="#151b22",edgecolor="none",pad=3))
    cb=fig.colorbar(hm,ax=ax,location="right",shrink=.7,pad=.02)
    cb.set_label("Speed / incoming speed")
    fig.suptitle(f"Viscous section screen  ·  car right, Y = −555 mm\n$Re_c$ = {reynolds:,}  |  {res:g} mm grid  |  Mean of {phase_count} snapshots, $t^*$ = 14–22  |  Isolated 2D, not road flow",x=.01,ha="left",fontweight="semibold",fontsize=16)
    suffix=f"{res:g}mm" if reynolds==650 else f"re{reynolds}_{res:g}mm"
    fig.savefig(HERE/f"section_comparison_{suffix}.png",dpi=165)
    plt.close(fig)

def main():
    results={}
    diagnostics={}
    data={}
    for (res,reynolds,marker) in ((2.,650,""),(1.25,650,"_dense"),(2.,1300,"_re1300")):
        count=0
        for name in ("on","off"):
            grid=f"{name}_{res:g}"
            stem=f"{name}{marker}_{res:g}"
            if not (HERE/f"{stem}.log").exists(): continue
            x,z,_,files=fields(stem,grid)
            if not files: continue
            selected=[(l,f) for l,f in files if 13.99<=l["tstar"]]
            if not selected: continue
            if len(selected)>1 and selected[-1][0]["tstar"]-selected[-2][0]["tstar"]<.05:
                selected.pop(-2) # a forced endpoint was written just after the regular snapshot
            count=len(selected)
            mean=mean_safe([f for l,f in selected])
            results[name,res,reynolds]=(x,z,mean)
            data[f"{stem}_x_mm"]=x
            data[f"{stem}_z_mm"]=z
            data[f"{stem}_mean_u_w_rho"]=mean.astype(np.float32)
            diagnostics[stem]={"phase_sample_times":[l["tstar"] for l,f in selected],"mean":measured(mean,x,z),"timeseries":[{"diagnostics":l,"samples":measured(f,x,z)} for l,f in files if l["tstar"]>=5.9]}
        if ("on",res,reynolds) in results and ("off",res,reynolds) in results:
            draw(results,res,reynolds,count)
    np.savez_compressed(HERE/"mean_fields.npz",**data)
    od={"profile":profiles["audit"],"slot_z_mm_geometric":slots,"probe_definition":"central 36% of local blade-on clearance, sampled at identical x and z with blade off. Exit sampled across Z=180–220 mm.", "runs":diagnostics}
    (HERE/"diagnostics.json").write_text(json.dumps(od,indent=2)+"\n")
    for k,a in diagnostics.items():
        print(k,a["phase_sample_times"])
        for x in ("slot_167","slot_183","slot_199","slot_210","exit_225","exit_245","exit_270"):
            print(x,*(f'{a["mean"][x][b]:.3f}' for b in ("u_mean_Uinf","w_mean_Uinf","vertical_angle_deg")))

if __name__=="__main__":main()
