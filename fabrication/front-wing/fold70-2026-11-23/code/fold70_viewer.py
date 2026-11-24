"""Self-contained CAD view sheet and draggable azimuth study."""
from pathlib import Path
from io import BytesIO
import base64,json
from PIL import Image,ImageChops
out=Path(__file__).resolve().parents[1]/'deliverables/fold70';v=out/'views'
frames=json.loads((v/'orbit/manifest.json').read_text())['frames']
def uri(b,m):return 'data:image/'+m+';base64,'+base64.b64encode(b).decode()
eyes=[Image.open(v/'orbit'/f['file']).convert('RGB') for f in frames]
boxes=[ImageChops.difference(im,Image.new('RGB',im.size,im.getpixel((0,0)))).convert('L').point(lambda n:255 if n>16 else 0).getbbox() for im in eyes]
crop=(min(b[0] for b in boxes)-15,min(b[1] for b in boxes)-12,max(b[2] for b in boxes)+15,max(b[3] for b in boxes)+12)
orbit=[]
for im in eyes:
    buf=BytesIO();im.crop(crop).save(buf,'WEBP',quality=92);orbit.append(uri(buf.getvalue(),'webp'))
panels=[('Installed ¾','installed_three_quarter.png'),('Top','installed_top.png'),('Chin alone','isolated_three_quarter.png'),('Low front','installed_low_front.png')]
buttons=''.join(f'<button aria-pressed="{str(i==0).lower()}">{label}</button>' for i,(label,_) in enumerate(panels+[('Rotate','')]))
imgs=''.join(f'<img class="shot" {"" if i==0 else "hidden"} src="{uri((v/p).read_bytes(),"png")}" alt="{label} CAD view of 70 mm folded splitter"/>' for i,(label,p) in enumerate(panels))
html='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><meta charset="utf-8"><title>70 mm folded splitter</title><style>body{font-family:var(--font-sans,system-ui);color:var(--foreground,#182126)}nav{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 8px}button{font:inherit;cursor:pointer;padding:5px 9px;color:var(--foreground,#182126);background:var(--secondary,#eee);border:1px solid var(--border,#bbb);border-radius:var(--radius,6px)}button[aria-pressed=true]{background:var(--primary,#2462aa);color:var(--primary-foreground,white)}.stage{aspect-ratio:16/10;position:relative;background:#212427;display:grid;place-items:center}.stage img{width:100%;height:100%;object-fit:contain;min-height:0}#orbit{touch-action:none;user-select:none;cursor:grab}#range{width:65%;vertical-align:middle}label{display:block;margin-top:5px;font-size:.9rem}[hidden]{display:none!important}</style></head><body><nav>'''+buttons+'''</nav><div class="stage">'''+imgs+'''<img id="orbit" hidden draggable="false" alt="Drag horizontally to rotate the installed CAD assembly"></div><label hidden>Rotate <input type="range" id="range" min="0" max="14" value="11" aria-label="Viewing angle"></label><script>const frames='''+json.dumps(orbit)+''';const img=document.getElementById('orbit'),r=document.getElementById('range'),buttons=[...document.querySelectorAll('button')],pics=[...document.querySelectorAll('.shot')];function set(v){r.value=Math.min(14,Math.max(0,Math.round(v)));img.src=frames[+r.value]}r.oninput=()=>set(r.value);buttons.forEach((b,i)=>b.onclick=()=>{buttons.forEach((c,j)=>c.setAttribute('aria-pressed',i===j));pics.forEach((p,j)=>p.hidden=i!==j);img.hidden=i!==4;r.parentElement.hidden=i!==4;if(i===4)set(r.value)});let start=0,angle=0;img.onpointerdown=e=>{img.setPointerCapture(e.pointerId);start=e.clientX;angle=+r.value};img.onpointermove=e=>{if(img.hasPointerCapture(e.pointerId))set(angle+(e.clientX-start)*18/img.clientWidth)};</script></body></html>'''
(out/'fold70_viewer.html').write_text(html)
