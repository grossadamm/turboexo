# Accepted ESP32-P4 cluster mocks

**Status: accepted by the user on 2026-11-19.** This directory is the canonical
visual baseline for Street, Track and Tuning on the 4D Systems ESP32-P4-70
(7-inch, 1280 × 800, non-touch). Earlier concepts and review screenshots in
`work/` are not the accepted baseline.

Open `replay.html` to use the self-contained animated mock. It starts in Track;
mode switching preserves playback position. Play, seek, playback speed, and
“Jump to revs” operate on the same clip. No server or network is required.

## Accepted design

- **Street:** mint on black, large centered speed, wide RPM arc and numeric RPM;
  compact filled bars below for oil pressure, coolant, fuel and boost/vacuum.
- **Track:** orange on black, rising RPM ribbon, dominant RPM and separate speed;
  compact filled bars below for oil pressure, oil temperature, coolant and boost.
- **Tuning:** cyan on black, separated RPM/load/raw AFR/target/throttle readings,
  three aligned rolling traces, and supporting numeric diagnostics. The traces
  show eight preceding seconds; only the graph's “−8 s” and “NOW” labels remain.
- Keep explicit scales, units, icons and readable labels. Boost fills outward
  from zero. Do not substitute unscaled arcs/dots for the accepted bars or shrink
  Street's primary instrument to make equal-weight side groups.

| Display | Street | Track |
| --- | --- | --- |
| RPM | 0–8,000 rpm | 0–8,000 rpm |
| Oil pressure | 0–100 psi | 0–100 psi |
| Coolant | 120–280°F | 120–240°F |
| Oil temperature | — | 140–300°F |
| Fuel | E / ½ / F and percent | — |
| Boost/vacuum | −15 / 0 / +15 psi | −15 / 0 / +15 psi |

Street's coolant scale was retained when the subsequent Track-only scale review
narrowed Track's coolant range. These are display bounds, not approved operating
limits, warning thresholds, a boost target or a redline setting.

## Data and implementation boundary

`data.json` contains 576 original samples from the October 23 recording,
750.082–804.507 seconds (54.425 seconds), including the 6,890 rpm peak.
`provenance.txt` records channel mappings, source locations and CSV/MLG hashes.
The original source files are not needed to play this saved extract.

- Engine numbers are recorded samples. RPM graphics interpolate between them.
- Speed, fuel and oil temperature are explicitly simulated preview inputs in
  `player.js`, pending wiring of their data into the cluster. Their absence from
  this extract is not a claim that the car lacks those data sources.
- Simulated speed is independent of the recorded stationary revs; it is not
  inferred from RPM. Fuel is approximately 62%; simulated oil temperature is
  206–212°F. The caption identifies the simulated fields.
- Boost is `(MAP − barometric pressure) × 0.1450377`, in psi gauge.
- The extract's temperature units were inferred; the repository project setting
  also selects FAHRENHEIT and its INI defines the Celsius-to-Fahrenheit conversion.
- Oil-pressure calibration and AFR readiness remain unverified. Tuning displays
  raw recorded AFR and target without asserting valid mixture measurements.
- Acceptance covers the visual mocks and replay behavior. This is not ECU/P4
  firmware, a hardware performance test, or approval of protection settings.

## Rebuild and validation

Edit the mode renderers and shared sources, then run:

```sh
python3 dashboard/esp32p4-mocks/build.py
```

`replay.html` embeds the JSON and scripts. It is checked in so the accepted version
is immediately usable. `shell.html` provides the preview controls and disclosure.
`ui.js` embeds the stock SVG shapes retained under `icons/`.

Before acceptance, all three modes were rendered and inspected; Street received
independent visual and scale-mapping reviews plus extreme-value checks. Rendering
was exercised across all 576 samples, and playback, seeking, mode continuity,
end-of-clip stop and restart were checked. These checks do not establish driving
legibility on the physical display.

Icons: Lucide Static 0.468.0 (ISC; fuel, thermometer, battery, gauge) and
Material Design Icons SVG 7.4.47 (Apache-2.0; oil). Original package license notices
are retained in `icons/`.
