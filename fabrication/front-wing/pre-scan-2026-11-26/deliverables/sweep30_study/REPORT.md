# Experimental 30° outward sweep

The comparison uses the same car-right corner in both simulations. The approved crest ends at 16° outward in plan. The study crest follows it for the first 80 mm, then turns progressively to 30°. Its trailing end moves 10.07 mm outward. The upper blade follows that curve at its original width. The outer footprint, sampled underside, 36° channel-floor exit and 42° upper-blade exit elevation are retained. The inboard shoulder grows wider and the outboard shelf narrower as a consequence of moving the crest. This is an exploratory geometry file.

[Matched overhead render](views/compare_top_16_vs_30_detail.png) · [Design curves and exit tangents](views/top_crest_traces.png) · [Overhead with tire context](views/compare_top_16_vs_30.png) · [Trial STEP](wing_right.step) · [CAD measurements](CAD.md)

## Results

Positive lateral angles and displacements point outboard. At 205 mm rearward, about 15 mm before the end of the wing, the fine-grid mean at the corresponding location within each slot changed from **4.22° inward to 2.03° outward**. Upward inclination at that location was 38.68° and 38.75° respectively. On the second grid the change in lateral angle was 6.10°, versus 6.25° on the finer grid. The 30° result was nearly straight back on the second grid. The robust result is a shift toward outboard flow inside the channel.

At the same fixed physical location inside both passages, the outward shift was about 11°. Part of that difference comes from the slot moving across the measurement window; the position relative to each crest is different there. The slot-relative comparison above is more informative for how each design guides air.

At 395 mm rearward, 23.5 mm ahead of the reference tire's foremost X station, the mean lateral angle across a fixed 85 × 90 mm patch shifted by just 0.008° and the mean upward angle by 0.016°. The pointwise RMS velocity-vector difference there was about 0.031% of freestream. This local footprint and the simplified flow model cannot establish changes to real wheel drag.

Of 2,162 shared upstream starting points, 231 crossed their respective slots and could be tracked clear of solids through the sampling plane in all four runs. At that plane the 30° design placed these streamlines about 5.3 mm farther outboard and 2.4 mm higher on average (4.8 and 1.9 mm on the second grid). All tracked endpoints remained inboard of the tire’s inner-face datum. The small changes in local flow direction near the tire and the larger accumulated position shifts measure different things. They do not show that air formerly striking the tire now clears it.

## Method and scope

Four blade-installed runs using the [same 3D potential-flow solver and boundary conditions](../cfd_corner_study/REPORT.md), with 1 and 1.5 mm local lateral and vertical resolution, 1.5 and 2.25 mm fore/aft. All non-wing obstacles came from the same CAD mesh cache. The baseline reruns reproduced the earlier blade-on fields byte for byte. The final trial mask used the independently checked final control body and separate upper blade. Both models omit the superseded mounting rail. The computed flow is idealized, steady and irrotational. The walls allow slip, the wheel is stationary and its envelope is inferred, and the cooling cores are blocked. Separation, tire wake, downforce and drag are outside this screen. The previous 2D section experiment was omitted because it cannot represent the lateral turn under study.

[Solver driver](cfd/compare_flow.py) · [Matched probe and streamline results](cfd/sweep_matched_metrics.json) · [Velocity-direction differences](cfd/sweep_direction_differences.png) · [Paired streamline displacement](cfd/sweep_matched_streamlines.png)

To reproduce from the existing artifact tree, activate a Python environment with NumPy, SciPy, matplotlib and PyAMG. In the cfd directory run the following before running evaluate_sweep.py. The geometry directory also contains the parametric CAD generator.

```sh
export OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1
for h in 1.5 1; do
  python compare_flow.py 16 "$h"
  python compare_flow.py 30 "$h" --control ../blade_off_cad/wing_right.stl --blade ../upper_blade.stl
done
python evaluate_sweep.py
```
