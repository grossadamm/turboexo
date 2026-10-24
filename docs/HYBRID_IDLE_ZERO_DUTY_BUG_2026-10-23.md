# Suspected Speeduino hybrid-idle zero-duty output defect

Recorded: 2026-10-23. Local investigation record; not submitted upstream.

## Finding and confidence

Source inspection confirms that the PWM Closed+Open loop (hybrid) zero-duty
path calls `disableIdle()`, but its PWM shutdown condition omits hybrid mode.
This is a verified code omission in the inspected firmware. Its responsibility
for the observed RPM spikes is a supported hypothesis, not electrically proven.

Vehicle: 1999 Miata BP-4W / Speeduino UA4C (AVR). Tune reports firmware
2025.01.6, signature speeduino 202501. Relevant source was inspected at tag
202501.6; the flashed binary was not independently identified or hashed.
Idle: PWM Closed+Open loop, one channel, Normal, 500 Hz; target800 RPM warm;
P0.0625/I0.03125/D0 (raw2/1/0), maximum99%, TPS reset5%, RPM hysteresis1000.
The test changed minimum duty from0% to5%; other tune constants were preserved.

## Code path

- [idle.cpp lines760–786](https://github.com/speeduino/speeduino/blob/202501.6/speeduino/idle.cpp#L760): shared PWM endpoint handling includes hybrid and calls `disableIdle()` at reported zero duty.
- [idle.cpp lines792–810](https://github.com/speeduino/speeduino/blob/202501.6/speeduino/idle.cpp#L792): PWM shutdown handles only pure closed-loop and open-loop, omitting `IAC_ALGORITHM_PWM_OLCL`.
- [Idle ISR](https://github.com/speeduino/speeduino/blob/202501.6/speeduino/idle.cpp#L835): schedules the next compare from current timer count plus PWM target. At a zero target, a missed compare/current-tick race could leave an unintended long output pulse. Actual electrical timing has not been measured.

The log's IAC value is a command, not pin-state or valve-position feedback.
A zero command therefore cannot establish that the physical valve was closed.

## Observations

| Log | Minimum observed duty | Result |
|---|---:|---|
| `2026-10-23_17.15.42` |0%|RPM peaks3859; TPS remains0%|
| `2026-10-23_17.25.31` |0%|Repeat spike3813; intended5% correction was not effective in this run|
| `2026-10-23_17.33.57` |0%|Old-tune run, spike3635; user identifies preceding run as old tune|
| `2026-10-23_17.35.10` |4% after initial stale sample|No spike in inspected~39s continuous segment; user also reports no spike after verifying/burning correction|

First event: MAP30→48kPa at log time733.551s, then65kPa at733.605s,
while RPM remains~1470 and IAC reports0%. RPM then rises through1653/2081/2423
before duty jumps to53% at734.078s. Crossing target+1000RPM resets negative
integral, explaining the later commanded reopening; it does not explain the
initial MAP rise. User explicitly reports no throttle, connector, or TunerStudio
action during this event. TPS remains0%, boost duty0%, sync losses0.

Second event similarly begins MAP30→49→67 while IAC remains0%, followed by RPM
rise and then a duty increase. CurrentTune's intervening TunerStudio save had
restored minimum0, so that run did not test the5% workaround.

Corrected run: exclude first stale sample at272.680s and following gap.
Inspect338.356–377.353s: duty4%, RPM1427–1507, target800, TPS0%, MAP30–31kPa,
coolant194–208F, zero sync losses. No claim of longer spike-free coverage is made.
User reports verifying and burning the corrected setting; full ECU readback and
power-cycle completion were not independently established.

## Workaround and remaining work

Minimum5% avoids the zero endpoint. At500Hz AVR timer resolution it can log4%;
this is expected quantization. It is not a calibrated mechanically closed valve
position. Preserve `TurboExo_closed_loop_idle_min5_PROVISIONAL_2026-10-23_172037.msq`.

High idle remains~1450RPM at this lower limit; investigate valve/output/airflow
separately. Do not increase PID gain to address a controller already at its floor.

For upstream confirmation, reproduce on a bench with a scope/logic analyzer,
compare hybrid zero vs positive duty and pure PWM closed-loop zero, verify the
exact flashed version, and test including hybrid in the PWM shutdown branch.
Do not deliberately reproduce engine rev spikes as the first confirmation test.
No firmware patch or upstream submission was performed. Prior static reviews
validated PID arithmetic but missed this endpoint; their unqualified PASS was
incomplete. The positive-floor result supports but does not prove causation.

## Evidence files

Raw `.mlg` and converted `.csv` files are in `../DataLogs/` under the names above.
Hashes below identify the inspected CSV snapshots; an actively recorded raw log
may continue to grow.

- `2026-10-23_17.15.42.csv` — SHA256 `6aceea12c6639e468e46c9cb6db9c02be1ce682e0407fd44d274db67e1e605bc`

- `2026-10-23_17.25.31.csv` — SHA256 `b30da138833de2fbc1c4665f5c5ca4cb6526b06768008e1d902d4fc21ff65772`

- `2026-10-23_17.33.57.csv` — SHA256 `d8e09d3669bb1582d67213a7e952ee5a91fec85a95b0be38db24407a20b3822f`

- `2026-10-23_17.35.10.csv` — SHA256 `4d2047ac4aacc63eb644a90e32e513c3cf5a3278a8d627e292388f5950555c27`

## Later session context

The final CSV snapshot now contains4929 data rows through804.156s; the hash above
was refreshed for that snapshot. The initial39-second no-spike observation remains
a bounded excerpt. Later high RPM in this file corresponds to user-commanded
neutral revs (TPS up to100%), not evidence of another unexplained spike.
After the documented manual idle-screw adjustment,750–768s shows881–913RPM at
IAC4%; the earlier~1450RPM floor observation predates that adjustment. See the
latest experiment entry for injector saturation and subsequent idle recovery.

### Later saved continuation

The log continued after the running-milestone commit. The current CSV/hash now
identify5237 rows ending1275.359s (last sample902RPM). Earlier4929-row/804.156s
statements describe the preceding captured snapshot; do not interpret timestamp
span as continuous coverage. Original milestone provenance hashes remain attached
to that earlier committed snapshot. No new calibration conclusion is drawn from
this continuation.
