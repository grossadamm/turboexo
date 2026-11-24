"""Export and re-open the complete modeled front-end layout in car-frame millimetres."""

import json
import re
import xml.etree.ElementTree as ET
import zipfile
from hashlib import sha256
from pathlib import Path
from xml.sax.saxutils import quoteattr

import cadquery as cq
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "deliverables/front_end_v4"
SPEC = {
    "fiberglass": "deliverables/body/fiberglass_with_hanger_reliefs_v4_mm.step",
    "outer_splitter_plates": "deliverables/bracket/outer_plates_v2_car_frame.step",
    "inboard_splitter_mounts": "deliverables/bracket/inboard_mounts_v4_mm.step",
    "supports_and_fasteners": "deliverables/body/cooler_supports_v4_mm.step",
    "intercooler": "deliverables/body/intercooler_with_tubes_v4_mm.step",
    "fin_face": "deliverables/body/intercooler_fins_v4_mm.step",
    "radiator_stays": "deliverables/body/radiator_stays_v4_mm.step",
    "overflow_line": "deliverables/body/radiator_overflow_v4_mm.step",
    "charge_hoses": "grid/intercooler_hoses_v4_mm.step",
    "rear_radiator": "deliverables/body/radiator_v4_mm.step",
    "rear_fin_field": "deliverables/body/radiator_fin_bays_v4_mm.step",
}
PALETTE = {
    "rear_fin_field": (0.48, 0.50, 0.51),
    "fin_face": (0.37, 0.39, 0.40),
    "radiator_stays": (0.24, 0.26, 0.24),
    "overflow_line": (0.83, 0.42, 0.12),
    "fiberglass": (0.46, 0.38, 0.33),
    "outer_splitter_plates": (0.37, 0.63, 0.17),
    "inboard_splitter_mounts": (0.37, 0.63, 0.17),
    "supports_and_fasteners": (0.38, 0.6, 0.2),
    "intercooler": (0.71, 0.72, 0.74),
    "charge_hoses": (0.13, 0.14, 0.15),
    "rear_radiator": (0.37, 0.38, 0.39),
}


def make():
    root = cq.Assembly(name="Front_end_V4_mm")
    for name, src in SPEC.items():
        if name == "fiberglass":
            s = cq.importers.importStep(str(ROOT / src)).val()
            root.add(s, name=name, color=cq.Color(*PALETTE[name]))
        else:
            group = cq.Assembly.load(str(ROOT / src))
            root.add(group, name=name, color=cq.Color(*PALETTE[name]))
    return root


def leaves(assembly):
    return [(s.moved(loc), n.split("/", 1)[1], c) for s, n, loc, c in assembly]


def signature(s):
    b = s.BoundingBox()
    return np.array(
        [
            b.xmin,
            b.ymin,
            b.zmin,
            b.xmax,
            b.ymax,
            b.zmax,
            s.Area(),
            sum(x.Volume() for x in s.Solids()),
        ]
    )


