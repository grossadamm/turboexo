"""Prepare and slice the fascia on the existing P1S ASA profile, offline."""
import json
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
from scipy.spatial import cKDTree
from shapely import LineString
import trimesh

from build_trim import APPROVED, OUT, FACE_Z, LIP_BACK_Z

sys.path.append(str(OUT.parent / "extended_print_review"))
from path_audit import parse

APP = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
PRODUCT = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}"
OBJECT_PATH = "3D/Objects/object_1.model"
ET.register_namespace("", CORE[1:-1])
ET.register_namespace("p", PRODUCT[1:-1])


def prepare(path, mesh):
    with ZipFile(APPROVED / "slice_work/source.3mf") as source:
        files = {key: source.read(key) for key in source.namelist() if not key.endswith(".png")}
    model = ET.fromstring(files["3D/3dmodel.model"])
    item = model.find(f".//{CORE}item")
    center = -mesh.bounds.mean(axis=0)
    placement = np.array([128.,128.,0.])+center
    placement[2] = -mesh.bounds[0,2]
    item.set("transform", "1 0 0 0 1 0 0 0 1 "+" ".join(map(str, placement)))
    for node in model.findall(f".//{CORE}components"):
        for component in list(node):
            if component.get("objectid") != "1":
                node.remove(component)
    sub = ET.fromstring(files[OBJECT_PATH])
    resources = sub.find(CORE + "resources")
    for obj in list(resources):
        if obj.get("id") != "1":
            resources.remove(obj)
    xmlmesh = resources[0].find(CORE + "mesh")
    xmlmesh.clear()
    vertices = ET.SubElement(xmlmesh, CORE + "vertices")
    faces = ET.SubElement(xmlmesh, CORE + "triangles")
    for vertex in mesh.vertices:
        ET.SubElement(vertices, CORE + "vertex", dict(zip(("x","y","z"), map(str, vertex))))
    for face in mesh.faces:
        ET.SubElement(faces, CORE + "triangle", dict(zip(("v1","v2","v3"), map(str, face))))
    cfg = ET.fromstring(files["Metadata/model_settings.config"])
    obj = cfg.find("object")
    obj.find("metadata[@key='name']").set("value","TurboExo soft-lip fascia")
    obj.find("metadata[@face_count]").set("face_count",str(len(mesh.faces)))
    for part in list(obj.findall("part")):
        if part.get("subtype") != "normal_part":
            obj.remove(part)
            continue
        part.find("metadata[@key='name']").set("value","TurboExo soft-lip fascia")
        part.find("metadata[@key='source_file']").set("value","display_trim_face_down.stl")
        part.find("mesh_stat").set("face_count",str(len(mesh.faces)))
        for axis in "xyz":
            part.find(f"metadata[@key='source_offset_{axis}']").set("value", "0")
    plate = cfg.find("plate")
    for meta in list(plate.findall("metadata")):
        if meta.get("key").endswith("_file"):
            plate.remove(meta)
    settings = json.loads(files["Metadata/project_settings.config"])
    settings.update(enable_support="0", brim_type="outer_only", brim_width="6",
                    brim_object_gap="0", elephant_foot_compensation="0.12",
                    wall_loops="4", layer_height="0.2")
    for key, node in (("3D/3dmodel.model",model),(OBJECT_PATH,sub),
                      ("Metadata/model_settings.config",cfg)):
        files[key] = ET.tostring(node, encoding="utf-8", xml_declaration=True)
    files["Metadata/project_settings.config"] = json.dumps(settings).encode()
    with ZipFile(path, "w", ZIP_DEFLATED) as project:
        for name, data in files.items():
            project.writestr(name,data)


