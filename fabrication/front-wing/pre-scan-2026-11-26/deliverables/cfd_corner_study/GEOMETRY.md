# Right front geometry for the flow screen

The two models share the same faired wing, bottom skin, chin, seal, bumper, right green metal, cooling package, and tire. The only change is the released wing's 42° upper blade. All lengths are millimetres. In solver coordinates, x increases rearward, y increases outboard on the right, and z increases upward. The centerplane is y=0 and the ground plane is z=0.

## Geometry included

| Part | Source and screen representation |
| --- | --- |
| Common right wing | Rebuilt using the accepted `code/faired42_wing.py` workflow, with only its final upper-blade union skipped. The vertical exterior envelope retains the lower fairing and 36° channel floor while capping internal lightening cavities and empty spar pockets. |
| Upper blade | The accepted generator's exact nominal standalone blade, tessellated and added as a Boolean obstacle mask to the common wing. No independent re-meshing of a different wing is used in the on case. |
| Fiberglass | Installed V9 exterior. At each lateral/elevation sample, the first longitudinal mesh strike starts an opaque volume that ends at a planar x=339.2 mm cap, near the rear of the fiberglass CAD. Rays that pass through actual openings without striking the fiberglass stay open until other modeled geometry. This preserves the projected frontal profile but is not the true inner wall, aft cheek, bonnet, or chassis. |
| Chin and seal | Installed rigid chin and compressed seal from `closed42_joint`, common to both cases. |
| Right green hardware | The two right-side solids from the V4 surveyed inboard bracket STEP (web and brace), plus the outer right plate from the released assembly family. Obsolete mount rail, add-on receivers and spars are excluded. |
| Center cooling | The nominal intercooler core and end tank, and the radiator core and tanks, are taken from the V4 CAD and treated as opaque solids at their actual nominal positions and dimensions. No pressure-drop law, suction, or mass flow through a core. No right-side duct inferred by mirroring the different car-left prototypes. |
| Right tire | Inferred straight-ahead CAD context pinned to the surveyed leading and inboard datums. The model fills the reference rim opening; it includes no tread, rotation, camber, steering, or load deformation. The nominal 580 × 205 mm reference envelope is not a measured tire specification. |

Walls are stair-stepped on a Cartesian grid. The raster uses triangle-ray intersections rather than a uniform high-resolution resampling. Panels and the blade use cell-center occupancy. If a thin physical interval lands between cell centers, it uses its nearest cell to avoid a numerical hole, which gives it approximately one cell of effective thickness in that direction. The resulting blockage and throat thickness are therefore grid-dependent.

## Validation and files

- Re-fusing the separately generated blade and control in OpenCascade reproduces the accepted STEP volume within 0.0033 mm³ using the same explicit integration tolerance. The rebuilt control is one valid B-rep solid, with a watertight single-solid STL.
- Independently sampling the native recombined CAD meshes and released combined STL on the same 1 mm lattice gives 99.866% solid occupancy overlap of the union. The most distant discrepant cell is 0.236 mm from the approved STL surface. That comparison excludes the screen's thin-sheet rounding and cavity-fill assumptions.
- Checks on three nonuniform Cartesian grids confirm that adding the blade only adds obstacle cells, all in the local blade envelope. At x=205 mm and y=550–568 mm, the nominal slot lies between the floor around z=184.8 mm and roof underside at z=195.9–196.2 mm.

`geometry.py` and `geometry_meshes.npz` are the runtime geometry and require only NumPy. `geometry_provenance.json` records source hashes and bounds. `geometry_validation.json` records the mesh and mask audit. `build_blade_control.py` and `prepare_geometry.py` reproduce the geometry from the original artifact tree with CadQuery, NumPy, SciPy, Shapely and trimesh. `verify_geometry.py` reproduces QA, with VTK for the independent closest-surface check.
