"""Compare rays through the marked fascia-to-surround zones in four views."""
import json

import numpy as np
import vtk

import build_trim as m
from params import model_to_local
from render_trim import actor, tess


def locator(parts):
    meshes = vtk.vtkAppendPolyData()
    for shape in parts:
        poly = actor("#999999", *tess(shape)).GetMapper().GetInput()
        meshes.AddInputData(poly)
    meshes.Update()
    search = vtk.vtkStaticCellLocator()
    search.SetDataSet(meshes.GetOutput())
    search.BuildLocator()
    return search


def depth(search, eye, point):
    unit = np.array([0.,0.,-1.]) if eye is None else point-eye
    unit /= np.linalg.norm(unit)
    start = point-100.*unit if eye is None else eye
    end = point+190.*unit
    t, p, index = vtk.mutable(0.), [0.,0.,0.], vtk.mutable(0)
    if not search.IntersectWithLine(start, end, 1e-7, t, p, [0.,0.,0.], index):
        return None
    return float(m.FACE_Z-p[2])


def zones():
    """Sample the display-plane perimeter and the exposed area inside it."""
    wire = m.outline(m.FACE_Z)
    points, _ = wire.sample(2400)
    shape = np.array([v.toTuple() for v in points])
    after = np.roll(shape,-1,axis=0)
    bands = {}
    for side, name in ((-1,"left"),(1,"right")):
        rows = []
        for y in np.arange(-51.5,54.,.25):
            cross = (shape[:,1]>y)!=(after[:,1]>y)
            a,b = shape[cross],after[cross]
            x = a[:,0]+(b[:,0]-a[:,0])*(y-a[:,1])/(b[:,1]-a[:,1])
            edge = max(side*x)
            for u in np.r_[np.arange(84.5,edge-.18,.45),edge+np.array([-.15,.05,.25,.45,.65,.85])]:
                rows.append(np.array([side*u,y,m.FACE_Z]))
        bands[name] = rows
    ytop = lambda x: 55.5+2.95 + (54.1-55.5) * (x+88.2)/176.4
    bands["top"] = [np.array([x,ytop(x)+delta,m.FACE_Z])
                    for x in np.arange(-88.,88.1,.5) for delta in (-.8,-.4,0.,.25,.50,.75)]
    return bands


def main():
    approved, lcd = m.references()
    base = m.to_local(m.cq.importers.importStep(str(m.OUT/"surround.step")).val())
    old_trim = m.to_local(m.cq.importers.importStep(str(m.ORIGINAL/"display_trim.step")).val())
    trim = m.to_local(m.cq.importers.importStep(str(m.OUT/"display_trim.step")).val())
    common = list(lcd.values())
    common.extend(part for sx,sy in m.HOLES
                  for part in m.fasteners(sx*m.HOLE_X,sy*m.HOLE_Y).values())
    old = locator([approved,old_trim,*common])
    new = locator([base,trim,*common])
    viewpoints = json.loads((m.REF/"viewpoints.json").read_text())["camera_centers"]
    views = {"normal":None, **{name:model_to_local(p)[0] for name,p in viewpoints.items()}}
    report = {}
    for name, eye in views.items():
        report[name] = {}
        for band, points in zones().items():
            a = [depth(old,eye,p) for p in points]
            b = [depth(new,eye,p) for p in points]
            missing = [p.round(3).tolist() for p,d in zip(points,b) if d is None]
            report[name][band] = dict(rays=len(points), previously_open=sum(d is None for d in a),
                                      now_open=len(missing), first_open_display_points_mm=missing[:12],
                                      previously_recessed_beyond_12_mm=sum(d is None or d>12. for d in a),
                                      now_recessed_beyond_12_mm=sum(d is None or d>12. for d in b))
    (m.OUT/"sightline_check.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2),flush=True)
    assert all(band["now_open"] == 0 for view in report.values() for band in view.values())


if __name__ == "__main__":
    main()
