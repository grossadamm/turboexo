"""Local STEP tessellation helper; replaces legacy preview-module dependency only."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import trimesh

def step_mesh(path):
    python = os.environ.get('CAD_PYTHON', sys.executable)
    code = 'import cadquery as c,sys; c.importers.importStep(sys.argv[1]).val().exportStl(sys.argv[2],tolerance=0.035,angularTolerance=0.075,relative=False)'
    with tempfile.TemporaryDirectory() as tmp:
        stl = Path(tmp) / 'mesh.stl'
        subprocess.run([python, '-c', code, str(path), str(stl)], check=True)
        mesh = trimesh.load_mesh(stl, process=False)
    if not len(mesh.faces):
        raise ValueError(f'Empty mesh: {path}')
    return mesh
