"""Regenerate the accepted faired right wing immediately before its blade union."""
from pathlib import Path
from tempfile import TemporaryDirectory
from inspect import getsource
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "code"))
import faired42_wing as accepted

if __name__ == "__main__":
    source = getsource(accepted.generate)
    union = "    result = result.fuse(upper_blade(side)).clean()\n"
    assert source.count(union) == 1
    namespace = vars(accepted).copy()
    exec(compile(source.replace(union, ""), accepted.__file__, "exec"), namespace)
    out = HERE / "blade_off_cad"
    out.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=HERE) as tmp:
        namespace["generate"]("right", Path(tmp), out)
