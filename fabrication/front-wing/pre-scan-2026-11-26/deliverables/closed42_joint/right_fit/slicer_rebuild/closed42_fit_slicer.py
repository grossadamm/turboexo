#!/usr/bin/env python3
"""Wrap two unchanged, already bed-oriented fit-check STLs in a Bambu project."""
import argparse
import copy
import json
import struct
import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
BAMBU = "http://schemas.bambulab.com/package/2021"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
MODEL_REL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
IDENTITY = "1 0 0 0 1 0 0 0 1"
TITLE = "Closed42 car-right fit check - draft PLA"
PLATES = [
    ("Inner chin + inboard rail", "inner_bed.stl"),
    ("Complete outer wing", "outer_bed.stl"),
]
ET.register_namespace("", CORE)
ET.register_namespace("p", PROD)
ET.register_namespace("BambuStudio", BAMBU)


def tag(ns, name):
    return f"{{{ns}}}{name}"


def metadata(elem, **keys):
    for key, value in keys.items():
        ET.SubElement(elem, "metadata", key=key, value=str(value))


def encode_xml(elem):
    return ET.tostring(elem, encoding="utf-8", xml_declaration=True)


def fresh_uuid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"TurboExo/closed42-right-fit/{key}"))


def read_binary_stl(path):
    raw = path.read_bytes()
    count = struct.unpack_from("<I", raw, offset=80)[0]
    if len(raw) != 84 + count * 50 or not count:
        raise ValueError(f"Not a complete binary STL: {path}")
    vertices = {}
    faces = []
    for _, _, _, *a in struct.iter_unpack("<12fH", memoryview(raw)[84:]):
        f = [vertices.setdefault(tuple(a[i:i + 3]), len(vertices)) for i in (0, 3, 6)]
        if len(set(f)) != 3:
            raise ValueError(f"Degenerate STL triangle: {path}, index {len(faces)}")
        faces.append(f)
    return list(vertices), faces


def model_document(outer, mesh_id, vs, fs):
    head = ET.Element(outer.tag, outer.attrib)
    ET.SubElement(head, tag(CORE, "metadata"), name="BambuStudio:3mfVersion").text = "1"
    res = ET.SubElement(head, tag(CORE, "resources"))
    obj = ET.SubElement(res, tag(CORE, "object"), {"id": str(mesh_id), "type": "model", tag(PROD, "UUID"): fresh_uuid(f"mesh/{mesh_id}")})
    mesh = ET.SubElement(obj, tag(CORE, "mesh"))
    vts = ET.SubElement(mesh, tag(CORE, "vertices"))
    for x, y, z in vs:
        ET.SubElement(vts, tag(CORE, "vertex"), x=format(x, ".9g"), y=format(y, ".9g"), z=format(z, ".9g"))
    trs = ET.SubElement(mesh, tag(CORE, "triangles"))
    for a, b, c in fs:
        ET.SubElement(trs, tag(CORE, "triangle"), v1=str(a), v2=str(b), v3=str(c))
    return encode_xml(head)


