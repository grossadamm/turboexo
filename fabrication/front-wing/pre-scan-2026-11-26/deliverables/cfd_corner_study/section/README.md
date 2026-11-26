# Viscous screen of the right wing at car Y = −555 mm

**The upper blade aimed the near-exit passage flow about 9° steeper in this model, but the flow there was slower both upward and rearward.** This was consistent across two grids and two deliberately low Reynolds numbers. The unsteady wake farther back did not have a consistent turning angle. This study does not establish whether the blade diverts air past the actual tire or improves any vehicle force.

[Fine-grid flow comparison](section_comparison_1.25mm.png) · [Coarse grid](section_comparison_2mm.png) · [Reynolds-number sensitivity](section_comparison_re1300_2mm.png)

## What was compared

The accepted faired right-wing STL was intersected at car Y = −555.0 mm. The airstream in the plots travels left to right along −car X, and the road is at car Z = 0. The isolated section has a 211.761 mm chord. The blade’s fore/aft extent in that plane is 57.651 mm, and the nearest point-to-point gap to the main wing is 8.551 mm. The blade is a separate contour in this plane. The control drops only that contour and preserves exactly the same main outline, including the rising channel floor. A second comparison against the regenerated pre-blade STL agreed within 0.00186 mm in outline Hausdorff distance. Five enclosed lightening or spar-pocket loops are filled because they have no external path in this plane. No CAD was edited.

At 210 mm aft, the blade-on opening spans Z = 188.19–200.13 mm. The reported measurement uses the central 36% of that opening (Z = 192.01–196.30 mm) and exactly the same positions with the blade off. It is a local sample, not the whole gap flux. The angle is calculated from the two average velocity components, positive upward from horizontal. The amber line in the detail panel marks the sample.

| Chord Reynolds number and grid | Blade on rearward / upward / angle | Blade off rearward / upward / angle |
|---|---:|---:|
| 650, 1.25 mm | 0.319 / 0.243 / +37.2° | 0.819 / 0.444 / +28.5° |
| 650, 2 mm | 0.287 / 0.221 / +37.6° | 0.783 / 0.432 / +28.9° |
| 1,300, 2 mm | 0.534 / 0.404 / +37.1° | 0.913 / 0.498 / +28.6° |

Velocities are divided by incoming speed. In the fine run the blade-on sample had **61% less rearward velocity and 45% less upward velocity** than the same sample with the blade off. Across the 17 fine-grid snapshots spanning dimensionless times 14–22, blade-on upward velocity ranged from 0.199 to 0.293 of incoming speed and blade-off ranged from 0.403 to 0.483, with no overlap. At twice the Reynolds number, the reduction of the mean upward component was only about 19%. Magnitudes at low Reynolds number should not be extrapolated. The flow is also not slower at every point. At the upstream 167 mm aperture sample, the blade-on case had higher mean rearward and upward components.

Both cases produced an unsteady wake behind the primary wing. At the standardized 270 mm aft wake sample spanning Z = 180–220 mm, the mean blade-on flow angle changed with the grid/cadence and Reynolds number, and individual runs show both upward and downward wake flow over time. The plots show streamlines of averaged fields. They are not particle trajectories or proof of downstream control.

## Solver and checks

- Unsteady, weakly compressible D2Q9 two-relaxation-time lattice Boltzmann solver. No turbulence model. The solid surfaces use linear interpolated no-slip reflection at the actual section-link intersections. The blade cannot disappear between grid centers because links crossing it are also marked when both ends are fluid. [Bouzidi et al. boundary method](https://doi.org/10.1063/1.1399290), [Ginzburg et al. TRT formulation](https://www.global-sci.org/oldweb/cicp/issue/FULLPDF/3/427/paper.pdf).
- Box spans 350 mm forward to 770 mm aft and 0–470 mm above the road. Uniform horizontal velocity inlet, density outlet, slip top, and moving no-slip ground at inlet speed. A damping layer next to the top and outlet reduces reflected disturbances and was not varied. Other car surfaces and tire are omitted. Geometry cannot vary across the span. Free-stream lattice Mach number was 0.113. The grids each resolve the narrowest gap with roughly 4–7 spacings.
- All six runs reached dimensionless time 22, defined as incoming speed × time / main section chord. The snapshots from 14–22 were used for the reported averages, with five outputs on each coarse run and 17 on the fine runs. There were no non-finite values at saved times. Across all logged cases, inlet/outlet mass flux differed by at most about 0.6% of the reference inlet flux, and peak local lattice Mach was about 0.214. The outlet damping exchanges mass/momentum with the reservoir, so this is an inlet-to-outlet diagnostic, not a conservative residual or an assertion of steady convergence.
- A blank domain preserved uniform horizontal velocity to within 0.011% of incoming speed per velocity component after one chord transit. The shared collision and wall treatment matched analytic moving-wall Couette and fractional-wall shear-decay solutions to 0.0148% and 0.0775% relative velocity L2 error, respectively. These numerical checks do not validate the car flow.
- No road Reynolds number was attempted. For scale, a 0.212 m chord at 20 m/s in air with kinematic viscosity 1.5×10⁻⁵ m²/s is near Re = 280,000. This study’s artificial Re = 650 and 1,300, 2D geometry, absent tire/bumper, and laminar model cannot establish full-scale stall, wheel bypass, downforce, or drag. No force coefficients are inferred.

## Data and reproducibility

[Diagnostics and sampled histories](diagnostics.json) · [Averaged field arrays](mean_fields.npz) · [Section outlines and mesh provenance](section_profiles.json) · [Analytical verification log](benchmark.log)

The fields contain rearward velocity and upward velocity normalized by incoming speed, plus lattice density, on arrays ordered by height and aft distance. Solid centers are NaN. The included [run script](run.sh), [solver](solve.cpp), [analytic checks](benchmark.cpp), [section and link extraction](prepare.py), and [analysis](analyze.py) reproduce the cases. Preparation uses NumPy, Trimesh and Shapely. Figures and diagnostics use NumPy, SciPy and Matplotlib. The build shown uses Clang and Homebrew libomp. Archived snapshots can be reanalyzed with `FLOW_DIR=run_cache python3 analyze.py`.