def mesh_for(s, group):
    vertices, tris = s.tessellate(0.035, 0.075)
    verts = np.array([p.toTuple() for p in vertices])
    faces = np.asarray(tris)
    for precision in (8, 7, 6, 5):
        m = trimesh.Trimesh(verts.copy(), faces.copy(), process=False)
        m.merge_vertices(digits_vertex=precision)
        repeated = np.any(np.diff(np.sort(m.faces, axis=1), axis=1) == 0, axis=1)
        if np.any(repeated):
            m.update_faces(~repeated)
        m.remove_unreferenced_vertices()
        if group == "fiberglass" or (m.is_watertight and m.is_winding_consistent):
            break
    if group == "intercooler" and len(m.faces) > 50000 and m.area_faces.min() < 1e-9:
        # The trimmed neck seam can create many submicron slivers. Reduce
        # only that tessellation with topology-preserving quadric collapse.
        import pymeshlab

        ms = pymeshlab.MeshSet()
        ms.add_mesh(pymeshlab.Mesh(m.vertices, m.faces))
        ms.meshing_decimation_quadric_edge_collapse(
            targetfacenum=14000,
            preservetopology=True,
            preserveboundary=True,
            preservenormal=True,
            optimalplacement=False,
        )
        q = ms.current_mesh()
        reduced = trimesh.Trimesh(q.vertex_matrix(), q.face_matrix(), process=False)
        assert (
            reduced.euler_number == m.euler_number
            and abs(reduced.volume / m.volume - 1) < 0.0001
        )
        rng = np.random.default_rng(4404)
        for source, target in [(m, reduced), (reduced, m)]:
            pts, _ = trimesh.sample.sample_surface(source, 2000, seed=rng)
            errors = np.concatenate(
                [
                    trimesh.proximity.closest_point(target, b)[1]
                    for b in np.array_split(pts, 20)
                ]
            )
            assert np.quantile(errors, 0.99) < 0.10 and errors.max() < 0.50, (
                errors.max()
            )
        m = reduced
    return m


