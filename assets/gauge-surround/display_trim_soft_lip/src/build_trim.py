"""Front fascia for upper_mount_revision. Units are mm.

Display-local X is viewer right, Y is up, Z points toward the viewer.
Z=0 is the glass face. Only the four lug seats support the fascia.
"""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

import cadquery as cq
import trimesh
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform

OUT = Path(__file__).resolve().parents[1]
ORIGINAL = OUT.parent / "display_trim"
APPROVED = OUT.parent / "upper_mount_revision"
sys.path.insert(0, str(APPROVED / "src"))
from geom import lbox, lcyl, lhex, to_model, trsf_local
from params import ACTIVE_CX, ACTIVE_H, ACTIVE_W, HOLE_X, HOLE_Y, HOLES, P, REF

FACE_Z = 2.30
RING_BACK_Z = .60
RETURN_Z = -.45
LUG_FACE_Z = -3.60
LUG_BACK_Z = -4.20
RELIEF = .62
WAIST_X = 83.96
OUTER_Y = 56.05
EAR_X = 91.37
BEZEL_CAD_X = 82.35
BEZEL_CAD_Y = 54.60
BODY_CLEARANCE = .50
PAD_D = 7.35
BORE_D = 3.6
SCREW_LENGTH = 14.
HEAD_D = 5.70
HEAD_H = 1.65
WASHER_T = .50
WASHER_D = 6.
BACK_APERTURE = (ACTIVE_W + 2 * RELIEF, ACTIVE_H + 2 * RELIEF)
FRONT_APERTURE = (BACK_APERTURE[0] + 2.1, BACK_APERTURE[1] + 2.55)
BACK_APERTURE_CY = .15
FRONT_APERTURE_CY = .36
LIP_BACK_Z = .35
LIP_THROAT_Z = .53
LIP_JOIN_Z = 1.10
LIP_APERTURE = (151.48, 95.18)
LIP_CY = .11
LIP_RADIUS = .18
LIP_EDGE_BEVEL = .10
LIP_LAND = 1.05
LIP_ROOT_OFFSET = 2.30
NUT_FACE = LUG_BACK_Z - P["pad_front_web"]
NUT_BACK = NUT_FACE - P["nut_t_nom"]
UNDER_HEAD = FACE_Z + WASHER_T
TIP_Z = UNDER_HEAD - SCREW_LENGTH

def to_local(shape):
    return cq.Shape.cast(BRepBuilderAPI_Transform(
        shape.wrapped, trsf_local().Inverted(), True).Shape())


def references():
    base = cq.importers.importStep(str(APPROVED / "surround.step")).val()
    lcd = {name: cq.Shape.importBrep(str(REF / "vendor" / f"lcd_{name}.brep"))
           for name in ("frame_lugs", "glass_1", "glass_2")}
    return to_local(base), {name: to_local(shape) for name, shape in lcd.items()}


def outline(z, left_corner_draft=0.):
    """A single spline outline with wide upper/lower borders and blended ears."""
    quarter = [
        [(72.5, OUTER_Y), (77., OUTER_Y), (84., OUTER_Y), (88.2, 54.23)],
        [(88.2, 54.23), (90.5, 53.23), (EAR_X, 51.95), (EAR_X, HOLE_Y)],
        [(EAR_X, HOLE_Y), (EAR_X, 46.05), (89.1, 45.01), (87.1, 43.05)],
        [(87.1, 43.05), (84.7, 40.70), (WAIST_X, 38.5), (WAIST_X, 35.0)],
    ]
    # The adjacent approved rail has a vertical face at X=-91.05.
    # Keep the lower-left nose tight and bring its blend in below the rail.
    lower_left = [
        [(72.5, OUTER_Y), (77., OUTER_Y), (83., OUTER_Y), (87.3, 53.64)],
        [(87.3, 53.64), (89.4, 52.95), (90.90, 51.45), (90.90, HOLE_Y)],
        [(90.90, HOLE_Y), (90.90, 47.18), (89.25, 45.23), (87.1, 43.05)],
        quarter[3],
    ]

    def pt(x, y):
        return cq.Vector(x, y, z)

    edges = []
    for sx, sy in HOLES:
        for segment in (lower_left if (sx, sy) == (-1, -1) else quarter):
            retreat = {(-1,-1):left_corner_draft, (1,-1):.28}.get((sx,sy), 0.)
            points = [pt(sx*(x-retreat*max(0., x-86.8)/(90.90-86.8)), sy*y)
                      for x,y in segment]
            edges.append(cq.Edge.makeBezier(points))
    for sign in (-1, 1):
        edges.append(cq.Edge.makeLine(pt(-72.5, sign*OUTER_Y), pt(72.5, sign*OUTER_Y)))
        edges.append(cq.Edge.makeLine(pt(sign*WAIST_X, -35.), pt(sign*WAIST_X, 35.)))
    return cq.Wire.assembleEdges(edges)


