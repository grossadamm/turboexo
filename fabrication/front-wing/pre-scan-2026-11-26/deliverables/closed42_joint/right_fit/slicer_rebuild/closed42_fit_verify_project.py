#!/usr/bin/env python3
"""Verify the native Bambu project and actual embedded per-plate G-code."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET
import zipfile
from closed42_fit_slicer import PLATES, PROD, read_binary_stl, tag

EXPECTED = {
    'printer_settings_id': 'Bambu Lab P1S 0.4 nozzle',
    'printer_model': 'Bambu Lab P1S',
    'nozzle_diameter': ['0.4'],
    'filament_settings_id': ['Generic PLA'],
    'filament_type': ['PLA'],
    'nozzle_temperature_initial_layer': ['220'],
    'nozzle_temperature': ['220'],
    'textured_plate_temp_initial_layer': ['55'],
    'textured_plate_temp': ['55'],
    'curr_bed_type': 'Textured PEI Plate',
    'initial_layer_print_height': '0.2',
    'layer_height': '0.28',
    'wall_loops': '2',
    'sparse_infill_density': '3%',
    'sparse_infill_pattern': 'gyroid',
    'enable_support': '1',
    'support_type': 'tree(auto)',
    'support_style': 'tree_slim',
    'support_on_build_plate_only': '1',
    'support_critical_regions_only': '1',
    'support_top_z_distance': '0.28',
    'support_bottom_z_distance': '0.28',
    'brim_type': 'outer_only',
    'brim_width': '5',
    'brim_object_gap': '0.1',
    'bed_exclude_area': ['0x0','18x0','18x28','0x28'],
    'printable_area': ['0x0','256x0','256x256','0x256'],
    'printable_height': '250',
}
IDENTITY = (1.,0.,0.,0.,1.,0.,0.,0.,1.)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def get_attrs(elem):
    return {a.attrib['key']: a.attrib['value'] for a in elem.findall('metadata') if 'key' in a.attrib}


def check_file(project, source, first_result, second_result, toolpath):
    for sl in (first_result, second_result):
        assert sl['return_code'] == 0 and sl['error_string'] == 'Success.'
        assert len(sl['sliced_plates']) == 2
        for plate, (name, filename) in zip(sl['sliced_plates'], PLATES):
            assert plate['warning_message'] == ''
            assert len(plate['objects']) == 1 and plate['objects'][0]['name'] == name, plate['objects']
    report = {'project': project.name, 'project_sha256': sha256(project.read_bytes()), 'slicer': 'Bambu Studio 02.09.01.70', 'reopen_and_reslice_success': True, 'printer_dispatch': False, 'plates': []}
    with zipfile.ZipFile(project) as z:
        assert z.testzip() is None
        settings = json.loads(z.read('Metadata/project_settings.config'))
        for key, value in EXPECTED.items():
            assert settings[key] == value, (key, settings[key], value)
        report['verified_embedded_project_settings'] = {k: settings[k] for k in EXPECTED}
        config = ET.fromstring(z.read('Metadata/model_settings.config'))
        slicing = ET.fromstring(z.read('Metadata/slice_info.config'))
        outer = ET.fromstring(z.read('3D/3dmodel.model'))
        for i, (name, filename) in enumerate(PLATES, 1):
            plate = next(p for p in config.findall('plate') if get_attrs(p)['plater_id'] == str(i))
            attrs = get_attrs(plate)
            assert attrs['plater_name'] == name
            assert len(plate.findall('model_instance')) == 1
            oid = get_attrs(plate.find('model_instance'))['object_id']
            part = config.find(f"object[@id='{oid}']/part")
            assert get_attrs(part)['source_file'] == filename
            comp = outer.find(f".//{{*}}object[@id='{oid}']/{{*}}components/{{*}}component")
            item = outer.find(f".//{{*}}build/{{*}}item[@objectid='{oid}']")
            mesh = ET.fromstring(z.read(comp.get(tag(PROD, 'path')).lstrip('/')))
            localvs = [tuple(float(v.attrib[k]) for k in 'xyz') for v in mesh.findall('.//{*}vertex')]
            triangles = [tuple(int(t.attrib[k]) for k in ('v1','v2','v3')) for t in mesh.findall('.//{*}triangle')]
            component_tx = tuple(map(float, comp.get('transform').split()))
            build_tx = tuple(map(float, item.get('transform').split()))
            assert component_tx[:9] == build_tx[:9] == IDENTITY, (component_tx,build_tx)
            tx = [a+b-c for a,b,c in zip(component_tx[9:], build_tx[9:], (307.2*(i-1), 0., 0.))]
            local_bounds = [list(map(fn, zip(*localvs))) for fn in (min,max)]
            actual_bounds = [[dim+delta for dim,delta in zip(point,tx)] for point in local_bounds]
            src_vs, src_tri = read_binary_stl(source / filename)
            translation = [128,132.4 if i == 1 else 128,0]
            assert len(triangles) == len(src_tri) and len(localvs) == len(src_vs)
            max_delta = 0.0
            for g, s in zip(triangles, src_tri):
                for ag, bs in zip(g, s):
                    max_delta = max(max_delta, math.dist([v+t for v,t in zip(localvs[ag],tx)], [v+t for v,t in zip(src_vs[bs],translation)]))
            assert max_delta < 0.0001, max_delta
            for img_role in ('thumbnail_file','thumbnail_no_light_file','top_file','pick_file'):
                assert z.read(attrs[img_role]).startswith(b'\x89PNG\r\n\x1a\n')
            gcode_path = f'Metadata/plate_{i}.gcode'
            assert attrs['gcode_file'] == gcode_path
            gcode = z.read(gcode_path)
            assert hashlib.md5(gcode).hexdigest() == z.read(gcode_path+'.md5').decode().lower(), gcode_path
            assert '= "Generic PLA"' in gcode[:60000].decode() and '= Bambu Lab P1S 0.4 nozzle' in gcode[:60000].decode()
            m = re.search(rb'; model printing time: ([^;]+); total estimated time: ([^\r\n]+)',gcode[:5000])
            total_estimate = m.group(2).decode()
            estimate_g = float(re.search(rb'; total filament weight \[g\] : ([\d.]+)', gcode[:5000]).group(1))
            ps = next(p for p in slicing.findall('plate') if get_attrs(p)['index'] == str(i))
            assert get_attrs(ps)['outside'] == 'false' and get_attrs(ps)['support_used'] == 'true'
            assert ps.find('filament').get('type') == 'PLA'
            assert float(ps.find('filament').get('used_g')) == estimate_g
            path = toolpath[str(i)]
            assert path['violation_count'] == 0 and path['deposition_commands_by_feature']['Support'] > 0 and path['deposition_commands_by_feature']['Brim'] > 0
            report['plates'].append({'plate': i, 'name': name, 'source_stl': filename, 'source_stl_sha256':sha256((source/filename).read_bytes()), 'triangle_count': len(triangles), 'mesh_only_transform_from_stl_to_physical_plate_mm': translation, 'max_distance_from_source_face_vertex_mm': max_delta, 'physical_plate_mesh_bounds_mm': actual_bounds, 'bed_clearance_mm_lower_bound': path['minimum_bed_edge_clearance_mm'], 'excluded_corner_clearance_mm_lower_bound': path['minimum_exclusion_zone_clearance_lower_bound_mm'], 'gcode': gcode_path, 'gcode_sha256': sha256(gcode), 'estimated_total_time': total_estimate, 'estimated_filament_g': estimate_g, 'slice_warning': None})
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('project', type=Path)
    p.add_argument('source_directory', type=Path)
    p.add_argument('first_result', type=Path)
    p.add_argument('second_result', type=Path)
    p.add_argument('toolpath_report', type=Path)
    ns = p.parse_args()
    print(json.dumps(check_file(ns.project, ns.source_directory, *(json.loads(k.read_text()) for k in (ns.first_result, ns.second_result, ns.toolpath_report))), indent=2))


if __name__ == '__main__':
    main()
