"""True top orthographic matched views of the right wing and installed context.

Run after deliverables/sweep30_study/wing_right.stl exists. No mesh is modified.
Coordinates are millimetres; screen right is outboard, screen up is aft.
"""
from pathlib import Path
import ctypes as ct
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import skin_first_views as base
import outboard_study_views as cad

D = cad.D
OUT = D / 'sweep30_study' / 'views'
WIDTH, HEIGHT = 1100, 1100
CENTER = np.array([-100., -530., 150.])
SPAN_MM = 330.
OUT_FILE = 'compare_top_16_vs_30_detail.png'


def scene(wing):
    parts = base.common() + [base.part(D/'closed42_joint', 'chin', base.C['wing'])]
    for side in ('left', 'right'):
        parts.append(base.part(wing if side == 'right' else D/'faired42_wing', 'wing_'+side, base.C['wing']))
        for stem, paint in [('plate','plate'), ('spar_fore','fore'), ('spar_aft','aft'),
                            ('receiver_fore','receiver'), ('receiver_aft','receiver'),
                            ('mount_rail','mount_rail')]:
            parts.append(base.part(D/'skin_first_wing', stem+'_'+side, base.C[paint]))
    return cad.combine(parts)


def render(assembled):
    v, tri, normals, colors = assembled
    # Exact vertical view. x image = -car Y, y image = car X.
    axes = np.array([[0.,-1.,0.], [1.,0.,0.], [0.,0.,1.]])
    p = v @ axes.T
    mid = (CENTER @ axes.T)[:2]
    uv = (p[:,:2]-mid)*(WIDTH/SPAN_MM)+[WIDTH/2,HEIGHT/2]
    facing = normals * np.where(normals[:,2]<0,-1.,1.)[:,None]
    key=np.array([.14,-.94,.31]); key/=np.linalg.norm(key)
    camera=np.array([0.,0.,1.]); half=key+camera; half/=np.linalg.norm(half)
    paint=np.all(colors==base.C['wing'],axis=1)
    standard=np.clip(.45+.47*np.maximum(0,facing@[.94,-.22,.26])+.25*np.maximum(0,facing@[-.05,.62,.78])+.1*np.maximum(0,facing@camera),.33,1.05)
    light=standard.copy()
    light[paint]=.52+.65*np.maximum(0,facing[paint]@key)+.13*np.maximum(0,facing[paint]@camera)
    shade=colors.astype(float)*light[:,None]
    shade[paint]+=255*.21*np.maximum(0,facing[paint]@half)[:,None]**16
    canvas=np.full((HEIGHT,WIDTH,3),[37,40,44],np.uint8)
    z=np.zeros((HEIGHT,WIDTH)); ids=np.full((HEIGHT,WIDTH),-1,np.int32)
    buf=[np.ascontiguousarray(x,d) for x,d in [(uv,float),(100/(3600+p[:,2]),float),(tri,np.int32),(np.clip(shade,0,255),np.uint8)]]+[canvas,z,ids]
    ct.CDLL('/tmp/fw_scan_raster.dylib').draw(WIDTH,HEIGHT,len(tri),*[ct.c_void_p(a.ctypes.data) for a in buf])
    return Image.fromarray(canvas)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    images=[render(scene(D/'faired42_wing')),render(scene(D/'sweep30_study'))]
    canvas=Image.new('RGB',(WIDTH*2+8,HEIGHT+120),(30,33,36)); draw=ImageDraw.Draw(canvas)
    title=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',44)
    detail=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',27)
    for i,(img,label) in enumerate(zip(images,['Previous  ·  16° sweep','Study  ·  30° sweep'])):
        x=i*(WIDTH+8); canvas.paste(img,(x,120))
        draw.text((x+30,14),label,font=title,fill='white')
        draw.text((x+30,75),'TOP  •  CAR RIGHT     WHEEL ABOVE     OUTBOARD RIGHT',font=detail,fill=(190,200,207))
    canvas.save(OUT/OUT_FILE)
    print(OUT/OUT_FILE)

if __name__=='__main__': main()
