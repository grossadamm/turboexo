"""Visual continuation, grown from the original brake scoop's deck and rail in mm."""
import numpy as np,trimesh as tm,json
from scipy.interpolate import PchipInterpolator
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parent
src=(R/'scoop_smooth_deck/build.py').read_text().split('def wire(t):')[0].replace('import cadquery as cq','')
ns={'__file__':str(R/'scoop_smooth_deck/build.py')};exec(src,ns);right=ns['right'];base=ns['base'];B=ns['B']
def smooth(v):return v*v*(3-2*v)
def outy(t):
    s=np.clip((t-245)/55,0,1)
    return 535.+14.*s**3.85
def floor(t,y):
    yr=right(t)
    fraction=np.clip((y-yr)/(outy(t)-yr),0.,1.)
    return base(t,yr)+B*(y-yr)+.0049*max(t-244.,0.)**2*fraction**1.5
def surf(t0,t1,y0,y1,height,ns,nt,embed):
    verts=[];faces=[]
    for top in (True,False):
        for j in range(ns+1):
            w=j/ns
            for i in range(nt+1):
                u=i/nt;t=t0(w)*(1-u)+t1(w)*u
                y=(1-w)*y0(t)+w*y1(t)
                z=floor(t,y)+(height(t,w,u) if top else embed)
                verts.append((-t,y,z))
    n=(ns+1)*(nt+1)
    for j in range(ns):
        for i in range(nt):
            a=j*(nt+1)+i;b=a+nt+1
            faces.extend(((a,b,a+1),(b,b+1,a+1),(a+n,a+n+1,b+n),(b+n,a+n+1,b+n+1)))
    ring=list(range(nt+1))+[j*(nt+1)+nt for j in range(1,ns+1)]+[ns*(nt+1)+i for i in range(nt-1,-1,-1)]+[j*(nt+1) for j in range(ns-1,0,-1)]
    for a,b in zip(ring,ring[1:]+ring[:1]):faces.extend(((a,a+n,b+n),(a,b+n,b)))
    m=tm.Trimesh(verts,faces,process=True);m.fix_normals();assert m.is_volume
    return m
# The new deck starts farther aft at the joint so it wraps behind the green plate.
# Its aft edge is at the same X as the existing deck, including where they overlap.
def nose(w):return 225.5+1.2*(1-smooth(w))
def inside(t):
    # Give the green plate its own narrow slot, then join the scoop at the rear.
    free=right(t)-1.
    f=smooth(np.clip((t-261.)/14.,0.,1.))
    return (1-f)*464.8+f*free
def tail(w):return 300.-1.6*w**12
floorpart=surf(nose,tail,inside,outy,lambda t,w,u:2.4,48,50,.18)
pieces=[floorpart]
# Repeat the original turning-vane profile; shorten each leading tip to fit the entry.
for root,height,start,yaw in [(477,15.,254.,36.),(510,15.,254.,42.)]:
    def y(t):
        s=max(0,t-254.)
        turn0=np.tan(np.deg2rad(30))
        return root+turn0*(s*s/80. if s<=40 else s-20)+(np.tan(np.deg2rad(yaw))-turn0)*s**3/(3*46**2)
    def h(t,w,u):
        rise=min(1.,.10+(t-start)/12)
        return 2.4+height*rise-.7*abs(2*w-1)
    pieces.append(surf(lambda w:start,lambda w:300.,lambda t:y(t)-.85,lambda t:y(t)+.85,h,2,30,1.7))
# Rounded outer rail belongs to the scoop: its top rises with the deck toward the outlet.
pieces.append(surf(lambda w:226.8,lambda w:298.25,lambda t:outy(t)-2.65,lambda t:outy(t)-.35,lambda t,w,u:2.4+2.+16.*smooth(min(u*1.45,1.))+.9*np.sin(np.pi*w),8,50,1.5))
extra=tm.boolean.union(pieces,engine='manifold');assert extra.is_volume and len(extra.split())==1
extra.export(P/'added_duct_geometry_mm.stl')
scoop=tm.load_mesh(R/'scoop_green_roof/green_roof.stl')
combined=tm.boolean.union([scoop,extra],engine='manifold');assert combined.is_volume and len(combined.split())==1
combined.export(P/'TurboExo_brake_scoop_progressive_turn_mm.stl')
print('Addition bbox',extra.bounds.tolist(),'fused solid volume',combined.volume,'joined overlap',extra.volume+scoop.volume-combined.volume)
