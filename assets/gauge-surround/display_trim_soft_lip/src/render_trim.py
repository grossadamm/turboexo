"""Render the released BRep assembly and a section through the upper-right screw."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray

import build_trim as m
from build_trim import OUT, REF, HOLE_X, HOLE_Y, HOLES, cq
from params import model_to_local

BASE = "#666e7a"
TRIM = "#6abbcb"
METAL = "#c7c9c3"
GLASS = "#263246"
PIXELS = "#0b587c"
FASTENERS = ("#555966", "#929ba1", "#be9b69")


def rgb(hex_color):
    return tuple(int(hex_color[i:i+2],16)/255 for i in (1,3,5))


def assembly():
    base, lcd = m.references()
    trim = m.to_local(cq.importers.importStep(str(OUT/"display_trim.step")).val())
    parts = [(BASE,base),(METAL,lcd["frame_lugs"]),
             (GLASS,lcd["glass_1"]),(PIXELS,lcd["glass_2"]),(TRIM,trim)]
    for sx,sy in HOLES:
        parts += list(zip(FASTENERS,m.fasteners(sx*HOLE_X,sy*HOLE_Y).values()))
    return parts


def tess(shape):
    v, f = shape.tessellate(.045,.16)
    return np.asarray([p.toTuple() for p in v]), np.asarray(f, dtype=np.int64)


def actor(color, vertices, faces):
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(vertices, deep=True))
    cells = vtk.vtkCellArray()
    cells.SetData(numpy_to_vtkIdTypeArray(np.arange(0,3*len(faces)+1,3),deep=True),
                  numpy_to_vtkIdTypeArray(faces.ravel(),deep=True))
    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetPolys(cells)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    if color == GLASS:
        mapper.SetResolveCoincidentTopologyToPolygonOffset()
        mapper.SetRelativeCoincidentTopologyPolygonOffsetParameters(0.,3.)
    result = vtk.vtkActor()
    result.SetMapper(mapper)
    prop = result.GetProperty()
    prop.SetColor(*rgb(color))
    prop.SetAmbient(.32)
    prop.SetDiffuse(.68)
    prop.SetSpecular(.20)
    prop.SetSpecularPower(28.)
    return result


def image(parts, direction, target, height, stem, eye=None):
    ren = vtk.vtkRenderer()
    ren.SetBackground(.085,.102,.133)
    for color,v,f in parts:
        ren.AddActor(actor(color,v,f))
    camera = ren.GetActiveCamera()
    camera.SetFocalPoint(*target)
    camera.SetPosition(*(np.array(target)+520*np.array(direction)))
    camera.SetViewUp(0.,1.,0.)
    if eye is None:
        camera.ParallelProjectionOn()
        camera.SetParallelScale(height/2)
    else:
        camera.SetPosition(*eye)
        camera.SetViewAngle(float(np.degrees(2*np.arctan(height/2/np.linalg.norm(eye-target)))))
    ren.ResetCameraClippingRange()
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(1320,880)
    win.SetMultiSamples(8)
    win.AddRenderer(ren)
    win.Render()
    screen = vtk.vtkWindowToImageFilter()
    screen.SetInput(win)
    screen.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetInputConnection(screen.GetOutputPort())
    writer.SetFileName(str(OUT/f"{stem}.png"))
    writer.Write()
    win.Finalize()


def draw_section(ax, plane, parts):
    for color,shape in parts:
        sh = cq.Workplane(plane).newObject([shape]).section().val()
        for face in sh.Faces():
            v,f = face.tessellate(.012,.12)
            points = np.asarray([plane.toLocalCoords(p).toTuple() for p in v])
            ax.tricontourf(points[:,0],points[:,1],f, np.ones(len(points)),
                          levels=[.5,1.5],colors=[color])
            for e in face.Edges():
                pts,_ = e.sample(max(2,int(e.Length()/.12)))
                p = np.asarray([plane.toLocalCoords(x).toTuple() for x in pts])
                ax.plot(p[:,0],p[:,1],color="#101722",linewidth=.55)


def section(parts):
    origin = cq.Vector(HOLE_X,HOLE_Y,0.)
    slope = .375
    plane = cq.Plane(origin,(1,slope,0),(slope,-1,0))
    fig,ax = plt.subplots(figsize=(12,4.4), layout="constrained")
    fig.patch.set_facecolor("#171e29")
    ax.set_facecolor("#171e29")
    draw_section(ax, plane, parts)
    ax.set(xlim=(-22,13),ylim=(-13.8,9.4),aspect="equal")
    ax.set_axis_off()
    ax.set_title("Section through upper-right screw and glass",loc="left",color="white",fontsize=15,pad=14)
    labels = [
        ("1.7 mm fascia", (-7,1.35),(-16,5.3)),
        ("Relieved inner lip",(-11.2,.49),(-21,2.8)),
        ("Glass face / active area",(-19,0),(-21,-6.0)),
        ("0.60 mm metal lug",(1,-3.9),(5.1,-2.6)),
        ("M3 × 14 and 6 mm washer",(1,3.1),(3.4,7.5)),
        ("Retained M3 nut",(2.45,-8.8),(5.7,-10.1)),
        ("Approved mount",(-4,-5.8),(-16,-9.2)),
    ]
    for label,xy,txt in labels:
        ax.annotate(label,xy,txt,fontsize=10,color="#f2f6ff",va="center",
                    arrowprops=dict(arrowstyle="-",color="#b3c3d6",lw=.9))
    fig.savefig(OUT/"section_lug_and_glass.png",dpi=155,facecolor=fig.get_facecolor())
    plt.close(fig)


def lip_comparison(parts):
    original = m.to_local(cq.importers.importStep(str(m.ORIGINAL/"display_trim.step")).val())
    glass_edge = m.ACTIVE_CX + 75.76
    plane = cq.Plane((glass_edge,0,0),(1,0,0),(0,-1,0))
    fig, axes = plt.subplots(1,2,figsize=(12,5.1),sharex=True,sharey=True,layout="constrained")
    fig.patch.set_facecolor("#171e29")
    for ax, title, trim in zip(axes,["Approved fascia","Refined fascia"],[original,parts[4][1]]):
        ax.set_facecolor("#171e29")
        draw_section(ax,plane,[*parts[2:4],(TRIM,trim)])
        ax.set(xlim=(-1.2,3.65),ylim=(-1.3,3.6),aspect="equal")
        ax.set_title(title,loc="left",color="white",fontsize=16,pad=8)
        ax.set_xlabel("Distance from glass edge (mm)",color="#dce5ef")
        ax.tick_params(colors="#aebdd0")
        ax.axvline(-.4,ymax=.56,ls=":",lw=1.1,color="#a6bdcd")
        ax.axhline(0,ls=":",lw=.8,color="#a6bdcd",alpha=.7)
        ax.text(-1.1,-1.17,"Active pixels",color="#a7d9ef",fontsize=10)
        for spine in ax.spines.values():
            spine.set_color("#52657a")
    axes[0].set_ylabel("Height relative to glass face (mm)",color="#dce5ef")
    for ax,z,detail in zip(axes,[.60,.35],["0.60 mm above glass plane","0.35 mm above glass plane"]):
        ax.annotate("",(0,z),(0,0),arrowprops=dict(arrowstyle="<->",color="#efcb81",lw=1.05))
        ax.hlines(z,0,.65,colors="#efcb81",linestyles=":",linewidth=.8)
        ax.annotate(detail,(.01,z/2),(.31,-.35),color="#efcb81",fontsize=10,
                    arrowprops=dict(arrowstyle="-",color="#efcb81",lw=.8))
    axes[1].annotate("0.10 × 0.18 mm bevel",(.02,.45),(-1.08,2.90),color="white",fontsize=10,
                     arrowprops=dict(arrowstyle="-",color="#dce5ef",lw=.8))
    axes[1].annotate("1.05 mm flat land",(.59,.35),(1.25,-.90),color="white",fontsize=10,
                     arrowprops=dict(arrowstyle="-",color="#dce5ef",lw=.8))
    fig.suptitle("Right aperture edge at display mid-height",color="#dce5ef",fontsize=15)
    fig.savefig(OUT/"section_before_after.png",dpi=150,facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    parts = assembly()
    meshes = [(c,*tess(s)) for c,s in parts]
    image(meshes,(0,0,1),(0,14,0),199,"assembly_front")
    eyes = json.loads((REF/"viewpoints.json").read_text())["camera_centers"]
    eye = model_to_local(eyes["236"])[0]
    image(meshes,(0,0,1),(0,9,-15),208,"assembly_oblique",eye=eye)
    image([meshes[4]],(.30,-.4,-1),(0,0,0),140,"trim_open_back")
    section(parts)
    lip_comparison(parts)
    payload = [{"c":rgb(c),"v":v.round(4).tolist(),"f":f.tolist()} for c,v,f in meshes]
    template = (OUT/"src/viewer.html").read_text()
    for key, name in (("SECTION_PATH","section_before_after.png"),
                      ("FRONT_PATH","assembly_front.png"),("OBLIQUE_PATH","assembly_oblique.png")):
        template = template.replace(key, str(OUT/name))
    (OUT/"assembly_view.html").write_text(
        template.replace("/* ASSEMBLY_MESH */",json.dumps(payload,separators=(",",":")))
        .replace("/* DRIVER_EYES */",json.dumps({k:model_to_local(v)[0].tolist()
                                               for k,v in eyes.items()})))


if __name__ == "__main__":
    main()
