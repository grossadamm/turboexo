# Right-front channel flow study

The fitted 42° upper blade increases local upward inclination. In this screen it did not produce a measurable improvement in outward turning at the sampled tire approach. The baseline is the same 36° floor and swept crest with the upper blade removed. Both cases omit the superseded rectangular mount rail. The geometry derives from the approved front-end CAD; the fit-print project was not used or modified.

## What to take from the runs

- **Inside the slot:** On the finest 3D grid the same small 18 × 7 mm window gives an upward inclination of 28.9° open and 37.5° with the blade. The lateral component points 7.5° outboard open and 10.4° inboard with the blade. Both fine grids give the same direction of change; individual angles vary by several degrees.
- **Behind the lip:** At a fixed patch 8 mm behind the floor, mean flow actually points downward in both idealized runs. A direction measured inside the slot is a poor proxy for persistent jet direction.
- **Ahead of the wheel:** The blade changes both mean directional angles by less than 0.02° across an 85 × 90 mm patch 23.5 mm ahead of the foremost tire station. This spatial average cannot exclude localized changes, and the wheel's modeled wake is physically incomplete.
- **Following a narrow seed band:** All 120 seeds from the finest 3D run reached the sampling plane. At 395 mm rearward the blade-on seed group averaged 3.6 mm higher and 3.0 mm farther inboard than the open case. The direction of this small displacement persisted for the 112 paired survivors on the 1.5 mm grid. Coarser grids could not trace paired seeds through the slot without interpolating across solids. These are numerical streamline projections for this particular upstream seed band.
- **Independent 2D viscous check:** An isolated section through the slot also gave about 9° more upward inclination, while its upward speed fell in that model. The speed trend disagrees with the 3D slip model at their respective local probes. Neither establishes a road-speed increase in upward momentum. See the separate [viscous section study](section/README.md).

[Flow directions](directions.png) · [3D streamline projections](model_streamlines.png) · [Geometry and omitted components](GEOMETRY.md) · [Geometry provenance](geometry_provenance.json)

## 3D method

The finite-volume solver enforces divergence-free potential flow on nonuniform rectilinear cells. The velocities are relative to straight-ahead incoming air with unit speed. Scaling the inviscid field to a speed such as 20 m/s does not change its directions. Coordinates increase rearward, right/outboard, and up. Impermeable slip walls surround solid cells; the ground and vehicle center plane use zero normal flux. Far upstream, downstream, outboard and top boundaries fix the perturbation potential to zero. Sealed or disconnected fluid pockets are removed. No circulation condition is imposed. There is no viscous boundary layer, physical separation, turbulence, or rotating tire. The fiberglass is closed aft and the cooling cores are opaque. Neither downforce, drag, cooling nor wheel-wake efficiency is established.

The base domain is x = −1,500…2,250, y = 0…2,200 and z = 0…2,000 mm. Fine grid spacing is 1.5 mm rearward and 1 mm laterally and vertically in the refinement box, with larger cells farther away. The largest runs had about 5.2 million connected fluid cells. The comparison is one geometry change. The thin upper blade uses subcell occupancy protection to avoid broken surfaces.

Velocities are averaged on fixed planes using positive rearward flux as weight. Each reported direction is computed from the corresponding two averaged velocity components. Three windows, in mm:

| Station rearward | Outboard range | Height range | Purpose |
| --- | --- | --- | --- |
| 205 | 550–568 | 187.5–194.5 | Sample inside the blade-on passage; same physical region in the open case |
| 228 | 547–576 | 197–220 | Sample just downstream of the floor |
| 395 | 550–635 | 175–265 | Broad tire-approach patch |

### Sensitivity

Up/out values are angles in degrees. Positive out points toward the wheel side. The first column is local lateral spacing in mm and the far-domain size multiplier. The two coarser slot comparisons lose some valid interpolation area at the walls; use the two finer grids for the matched aperture. The domain expansion was run at the coarse resolution.

| Spacing / domain | Slot sampled area off / on (mm²) | Inside slot, open: up / out | Inside slot, upper blade: up / out | At tire patch, change: up / out |
| --- | --- | --- | --- | --- |
| 3 / 1 | 121.3 / 108.4 | +25.7 / +6.2 | +26.9 / -2.4 | -0.010 / -0.013 |
| 2 / 1 | 126.0 / 122.4 | +26.3 / +6.9 | +30.4 / -11.4 | -0.010 / -0.010 |
| 1.5 / 1 | 126.0 / 126.0 | +25.6 / +6.1 | +36.4 / -12.5 | -0.013 / -0.011 |
| 1 / 1 | 126.0 / 126.0 | +28.9 / +7.5 | +37.5 / -10.4 | -0.010 / -0.008 |
| 3 / 1.5 | 121.3 / 108.4 | +25.7 / +6.2 | +26.9 / -2.4 | -0.010 / -0.013 |

Every linear solve reached a relative residual below 1e−8, and the net flux imbalance across all outer boundaries was below 1e−8 of inlet flux. A separate sphere-in-uniform-flow check compared against the exact potential solution: RMS vector error between 1.6 and 2.8 radii was 0.83% of freestream at 5 mm spacing and 0.40% at 2.5 mm. These checks test numerics; they do not validate real-car aerodynamics. [NASA verification guidance](https://www.grc.nasa.gov/www/wind/valid/tutorial/verassess.html)

## Reproduce

From this directory, use a Python environment with NumPy, SciPy, PyAMG and Matplotlib. The cached CAD-derived triangles are included. Run `python verify.py`, then `python flow.py --spacing H` for H = 3, 2, 1.5 and 1. Run `python flow.py --spacing 3 --wide 1.5` for the domain check. Then run `python trace_flow.py` and `python figures.py`. The station results are in the JSON files named for grid, domain multiplier and blade configuration. The compressed NPZ arrays contain the local velocity fields, rather than full-domain output. The 2D model has its own [instructions](section/README.md).

A physical A/B tuft test at the channel exit and just upstream of the wheel would check whether the upward and outward directions persist. A road-speed CFD decision about tire flow would need a viscous 3D model, a moving ground plane, rotating wheel with measured geometry, a realistic cooling-flow path and refinement through the slot and wheel boundary layers.
