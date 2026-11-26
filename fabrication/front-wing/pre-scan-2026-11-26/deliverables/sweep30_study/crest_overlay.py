"""Overlay CAD crest curves in the pixel frame of sweep30_top_comparison.py."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import math
from build_sweep30 import crest_outboard
root=Path(__file__).resolve().parent/'views'
im=Image.open(root/'compare_top_16_vs_30_detail.png').convert('RGB')
assert im.size==(2208,1220)
draw=ImageDraw.Draw(im)
c=(145,228,242)
for i,deg in enumerate((16,30)):
    def pos(x,out):
        return (i*1108+550+(out-530)*1100/330,120+550+(x+100)*1100/330)
    pts=[pos(x,crest_outboard(x,variant=bool(i))) for x in np.linspace(-36,-220,250)]
    draw.line(pts,fill=c,width=4)
    end=crest_outboard(-220,variant=bool(i))
    slope=math.tan(math.radians(deg))
    for a in range(0,34,6):
        draw.line([pos(-220-a,end+a*slope),pos(-220-a-3,end+(a+3)*slope)],fill=c,width=4)
im.save(root/'top_crest_traces.png')
