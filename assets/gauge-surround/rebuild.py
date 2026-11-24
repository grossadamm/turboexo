"""Rebuild the matched CAD pair into a separate directory, preserving release files."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--validate', action='store_true')
args = p.parse_args()
out = args.output.resolve()
if out == HERE or HERE in out.parents:
    p.error('Use an output directory outside the archived release')
if out.exists():
    p.error('Output directory must not exist')
shutil.copytree(HERE, out)
steps = ['upper_mount_revision/src/surround.py', 'display_trim_flush/src/build_trim.py']
if args.validate:
    steps += ['display_trim_flush/src/validate_trim.py',
              'display_trim_flush/src/check_sightlines.py',
              'display_trim_flush/src/check_removal.py']
for step in steps:
    subprocess.run([sys.executable, str(out / step)], check=True, cwd=out)
print('Rebuilt CAD:', out / 'display_trim_flush')