def write_meshes(parts, report):
    path = DEST / ".front_end_v4_staging.3mf"
    ns = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    obj = DEST / ".front_end_v4_staging.obj"
    with (
        zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=4) as z,
        obj.open("w") as o,
    ):
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>',
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        )
        o.write("# Millimetres. X forward; Y car-left; Z up. Keep the origin.\n")
        with z.open("3D/3dmodel.model", "w") as xml:

            def put(s):
                xml.write(s.encode("utf-8"))

            put(
                f'<?xml version="1.0" encoding="UTF-8"?><model xmlns="{ns}" unit="millimeter" xml:lang="en-US"><metadata name="Title">Front end V4 reference assembly</metadata><resources><basematerials id="1">'
            )
            for _, name, col in parts:
                srgb = col.toTuple()[:3] if col else (0.5, 0.5, 0.5)
                rgb = "".join(f"{int(np.clip(x, 0, 1) * 255 + 0.5):02X}" for x in srgb)
                put(
                    f'<base name={quoteattr(name.rsplit("/", 1)[-1])} displaycolor="#{rgb}"/>'
                )
            put(
                '<base name="Recessed fin field" displaycolor="#303538"/></basematerials>'
            )
            offset = 1
            rear_master = None
            rear_id = None
            rear_idx = None
            for i, (shape, name, col) in enumerate(parts):
                group = name.split("/")[0]
                if group == "fin_face":
                    from fin_mesh_v4 import strip_mesh

                    mesh = strip_mesh(name)
                    pitch_data = json.loads(
                        (ROOT / "grid/intercooler_tube_pitch_v4.json").read_text()
                    )
                    gap = pitch_data["period_mm"] - 4.3 - 0.23 - 0.06
                    r = 0.775
                    cells = (len(mesh.vertices) // 4 - 1) // 34
                    analytic = cells * (2 * (gap - 2 * r) + 2 * np.pi * r) * 0.23 * 2.1
                    assert abs(mesh.volume / analytic - 1) < 0.002
                    # Non-adaptive default kernel integration over the long
                    # corrugated curve can differ by several percent. Use the
                    # exact developed length; check adaptive integration too on
                    # a representative exported B-rep.
                    report[name]["analytic_volume_mm3"] = analytic
                    if name.endswith("_01"):
                        from OCP.BRepGProp import BRepGProp
                        from OCP.GProp import GProp_GProps

                        props = GProp_GProps()
                        BRepGProp.VolumePropertiesGK_s(shape.wrapped, props, 1e-5)
                        report[name]["adaptive_step_volume_mm3"] = props.Mass()
                        assert abs(props.Mass() / analytic - 1) < 0.001
                    report[name]["default_kernel_volume_mm3"] = report[name][
                        "volume_mm3"
                    ]
                    report[name]["volume_mm3"] = analytic
                    assert (
                        np.max(abs(mesh.bounds.flatten() - signature(shape)[:6]))
                        < 0.035
                    )
                elif group == "rear_fin_field":
                    from radiator_fins_v4 import Layout
                    from radiator_fins_v4 import mesh as rear_mesh

                    layout = Layout()
                    ii = int(name.rsplit("_", 1)[-1]) - 1
                    if rear_master is None:
                        rear_master = rear_mesh(name)
                        rear_id = i + 2
                        rear_idx = ii
                    delta = layout.atlas(
                        0.0, 0.0, (ii - rear_idx) * layout.tube_pitch
                    ) - layout.atlas(0.0, 0.0, 0.0)
                    mesh = rear_master.copy()
                    mesh.apply_translation(delta)
                    assert (
                        np.max(
                            abs(
                                mesh.bounds.flatten()
                                - np.asarray(report[name]["bbox_mm"])
                            )
                        )
                        < 0.04
                    )
                    report[name]["volume_mm3"] = layout.volume()
                else:
                    mesh = mesh_for(shape, group)
                if group != "fiberglass":
                    assert mesh.is_watertight and mesh.is_winding_consistent, (
                        name,
                        mesh.is_watertight,
                        mesh.euler_number,
                    )
                report[name]["mesh_triangles"] = len(mesh.faces)
                report[name]["mesh_watertight"] = mesh.is_watertight
                kind = "surface" if group == "fiberglass" else "model"
                o.write("o " + re.sub(r"[^a-zA-Z0-9_]+", "_", name) + "\n")
                np.savetxt(o, mesh.vertices, fmt="v %.9f %.9f %.9f")
                np.savetxt(o, mesh.faces + offset, fmt="f %d %d %d")
                offset += len(mesh.vertices)
                if group == "rear_fin_field" and i + 2 != rear_id:
                    matrix = "1 0 0 0 1 0 0 0 1 " + " ".join(f"{q:.9f}" for q in delta)
                    put(
                        f'<object id="{i + 2}" type="model" name={quoteattr(name)}><components><component objectid="{rear_id}" transform="{matrix}"/></components></object>'
                    )
                    report[name]["mesh_instance_of_id"] = rear_id
                    continue
                put(
                    f'<object id="{i + 2}" type="{kind}" name={quoteattr(name)} pid="1" pindex="{i}"><mesh><vertices>'
                )
                for start in range(0, len(mesh.vertices), 6000):
                    put(
                        "".join(
                            '<vertex x="{:.9f}" y="{:.9f}" z="{:.9f}"/>'.format(
                                *tuple(p)
                            )
                            for p in mesh.vertices[start : start + 6000]
                        )
                    )
                put("</vertices><triangles>")
                metal = np.zeros(len(mesh.faces), bool)
                if "Tube_core_with_recessed" in name:
                    measured = json.loads(
                        (ROOT / "grid/intercooler_v4_measurements.json").read_text()
                    )
                    loc = (
                        mesh.triangles_center - measured["local_frame_origin_xyz_mm"]
                    ) @ np.array(
                        measured["local_axes_front_lateral_up_as_car_xyz_rows"]
                    ).T
                    metal = abs(loc[:, 0] + 3.25) < 0.002
                if name.endswith("/rear_finned_core"):
                    coeff = json.loads(
                        (ROOT / "grid/rear_heat_exchanger_v4.json").read_text()
                    )["face_coefficients"]
                    xc, yc, zc = mesh.triangles_center.T
                    delta = xc - (
                        coeff[0] + coeff[1] * yc / 300 + coeff[2] * (zc - 415) / 80
                    )
                    metal = abs(delta + 1.1) < 0.002
                standard = '<triangle v1="%d" v2="%d" v3="%d"/>'
                recess = (
                    '<triangle v1="%d" v2="%d" v3="%d" pid="1" p1="'
                    + str(len(parts))
                    + '"/>'
                )
                for start in range(0, len(mesh.faces), 7000):
                    put(
                        "".join(
                            (recess if use else standard) % tuple(t)
                            for t, use in zip(
                                mesh.faces[start : start + 7000],
                                metal[start : start + 7000],
                            )
                        )
                    )
                put("</triangles></mesh></object>")
            put(
                "</resources><build>"
                + "".join(f'<item objectid="{i + 2}"/>' for i in range(len(parts)))
                + "</build></model>"
            )
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        tree = ET.fromstring(z.read("3D/3dmodel.model"))
        assert tree.attrib["unit"] == "millimeter"
        assert len(tree.findall(".//{*}object")) == len(parts)
        for e in tree.findall(".//{*}object"):
            entry = report[e.attrib["name"]]
            if "mesh_instance_of_id" in entry:
                assert (
                    int(e.find(".//{*}component").get("objectid"))
                    == entry["mesh_instance_of_id"]
                )
            else:
                assert len(e.findall(".//{*}triangle")) == entry["mesh_triangles"]
    # Native 3MF SDK checks relationships, units, object types and mesh resources.
    import lib3mf

    wrapper = lib3mf.Wrapper()
    native = wrapper.CreateModel()
    reader = native.QueryReader("3mf")
    reader.ReadFromFile(str(path))
    it = native.GetMeshObjects()
    counts = []
    while it.MoveNext():
        counts.append(it.GetCurrentMeshObject().GetTriangleCount())
    assert sorted(counts) == sorted(
        e["mesh_triangles"] for e in report.values() if "mesh_instance_of_id" not in e
    )
    scene = trimesh.load_scene(path, process=False)
    assert sum(
        len(scene.geometry[scene.graph[n][1]].faces) for n in scene.graph.nodes_geometry
    ) == sum(e["mesh_triangles"] for e in report.values())
    objmesh = trimesh.load(obj, force="mesh", process=False)
    assert len(objmesh.faces) == sum(e["mesh_triangles"] for e in report.values())
    path.replace(DEST / "front_end_v4_mm.3mf")
    obj.replace(DEST / "front_end_v4_mm.obj")


def run():
    DEST.mkdir(exist_ok=True)
    root = make()
    step = DEST / "front_end_v4_mm.step"
    root.export(str(step))
    before = {n: s for s, n, c in leaves(root)}
    opened = cq.Assembly.load(str(step))
    parts = leaves(opened)
    report = {}
    for shape, name, color in parts:
        assert shape.isValid(), name
        original = before[name]
        a, b = signature(original), signature(shape)
        assert (
            np.max(abs(a[:6] - b[:6])) < 0.002
            and np.allclose(a[6:], b[6:], atol=0.001, rtol=1e-6)
            and len(original.Faces()) == len(shape.Faces())
        ), name
        report[name] = {
            "solids": len(shape.Solids()),
            "faces": len(shape.Faces()),
            "bbox_mm": b[:6].round(4).tolist(),
            "volume_mm3": float(b[-1]),
            "area_mm2": float(b[-2]),
            "max_bbox_roundtrip_mm": float(max(abs(a[:6] - b[:6]))),
            "volume_roundtrip_mm3": float(b[-1] - a[-1]),
        }
    assert len(parts) == len(before)
    write_meshes(parts, report)
    record = {
        "frame": "X forward, Y car-left, Z up; mm",
        "step_reimport_names_and_geometry_verified": True,
        "files_used": {
            k: {"path": v, "sha256": sha256((ROOT / v).read_bytes()).hexdigest()}
            for k, v in SPEC.items()
        },
        "separate_parts": len(report),
        "solid_count": sum(e["solids"] for e in report.values()),
        "mesh_triangles": sum(e["mesh_triangles"] for e in report.values()),
        "parts": report,
    }
    (DEST / "assembly_checks.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        record["separate_parts"],
        "components",
        record["solid_count"],
        "solids",
        record["mesh_triangles"],
        "triangles",
    )


if __name__ == "__main__":
    run()