def relationships(targets):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<Relationships xmlns="{REL}">'
            + ''.join(f'<Relationship Target="/{t}" Id="rel-{i}" Type="{MODEL_REL}"/>' for i, t in enumerate(targets, 1))
            + '</Relationships>').encode()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("template", type=Path, help="Prior fold70 Bambu Studio P1S Generic PLA 3MF")
    ap.add_argument("parts", type=Path, help="Directory with inner_bed.stl and outer_bed.stl")
    ap.add_argument("output", type=Path, help="Input 3MF to slice with Bambu Studio CLI")
    ap.add_argument("--inner-center", nargs=2, type=float, default=(128, 132.4), metavar=("X", "Y"))
    ap.add_argument("--outer-center", nargs=2, type=float, default=(128, 128), metavar=("X", "Y"))
    ap.add_argument("--override-settings", type=Path)
    ap.add_argument("--outer-settings", type=Path, help="Object-level Bambu process overrides for the outer wing")
    args = ap.parse_args()
    with zipfile.ZipFile(args.template) as src:
        settings = json.loads(src.read("Metadata/project_settings.config"))
        outer = ET.fromstring(src.read("3D/3dmodel.model"))
        refconfig = ET.fromstring(src.read("Metadata/model_settings.config"))
        types = src.read("[Content_Types].xml")
    assert settings["printer_settings_id"] == "Bambu Lab P1S 0.4 nozzle"
    assert settings["filament_settings_id"] == ["Generic PLA"]
    assert settings["printable_area"] == ["0x0", "256x0", "256x256", "0x256"]
    if args.override_settings:
        settings.update(json.loads(args.override_settings.read_text()))
    settings["print_settings_id"] = "Closed42 RIGHT fit - DRAFT 0.28mm 2 walls 3%"
    for key in list(outer):
        if key.tag != tag(CORE, "metadata") or key.get("name", "").startswith("Thumbnail_"):
            outer.remove(key)
        elif key.get("name") == "Title":
            key.text = TITLE
    res = ET.SubElement(outer, tag(CORE, "resources"))
    build = ET.SubElement(outer, tag(CORE, "build"), {tag(PROD, "UUID"): fresh_uuid("build")})
    config = ET.Element("config")
    objects = []
    plates = []
    summary = []
    for i, ((name, filename), (x, y)) in enumerate(zip(PLATES, [args.inner_center, args.outer_center]), 1):
        vs, fs = read_binary_stl(args.parts / filename)
        mins, maxs = [tuple(map(fn, zip(*vs))) for fn in (min, max)]
        if any(abs((lo + hi) / 2) >= 0.001 for lo, hi in zip(mins[:2], maxs[:2])) or abs(mins[2]) >= 0.001:
            raise ValueError(f"STL is not XY centered with bottom Z=0: {filename}, {mins}, {maxs}")
        mesh_id, obj_id = (i * 2 - 1), (i * 2)
        path = f"3D/Objects/object_{i}.model"
        objects.append((path, model_document(outer, mesh_id, vs, fs)))
        obj = ET.SubElement(res, tag(CORE, "object"), {"id": str(obj_id), "type": "model", tag(PROD, "UUID"): fresh_uuid(f"assembly/{i}")})
        comps = ET.SubElement(obj, tag(CORE, "components"))
        ET.SubElement(comps, tag(CORE, "component"), {tag(PROD, "path"): f"/{path}", "objectid": str(mesh_id), tag(PROD, "UUID"): fresh_uuid(f"comp/{i}"), "transform": f"{IDENTITY} 0 0 0"})
        # Consecutive Bambu P1S virtual plate origins are 1.2 × 256 mm apart.
        virtual_x = x + (i - 1) * 307.2
        ET.SubElement(build, tag(CORE, "item"), {"objectid": str(obj_id), tag(PROD, "UUID"): fresh_uuid(f"build/{i}"), "transform": f"{IDENTITY} {virtual_x:.6f} {y:.6f} 0", "printable": "1"})
        objcfg = copy.deepcopy(refconfig.find("object"))
        objcfg.set("id", str(obj_id))
        objcfg.find("metadata[@key='name']").set("value", name)
        objcfg.find("metadata[@face_count]").set("face_count", str(len(fs)))
        part = objcfg.find("part")
        part.set("id", str(mesh_id))
        part.set("uuid", fresh_uuid(f"part/{i}"))
        part.find("metadata[@key='name']").set("value", name)
        part.find("metadata[@key='source_file']").set("value", filename)
        part.find("mesh_stat").set("face_count", str(len(fs)))
        if i == 2 and args.outer_settings:
            for k, v in json.loads(args.outer_settings.read_text()).items():
                e = ET.Element("metadata", key=k, value=v)
                objcfg.insert(list(objcfg).index(part), e)
        config.append(objcfg)
        plate = ET.Element("plate")
        metadata(plate, plater_id=i, plater_name=name, locked="false", filament_map_mode="Auto For Flush", filament_maps="1", filament_volume_maps="0")
        model_instance = ET.SubElement(plate, "model_instance")
        metadata(model_instance, object_id=obj_id, instance_id=0, identify_id=i)
        plates.append(plate)
        summary.append({"plate": i, "file": filename, "name": name, "faces": len(fs), "vertices": len(vs), "stl_bounds_mm": [mins, maxs], "plate_translation_mm": [x, y, 0]})
    config.extend(plates)
    ET.SubElement(config, "assemble")
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as out:
        out.writestr("[Content_Types].xml", types)
        out.writestr("3D/3dmodel.model", encode_xml(outer))
        out.writestr("3D/_rels/3dmodel.model.rels", relationships([p for p, _ in objects]))
        out.writestr("_rels/.rels", relationships(["3D/3dmodel.model"]))
        out.writestr("Metadata/model_settings.config", encode_xml(config))
        out.writestr("Metadata/project_settings.config", json.dumps(settings, indent=2))
        for p, data in objects:
            out.writestr(p, data)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
