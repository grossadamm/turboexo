"""Plot tracked 3D streamlines and matched local directions from the converged solve."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.spatial import ConvexHull
from pathlib import Path
from geometry import mesh_triangles
HERE=Path(__file__).resolve().parent
COLORS=['#29729c','#bf4a23']
LABELS=['Open channel','With upper blade']
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
def data(name):
    return json.loads((HERE/f'1_1_{name}.json').read_text())['windows']
def plot_angles():
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.7),layout='constrained')
    for ax,key,title in zip(axes,['up_deg','outward_deg'],['Side view  ·  positive is up','Top view  ·  positive is outboard']):
        for i,n in enumerate(('off','on')):
            d=data(n)
            vals=[d[w][key] for w in ('inside_slot','upstream_of_tire')]
            xx=np.arange(2)+(-.18 if i==0 else .18)
            ax.bar(xx,vals,width=.32,color=COLORS[i],label=LABELS[i])
            for x,y in zip(xx,vals):
                ax.text(x,y+(1 if y>0 else -1),f'{y:+.1f}°',ha='center',va='bottom' if y>0 else 'top',fontsize=10)
        ax.axhline(0,c='#55616a',lw=.9)
        ax.set_xticks([0,1],['In the slot¹','Ahead of the tire²'])
        ax.set_ylim((-12,45) if key=='up_deg' else (-42,16))
        ax.set_title(title,loc='left',weight='bold')
        ax.set_ylabel('Mean flow direction (degrees)')
    axes[0].legend(frameon=False,fontsize=9,loc='upper right')
    fig.suptitle('What the upper blade changed in the 3D slip-flow model',weight='bold',fontsize=14)
    fig.supxlabel('¹ Same 18 × 7 mm patch in both runs.    ² Same 85 × 90 mm patch, 23.5 mm ahead of the tire nose.',fontsize=9)
    fig.savefig(HERE/'directions.png',dpi=175,bbox_inches='tight')
def hull(ax,name,axis,color,alpha=1):
    pts=mesh_triangles(name).reshape(-1,3)[:,[0,axis]]
    outline=pts[ConvexHull(pts).vertices]
    ax.fill(outline[:,0],outline[:,1],color=color,alpha=alpha,lw=.5,zorder=0)
def trajectories():
    fig,axes=plt.subplots(2,1,figsize=(9.2,6.5),layout='constrained')
    sc=json.loads((HERE/'section'/'section_profiles.json').read_text())
    for (ax,index,title) in [(axes[0],1,'Side projection   ·   height above ground'),(axes[1],0,'Top projection   ·   distance from car centerline')]:
        if index==1:
            for n in ['base','blade']:
                p=np.array(sc[n]);ax.fill(*p.T,color='#ccd3d6',lw=0,zorder=-2)
            ax.set_ylim(105,255);ax.set_ylabel('Up (mm)')
        else:
            hull(ax,'wing_control',1,'#d5d9d9');hull(ax,'upper_blade',1,'#a6afb1')
            ax.set_ylim(470,630);ax.set_ylabel('Outboard (mm)')
        hull(ax,'tire',2 if index==1 else 1,'#555e63')
        for i,n in enumerate(('off','on')):
            d=np.load(HERE/f'trace_1_1_{n}.npz')
            paths=d['pos'][:,d['paired'],index];x=d['s']
            a=np.argmin(abs(x-395))+1
            ax.fill_between(x[:a],np.percentile(paths,10,axis=1)[:a],np.percentile(paths,90,axis=1)[:a],color=COLORS[i],alpha=.16,lw=0)
            ax.plot(x[:a],np.median(paths,axis=1)[:a],color=COLORS[i],lw=2,label=LABELS[i])
        ax.axvline(395,c='#666',ls=':',lw=1)
        ax.set_xlim(85,500);ax.set_aspect('equal',adjustable='box')
        ax.set_title(title,loc='left',fontsize=11,weight='bold')
        ax.grid(alpha=.13)
    axes[1].text(477,608,'Tire',ha='center',va='center',color='white',fontsize=9)
    axes[0].legend(frameon=False,loc='upper left')
    axes[1].set_xlabel('Rearward distance in car coordinates (mm)   →')
    fig.suptitle('Streamlines seeded inside the channel',fontsize=14,weight='bold')
    fig.supxlabel('Same 120 start points in both runs. Lines show medians and bands cover the middle 80%.\nSlip walls and a stationary tire. The model cannot form a separated tire wake.',fontsize=9)
    fig.savefig(HERE/'model_streamlines.png',dpi=175,bbox_inches='tight')
if __name__=='__main__':
    plot_angles();trajectories()
