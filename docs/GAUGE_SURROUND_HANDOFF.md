# Gauge surround handoff — 2026-11-24

## Current state

The user started `TurboExo_Bracket_TEST_PLA_2wall_028.gcode.3mf` from Handy after
its SD-card upload and full readback checksum verification. This is a PLA fit test:
2 walls, 0.28 mm layers, 0.20 first layer, 55 degree tilt, P1S 0.4 mm/textured PEI,
220 C nozzle and 55 C bed, snug supports. Estimate 8 h 13 min / 280.28 g.
User confirmation is the evidence of start; we have not independently checked
live progress, completion or the physical result. Do not duplicate the job.

Authoritative saved package: [assets/gauge-surround](../assets/gauge-surround/README.md).
Current matched base and fascia are **display_trim_flush**. Its base mesh is the
one in the active PLA job; the job's archive verifies identical geometry and pose
to the ASA release. Both mounting slots and four nut seats are clear of sampled
support beads. Lower nut-loading approaches still need support cleanup.

## User decisions that must survive the handoff

- Whole main surround is one piece, with integrated braced vehicle mounts.
- Solid uninterrupted flat roof: **NO USB cutout and NO USB cover**.
- Straight outer shade edges: no inherited inward steps or tapers. Roof is
  279.48 x 192.49 mm; the wider shade accommodates the display/sidewalls.
- Preserve corrected display pose and manufacturer mounting dimensions.
- Round/blend the upper display ears; preserve their true bore axes and lug seats.
- Actual vehicle bolt openings, not blank transfer-drill pads.
- Front fascia conceals bezel and tabs, not a full rear enclosure.
- Preserve BOTH the soft inner lip toward the glass AND the flush outer perimeter
  transition closing the marked top/side gaps. Use the matched base with it.
- Shared four mounting screws secure fascia + display to the base; M3 x 14 with
  washers replaces the original too-short M3 x 8.
- User accepts removing the whole surround for service.
- User wants coherent design, not accumulating patches, repeated reviews, or an
  unsolicited test-gauge detour. Discuss design preferences before changing them.
- Current print material is PLA for testing. ASA was the intended later material.
- Use Codex for further delegation; the user switched away from the Claude-key path.

## Hardware and CAD facts

Display: 4D Systems ESP32-P4-70 non-touch. OEM body 164.8 x 109.3 mm, active area
150.72 x 94.20 mm (display-local active center X=-1.65 mm). Four lug holes
173.70 x 98.40 mm, OEM diameter 3.5 mm; base bores 3.4 mm, trim bores 3.6 mm.
Exact vendor BReps/component envelopes and transformed pose are saved in
`upper_mount_revision/inputs/`. Hood coordinate frame: rear-right top corner,
+X forward, +Y car-left, +Z hood normal. Do not confuse print orientation with this.

Printed vehicle slots: right 8.4 x 5.5 mm; left 8.4 x 6.6 mm, through 6 mm pads.
These include modest clearance around photo-derived metal-slot estimates.
Vehicle faces retain nominal right 7 mm / left 4 mm offsets from estimated steel
planes. Actual spacer fit, fastener/backing choice and installed tool approach
have not been physically confirmed. Metal outer slots on square tabs are targets;
inner round holes are separate features. Do not casually shift axes based on
inconsistent photo registrations.

Fascia: 1.70 mm front web, minimum nominal glass gap 0.35 mm, soft bevel/taper at
inner opening. Screw load transfers to metal lugs, not glass. The current outer
perimeter uses shallow matched base lands to hide seam daylight while retaining
assembly clearance. CAD check found zero installed overlap, active-screen view
clear from three recorded eyes plus normal, and a continuous removal-clearance
bound of 0.121 mm. This is tight nominal geometry, not a physical fit guarantee.

Shared hardware: 4 fully threaded M3 x 0.5 x 14 ISO 7380-1 button heads, 4 DIN 433
washers (6 OD x 3.2 ID x 0.5), existing 5.5 AF x 2.4 mm M3 nuts. The original M3x8
is too short with fascia. See release README for the tilted fascia removal path;
LCD then moves 10 mm up + 20 mm toward viewer together, followed by straight out.

## Checks performed and what remains

- STEP reloads: valid one solid per printed part. STL: connected/watertight.
- OEM screw centers and lug seating planes independently checked against vendor CAD.
- Actual glass/body/PCB, hardware paths, removal and sightline checks passed in CAD.
- The earlier left support/green-steel interference was removed in the rebuilt base;
  six prior witness points clear by 2.17–5.18 mm before the seam-land refinement.
- Slice projects were checked for the actual model assignment, material, pose,
  support exclusions and G-code. Four-wall ASA/PLA variants are superseded for the
  test now running. The PLA draft saved here preserves the final shape.
- Photo registration has depth/normal ambiguity. Independent alternatives disagreed,
  so the final fit review recommended keeping the best-supported axes for fitting,
  not applying a speculative offset. Review evidence is archived for context.
- Physical fit, backing/tool access, thermal performance and vibration life remain
  unmeasured. The next useful evidence is the user's printed-part result. Record
  observed fit and any signed corrections; don't restart the whole reconstruction.

## Source evidence and local continuation

Original capture: `/Users/adamgross/Desktop/newdash/IMG_2740..2745.HEIC` and
`IMG_2746.MOV`; calibrated extracts and scan:
`/Users/adamgross/dev/artifacts/gauge-surround-2026-11-20/`.
New exposed-hole photographs IMG_2850/2851/2852 are archived in `evidence/`.
Raw MOV/old still reads sometimes returned OS error 11; archived extracts were used.
Original measurement/pose JSON and vendor geometry needed for rebuild are committed.

Working artifact root: `/Users/adamgross/dev/artifacts/gauge-surround-design-2026-11-21/`.
Original conversation T3 thread ID: `3e6490b6-bda2-4f93-b62e-91ca39b9daff`.
Prior HTML painter renderer made false roof tears; current viewer uses WebGL depth
buffering. Don't interpret mesh triangulation artifacts as a damaged flat surface.

## Printer upload, if later explicitly requested

User starts jobs through Handy. The last action was upload-only, not automatic start.
Verified remote path: `/model/TurboExo_Bracket_TEST_PLA_2wall_028.gcode.3mf`.
Older ASA and four-wall PLA files are also on the SD card; name the correct job.
Authenticated FTPS used the existing printer at 192.168.1.108:990 with saved Studio
serial/access code read privately from its configuration. Never commit or print
credentials. Trust used Bambu Studio's installed
`/Applications/BambuStudio.app/Contents/Resources/cert/printer.cer`, hostname matched
to saved serial and partial-chain verification. No certificate validation disabled.
The obsolete /private/tmp printer.pem had disappeared; it is not required now.
Upload helper remains outside the repo under `printer_upload/` or `pla_test_draft/`.
Readback SHA-256 verification is mandatory before reporting upload complete.
No print should be started just because an upload succeeded.

Desktop UI returned cgWindowNotFound across Studio and Finder; Mac lock state was
not independently established. Direct FTPS upload worked despite that. Don't invent
an unlocked desktop or assume no printer connection solely from UI failure.