def rectangle_wire(width, height, radius, z, x=0., y=0.):
    """A planar rounded rectangle with a fixed centre and outer size."""
    if not radius:
        return cq.Workplane("XY", origin=(x, y, z)).rect(width, height).val()
    sketch = cq.Sketch().rect(width, height).vertices().fillet(radius)
    return sketch._faces.Faces()[0].outerWire().translate((x, y, z))


def approved_aperture_at(z):
    # The released aperture tool extends 0.01 mm beyond both web faces.
    t = (z - (RING_BACK_Z - .01)) / (FACE_Z - RING_BACK_Z + .02)
    size = [a + t * (b - a) for a, b in zip(BACK_APERTURE, FRONT_APERTURE)]
    return rectangle_wire(*size, .4 + .6*t, z, ACTIVE_CX,
                          BACK_APERTURE_CY + t * (FRONT_APERTURE_CY - BACK_APERTURE_CY))


def lip_wire(z, offset):
    return rectangle_wire(*(n + 2*offset for n in LIP_APERTURE),
                          LIP_RADIUS + offset, z, ACTIVE_CX, LIP_CY)


def aperture():
    return cq.Solid.makeLoft([
        lip_wire(LIP_BACK_Z-.02, LIP_EDGE_BEVEL),
        lip_wire(LIP_BACK_Z, LIP_EDGE_BEVEL),
        lip_wire(LIP_THROAT_Z, 0.),
        approved_aperture_at(LIP_JOIN_Z),
        approved_aperture_at(FACE_Z+.01),
    ], ruled=True)


def inner_lip_blank():
    # The rear chamfer ends in a flat land. The outside of the lip slopes
    # into the web and recedes as the part rises from the print bed.
    return cq.Solid.makeLoft([
        lip_wire(LIP_BACK_Z, LIP_EDGE_BEVEL+LIP_LAND),
        lip_wire(RING_BACK_Z, LIP_ROOT_OFFSET),
        lip_wire(RING_BACK_Z+.05, LIP_ROOT_OFFSET),
    ], ruled=True)


def fasteners(x, y):
    washer = lcyl(x, y, FACE_Z, UNDER_HEAD, WASHER_D).cut(lcyl(x, y, FACE_Z-.1, UNDER_HEAD+.1, 3.2))
    # Simplified threaded shank and rounded cap with a 2 mm hex socket.
    cap = lcyl(x, y, UNDER_HEAD, UNDER_HEAD+HEAD_H, HEAD_D)
    rim = [edge for edge in cap.Edges() if abs(edge.Center().z-UNDER_HEAD-HEAD_H)<1e-6]
    cap = cap.fillet(1.25, rim)
    screw = cap.fuse(lcyl(x,y,TIP_Z,UNDER_HEAD,3.)).cut(
        lhex(x, y, UNDER_HEAD+HEAD_H-1.05, UNDER_HEAD+HEAD_H+.1, 2.))
    nut = lhex(x,y,NUT_BACK,NUT_FACE,P["nut_af_nom"]).cut(
        lcyl(x,y,NUT_BACK-.1,NUT_FACE+.1,3.))
    return {"Button head screw": screw, "Washer": washer, "Retained nut": nut}


