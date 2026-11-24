"""Render the released BRep assembly and a section through the upper-right screw."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
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


def assembly(prior=False):
    base, lcd = m.references()
    if not prior:
        base = m.to_local(cq.importers.importStep(str(OUT/"surround.step")).val())
    folder = m.ORIGINAL if prior else OUT
    trim = m.to_local(cq.importers.importStep(str(folder/"display_trim.step")).val())
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


def image(parts, direction, target, height, stem=None, eye=None, size=(1320,880)):
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
    win.SetSize(*size)
    win.SetMultiSamples(8)
    win.AddRenderer(ren)
    win.Render()
    screen = vtk.vtkWindowToImageFilter()
    screen.SetInput(win)
    screen.Update()
    frame = screen.GetOutput()
    from vtk.util.numpy_support import vtk_to_numpy
    pixels = vtk_to_numpy(frame.GetPointData().GetScalars()).reshape(size[1],size[0],3)
    rendered = Image.fromarray(pixels[::-1].copy())
    if stem:
        rendered.save(OUT/f"{stem}.png")
    win.Finalize()
    return rendered


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


def pair(before, after, filename):
    width, height = before.size
    output = Image.new("RGB", (2*width+16,height+38), "#171e29")
    for x, title, panel in ((0,"Soft-lip fascia",before),(width+16,"Flush perimeter",after)):
        output.paste(panel,(x,38))
        ImageDraw.Draw(output).text((x+10,12),title,fill="#eaf0f6",font_size=17)
    output.save(OUT/filename)


def main():
    parts = assembly()
    meshes = [(c,*tess(s)) for c,s in parts]
    image(meshes,(0,0,1),(0,14,0),199,"assembly_front")
    eyes = json.loads((REF/"viewpoints.json").read_text())["camera_centers"]
    eye = model_to_local(eyes["236"])[0]
    image(meshes,(0,0,1),(0,9,-15),208,"assembly_oblique",eye=eye)
    image([meshes[4]],(.30,-.4,-1),(0,0,0),140,"trim_open_back")
    section([(c,s.Solids()[0]) for c,s in parts if len(s.Solids())==1])
    prior = [(c,*tess(s)) for c,s in assembly(prior=True)]
    # Register the annotation crop to the two driver-left screw centers.
    # Their 98.4 mm pitch spans about 557 px in the supplied crop.
    crop_view = dict(direction=(0,0,1), target=(-82.22,4.23,0),
                     height=112.18, size=(204,635))
    pair(image(prior,**crop_view),image(meshes,**crop_view),"before_after_annotated_front.png")
    # Enlarge the marked lower side rail at the same orthographic heading.
    rail_view = dict(direction=(0,0,1),target=(-80.25,-26.96,0),
                     height=37.81,size=(270,214))
    pair(image(prior,**rail_view),image(meshes,**rail_view),"before_after_diagonal_rail.png")
    view = dict(direction=(0,0,1),target=(0,9,-15),height=208,eye=eye,size=(960,640))
    pair(image(prior,**view),image(meshes,**view),"before_after_driver.png")
    black = [("#292d32" if c==TRIM else "#30343a" if c==BASE else c,v,f) for c,v,f in meshes]
    image(black,(0,0,1),(0,9,-15),208,"assembly_black_ASA",eye=eye)

    payload = [{"c":rgb(c),"v":v.round(4).tolist(),"f":f.tolist()} for c,v,f in meshes]
    template = (OUT/"src/viewer.html").read_text()
    for key, name in (("SECTION_PATH","before_after_annotated_front.png"),
                      ("FRONT_PATH","assembly_front.png"),("OBLIQUE_PATH","assembly_oblique.png")):
        template = template.replace(key, str(OUT/name))
    (OUT/"assembly_view.html").write_text(
        template.replace("/* ASSEMBLY_MESH */",json.dumps(payload,separators=(",",":")))
        .replace("/* DRIVER_EYES */",json.dumps({k:model_to_local(v)[0].tolist()
                                               for k,v in eyes.items()})))


if __name__ == "__main__":
    main()
