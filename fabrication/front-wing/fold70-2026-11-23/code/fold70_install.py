"""Insert the 70 mm study in a copy of the verified installation at the original origin."""
from pathlib import Path
from hashlib import sha256
import json
import cadquery as cq
from package_front_v4 import leaves
root=Path(__file__).resolve().parents[1]
prior=root/'deliverables/full_folded_chin/installed_mm.step'
out=root/'deliverables/fold70'; src=out/'full_folded_chin_mm.step'
shape=cq.importers.importStep(str(src)).val()
assembly=cq.Assembly.load(str(prior))
name='complete_folded_splitter_chin'
item,=[item for item in assembly.children if item.name==name]
item.obj=shape.moved(item.loc.inverse)
assembly.name='Fold70_installation'
path=out/'installed_mm.step'
assembly.export(str(path))
new=leaves(cq.Assembly.load(str(path))); old=leaves(assembly)
assert [k for p,k,c in old]==[k for p,k,c in new] and len(new)==146
chin,=[s for s,k,c in new if k==name]
assert len(chin.Solids())==1 and chin.isValid() and abs(chin.Volume(1e-7)-shape.Volume(1e-7))<2.
(out/'assembly_check.json').write_text(json.dumps({'installed_sha256':sha256(path.read_bytes()).hexdigest(),'new_chin_sha256':sha256(src.read_bytes()).hexdigest(),'previous_assembly_sha256':sha256(prior.read_bytes()).hexdigest(),'component_count':len(new),'valid_single_chin':True},indent=2)+'\n')