def make_trim():
    body = cq.Solid.makeLoft([outline(RING_BACK_Z), outline(FACE_Z, .63)], ruled=True)
    body = body.fillet(.22, [e for e in body.Edges() if abs(e.Center().z-FACE_Z)<1e-6])
    # The three short returns register around the body with clearance.
    # An open lower edge can rise past the bezel during removal.
    cavity_x = BEZEL_CAD_X+BODY_CLEARANCE
    cavity_y = BEZEL_CAD_Y+BODY_CLEARANCE
    lip = [lbox(-74.,74.,cavity_y,OUTER_Y-.06,RETURN_Z,RING_BACK_Z+.05)]
    for sx in (-1, 1):
        x0, x1 = sorted([sx*cavity_x, sx*(WAIST_X-.06)])
        lip.append(lbox(x0,x1,-35.,43.,RETURN_Z,RING_BACK_Z+.05))
    cutouts = [aperture()]
    pads = []
    for sx, sy in HOLES:
        x, y = sx*HOLE_X, sy*HOLE_Y
        pad = lcyl(x,y,LUG_FACE_Z,RING_BACK_Z+.05,6.7 if (sx,sy)==(-1,-1) else PAD_D)
        if (sx, sy) == (-1, -1):
            pad = pad.cut(
                lbox(-95,x-3.0,-55,-42,LUG_FACE_Z-.1,RING_BACK_Z+.1),
                lbox(-95,-80,y+2.95,-42,LUG_FACE_Z-.1,RING_BACK_Z+.1))
        pads.append(pad)
        cutouts.append(lcyl(x,y,LUG_FACE_Z-.1,FACE_Z+.1,BORE_D))
        cutouts.append(cq.Solid.makeCone(BORE_D/2, BORE_D/2+.25, .25,
                                       cq.Vector(x,y,FACE_Z-.25)))
    return body.fuse(*lip,*pads,inner_lip_blank()).cut(*cutouts).clean()


def make_print(trim):
    """Flat cosmetic face on bed; Y inverted by the proper rigid rotation."""
    return trim.rotate((0,0,0),(1,0,0),180).translate((0,0,FACE_Z))


def export_assembly_3mf(parts):
    """Reference-only 3MF with separately named and colored assembly objects."""
    core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    model = ET.Element("model", xmlns=core, unit="millimeter")
    ET.SubElement(model, "metadata", name="Title").text = "TurboExo fascia installed — reference only"
    resources = ET.SubElement(model, "resources")
    colors = ET.SubElement(resources, "basematerials", id="1")
    build = ET.SubElement(model, "build")
    for i, (name, shape, color) in enumerate(parts, 2):
        v, f = shape.tessellate(.035, .12)
        mesh = trimesh.Trimesh([p.toTuple() for p in v], f)
        mesh.update_faces(mesh.nondegenerate_faces() & mesh.unique_faces())
        mesh.remove_unreferenced_vertices()
        assert mesh.is_watertight and mesh.is_winding_consistent, name
        ET.SubElement(colors, "base", name=name, displaycolor=color)
        obj = ET.SubElement(resources, "object", id=str(i), name=name, type="model",
                            pid="1", pindex=str(i-2))
        xmlmesh = ET.SubElement(obj, "mesh")
        vertices = ET.SubElement(xmlmesh, "vertices")
        triangles = ET.SubElement(xmlmesh, "triangles")
        for vertex in mesh.vertices:
            ET.SubElement(vertices, "vertex", dict(zip(("x","y","z"), map(lambda x: f"{x:.7f}", vertex))))
        for face in mesh.faces:
            ET.SubElement(triangles, "triangle", dict(zip(("v1","v2","v3"), map(str, face))))
        ET.SubElement(build, "item", objectid=str(i))
    with ZipFile(OUT / "display_trim_assembly.3mf", "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>""")
        archive.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>""")
        archive.writestr("3D/3dmodel.model", ET.tostring(model, encoding="utf-8", xml_declaration=True))


def main():
    base, lcd = references()
    trim = make_trim()
    assert trim.isValid() and len(trim.Solids()) == 1
    model_trim = to_model(trim)
    model_trim.exportStep(str(OUT / "display_trim.step"))
    model_trim.exportStl(str(OUT / "display_trim.stl"), .035, .12)
    make_print(trim).exportStl(str(OUT / "display_trim_face_down.stl"), .035, .12)
    parts = [("Approved surround", to_model(base), "#666E7A"),
             ("Soft-lip fascia", model_trim, "#6ABBCB")]
    colors = {"frame_lugs": "#C7C9C3", "glass_1": "#263246", "glass_2": "#0B587C"}
    for name, part in lcd.items():
        parts.append((f"OEM {name}", to_model(part), colors[name]))
    for sx, sy in HOLES:
        for (name, part), color in zip(fasteners(sx*HOLE_X, sy*HOLE_Y).items(),
                                       ("#555966", "#929BA1", "#BE9B69")):
            parts.append((f"{name} {sx:+d} {sy:+d}", to_model(part), color))
    assy = cq.Assembly(name="TurboExo display and soft-lip fascia")
    for name, part, color in parts:
        assy.add(part, name=name, color=cq.Color(*(int(color[i:i+2], 16)/255 for i in (1,3,5))))
    assy.export(str(OUT / "display_trim_assembly.step"))
    export_assembly_3mf(parts)


if __name__ == "__main__":
    main()