def audit_export(project, mesh, scratch):
    with ZipFile(project) as archive:
        root = ET.fromstring(archive.read("3D/3dmodel.model"))
        sub = ET.fromstring(archive.read(OBJECT_PATH))
        assert archive.read("Metadata/plate_1.gcode") == (scratch/"plate_1.gcode").read_bytes()
        settings = json.loads(archive.read("Metadata/project_settings.config"))
        assert settings["enable_support"] == "0" and settings["brim_type"] == "outer_only"
    vertices = np.array([[float(v.attrib[k]) for k in "xyz"]
                         for v in sub.findall(f".//{CORE}vertex")])
    faces = np.array([[int(f.attrib[k]) for k in ("v1","v2","v3")]
                      for f in sub.findall(f".//{CORE}triangle")])
    [item] = root.findall(f".//{CORE}item")
    [component] = root.findall(f".//{CORE}component")
    for node in (component,item):
        transform = np.fromstring(node.attrib["transform"],sep=" ").reshape(4,3)
        vertices = vertices @ transform[:3] + transform[3]
    placement = np.r_[[128.,128.]-mesh.bounds.mean(axis=0)[:2], -mesh.bounds[0,2]]
    deviation, ids = cKDTree(mesh.vertices + placement).query(vertices)
    assert len(ids) == len(mesh.vertices) == len(np.unique(ids)) and deviation.max() < .001
    assert {tuple(sorted(f)) for f in ids[faces]} == {tuple(sorted(f)) for f in mesh.faces}
    return dict(mesh_matches_stl=True, max_exported_vertex_delta_mm=float(deviation.max()),
                triangles=len(faces), archived_gcode_matches_cli=True)


def audit_aperture(gcode):
    roads, groups, _, _, config = parse(gcode)
    assert not any("bridge" in k.lower() or "support" in k.lower() for k in roads)
    per_layer = {}
    last_lip_layer = round(np.ceil((FACE_Z-LIP_BACK_Z)/.2)*.2, 3)
    for feature,z,xy in groups:
        if feature != "Outer wall" or z > last_lip_layer:
            continue
        width,height = np.ptp(xy,axis=0)
        if 149. < width < 157. and 92. < height < 101.:
            per_layer.setdefault(z,[]).append(xy)
    assert sorted(per_layer) == [round(k*.2,2) for k in range(1,round(last_lip_layer/.2)+1)]
    rows = []
    previous = None
    nominal_width = float(config["outer_wall_line_width"])
    for z,loops in sorted(per_layer.items()):
        # On the last layer a second exterior perimeter follows the lip root.
        aperture = min(loops, key=lambda xy:np.ptp(xy[:,0]))
        seam = float(np.linalg.norm(aperture[-1]-aperture[0]))
        assert seam < .10
        points = np.asarray(LineString(aperture).segmentize(.03).coords)
        shift = None if previous is None else float(cKDTree(previous).query(points)[0].max())
        assert shift is None or shift < nominal_width
        rows.append(dict(print_z_mm=z, perimeter_centerline_size_mm=np.ptp(aperture,axis=0).tolist(),
                         perimeter_seam_gap_mm=seam, max_shift_from_prior_mm=shift))
        previous = points
    return dict(support_features=[], bridge_features=[], nominal_wall_width_mm=nominal_width,
                lip_last_toolpath_layer_mm=last_lip_layer,
                aperture_perimeter_by_layer=rows)


def main():
    mesh = trimesh.load_mesh(OUT / "display_trim_face_down.stl")
    scratch = OUT / "slice_work"
    scratch.mkdir(exist_ok=True)
    prepare(scratch/"source.3mf",mesh)
    command = ["sandbox-exec", "-p", "(version 1) (allow default) (deny network*)",
               APP, "--datadir", str(scratch/"data"), "--debug", "3",
               "--arrange", "0", "--orient", "0", "--outputdir", str(scratch),
               "--slice", "1", "--export-3mf", "display_trim_P1S_ASA.3mf", str(scratch/"source.3mf")]
    with (scratch/"cli.log").open("w") as log:
        subprocess.run(command, cwd=scratch, stdout=log, stderr=subprocess.STDOUT, check=True)
    result = json.loads((scratch/"result.json").read_text())
    plate = result["sliced_plates"][0]
    assert result["return_code"] == 0 and len(plate["objects"]) == 1
    assert "Support" not in plate["feature_type_times"]
    bbox = plate["objects"][0]["bbox"]
    assert bbox["z"] < .01 and bbox["x"] > 6 and bbox["y"] > 6
    assert bbox["x"] + bbox["width"] + 6 < 256
    assert bbox["y"] + bbox["depth"] + 6 < 256
    # Object-space proof, independent of the slicer's reported bounding box.
    assert np.allclose([bbox["width"],bbox["depth"],bbox["height"]], mesh.extents, atol=.03)
    project = scratch/"display_trim_P1S_ASA.3mf"
    result["export_audit"] = audit_export(project, mesh, scratch)
    result["aperture_gcode_audit"] = audit_aperture(scratch/"plate_1.gcode")
    shutil.copy2(project, OUT/"display_trim_P1S_ASA.3mf")
    (OUT/"slice_validation.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__ == "__main__":
    main()
