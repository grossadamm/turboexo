"""Package the fitted corner joint into the latest inspected front-end viewer."""
import argparse
from base64 import b64encode
from pathlib import Path
import re

import cadquery as cq
import numpy as np
import trimesh
from OCP.BRep import BRep_Tool
from OCP.BRepLib import BRepLib_ToolTriangulatedShape
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopAbs import TopAbs_REVERSED
from OCP.TopLoc import TopLoc_Location

D = Path(__file__).resolve().parents[1]/'deliverables'
ORIGINAL = D/'faired42_wing'
OUT = D/'closed42_joint'


def surface_mesh(path, color):
    shape = cq.importers.importStep(str(path)).val()
    assert shape.isValid() and shape.Solids(), path
    BRepMesh_IncrementalMesh(shape.wrapped,.03,False,.06,True).Perform()
    positions, normals, triangles = [], [], []
    offset = 0
    for face in shape.Faces():
        location = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face.wrapped, location)
        if not tri or not tri.NbTriangles():
            continue
        if tri.HasNormals():
            tri.RemoveNormals()
        BRepLib_ToolTriangulatedShape.ComputeNormals_s(face.wrapped,tri)
        indices = range(1,tri.NbNodes()+1)
        xf = location.Transformation()
        p = np.array([tri.Node(i).Transformed(xf).Coord() for i in indices])
        n = np.array([tri.Normal(i).Transformed(xf).Coord() for i in indices])
        f = np.array([tri.Triangle(i).Get() for i in range(1,tri.NbTriangles()+1)])-1
        if face.wrapped.Orientation()==TopAbs_REVERSED:
            f = f[:,[0,2,1]]
        if np.sum(np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])*n[f[:,0]])<0:
            n = -n
        positions.append(p[:,[1,2,0]]*.001)
        normals.append(n[:,[1,2,0]])
        triangles.append(f+offset)
        offset += len(p)
    mesh = trimesh.Trimesh(vertices=np.vstack(positions), faces=np.vstack(triangles),
                           vertex_normals=np.vstack(normals),process=False)
    mesh.visual.vertex_colors=color
    return mesh


def make_glb(assignments):
    scene=trimesh.load_scene(ORIGINAL/'render_front.glb',process=False)
    for key,path in assignments:
        color_source=key if key in scene.geometry else ('seal' if 'seal' in key else 'chin')
        mesh=surface_mesh(path,scene.geometry[color_source].visual.vertex_colors[0].copy())
        if key in scene.geometry:
            scene.geometry[key]=mesh
        else:
            scene.add_geometry(mesh,geom_name=key,node_name=key)
    dest=OUT/'render_front.glb'
    scene.export(dest,include_normals=True)
    assert set(trimesh.load_scene(dest,process=False).geometry)==set(scene.geometry)


def make_page(glb, fallback, output):
    page = Path(__file__).with_name('viewer_template.html').read_text()
    page = page.replace('__GLB__', b64encode(glb.read_bytes()).decode())
    page = page.replace('__FALLBACK__', b64encode(fallback.read_bytes()).decode())
    tmp=output.with_suffix('.next')
    tmp.write_text(page)
    tmp.replace(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--part',nargs=2,action='append',metavar=('NAME','STEP'))
    parser.add_argument('--output',type=Path,default=OUT/'rotate.html')
    parser.add_argument('--glb',type=Path,default=OUT/'render_front.glb')
    parser.add_argument('--fallback',type=Path,default=OUT/'views/full.png')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.part:
        make_glb([(k,Path(v)) for k,v in args.part])
    make_page(args.glb,args.fallback,args.output)
