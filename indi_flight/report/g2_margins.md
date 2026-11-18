# G2 stability margins: preliminary (pre-freeze) evidence, reference airframe quad5in

Status: PRELIMINARY. Every number below was flown before the freeze, on binaries that are not the frozen pair, mostly
one or two seeds. G2 is decided only on the frozen pair in stage 6 with `--gate` (GATES.md G2, G1.7). This section
does not state G2 as passed. PID is a reference only; it is never a pass condition (F-5).

Gate thresholds (GATES.md, G2): GM >= 6 dB, PM >= 45 deg, delay margin >= 2 control periods + telemetry latency
(model-only path: + 0), controller rates 800 and 400 Hz pass, 267 Hz reported. Each margin is the worst of 2 runs in the
final test; the preliminary cells below are 1-2 runs. The telemetry latency value is not found in the files read, so the
delay-margin criterion is compared with 2 periods only and flagged where it matters.

Airframe quad5in (5 inch, ~600 g), sim v2 (rotor speed through the eRPM telemetry model) unless a row says model-only.

## 1. Method

**Break points (one per loop).** INDI rate loops (roll, pitch, yaw): M3a, the torque setpoint, with the excitation d
added to the controller output c and u = c + d sent to both the publish and the stored previous setpoint, so every
feedback path (gyro, measured rotor speed, modelled actuator) closes through u (D-G2-BREAK, D-G2-INJ; parameters
`MC_INDI_INJ_*`). PID: M1 (gyro), M2 as cross-check; not flown here. Attitude loop: the rate setpoint (attitude-loop
output), `MC_INDI_INJ_PT 1`, L = -Y/X with y = rates_sp_pre_inject, x = rates_sp_applied (extractor `bench/ratesp_csv.py`;
design `design/attitude_break_s86.md`). INDI acceleration loop: stage output t_c, `MC_INDI_PINJ_PT 1` (D-G2-PINJ-OUT).
Velocity/position loop: stage input a_ref, `MC_INDI_PINJ_PT 0` (D-G2-PINJ). The acceleration break closes every path
through the plant input, so with a matched actuator model the INDI incremental terms cancel and L is dominated by the
outer loops; the INDI-specific part is read above about 3 Hz (README `results/stage5_s84_accbreak`).

**Excitation.** Schroeder multisine on the 1/Tp grid, 10 bins per decade, in hover, NP >= 3 periods with the first
discarded. Rate loop: 1-60 Hz, Tp 7.5-10 s, AMP 0.001 (yaw 0.008). Outer loops: 0.2-8 Hz, Tp 10 s (xy: Tp 20 s, AMP
0.08), NP 5, DLY 20 s, AMP 0.04. Attitude: 0.2-20 Hz, Tp 10, NP 5, ramp 0.06 rad/s per component. Amplitude chosen
in a pre-test where two amplitudes agree within 1 dB / 5 deg (attitude pre-test: 1.0 dB / 3 deg over 0.4-12.6 Hz).

**Estimator and coherence.** `bench/margins_est.py` (`frf_periodic`: period-exact FFT, or least squares on actual
sample times when the time base is non-uniform); bins kept where coherence >= 0.8, >= 0.9 within a decade of crossover.
Rate loop wrapper `bench/m3a_margins_pretest.py` (reads `bench/m3a_csv.py`); outer loops `bench/pinj_csv.py --margins`.
A S85 defect (no constant column in the LS phasor fit, bias for signals with a mean near -g) was fixed; the S84 output
break was re-scored (PM 58.7 -> 61.3 deg); S83 and rate-loop numbers did not change.

**Validity checks.** Per run: no fault, not landed, u = c + d (max error 3e-8 on the attitude cells), logged rate equals
the controller rate, pre-injection gate (RMS of rate, `--delay 4 --length 15`) for rate cells, `hole_report` (sim holes and
controller gaps; evidence limit 1 per run). Outer-loop and attitude cells must be flown one at a time: parallel flights
produced sim holes of 0.10-0.21 % (stage5_s86_g2outer finding 1).

**Second key.** Independent recomputation from the same CSV windows. Found: S41 `second_key_m3a_s41.py` (PM agrees
within 0.09 deg, per-bin criterion DISAGREE at the time; later fixes not re-read); S82 injector code AGREE WITH MINOR;
S84 high-frequency FRF AGREE (`hf_second_key.md`, 0.05 dB / 0.2 deg); attitude extractor keyed T193 AGREE WITH MINOR.
Margins of the S86/S87 outer-loop cells and of the S91/S92 attitude cells: UNKEYED (stated in their READMEs; no key
file found for the S91 margins). Rate-loop S76/S77 flights: single key (FRF script keyed S40).

**Linear-model cross-check.** `bench/margins_models.py` (`L_indi`, `L_att_indi_outer`), `bench/att_model_vs_measured.py`.
Acceptance: PM within 10 deg and GM within 3 dB, or the difference explained in ANOMALIES.md.

## 2. Results per loop

Delay margin in periods is derived (DM / control period) where a period is given; this is arithmetic on the cited
numbers. "nf" = not flown, "nfd" = not found in the files read. GM "none" = no -180 deg crossing in the analysed band.

### 2.1 Rate loop, roll (M3a, INDI)

| configuration | GM dB | PM deg | DM ms (periods) | f_c Hz | model GM / PM | 2nd key | source |
|---|---|---|---|---|---|---|---|
| INDI v2 (meas.) 800 Hz, HEAD dcba400943, bld 0 | 16.2 | 69.1 | 47.1 (37.7) | 4.07 | model PM 66.7 / f_c 4.60 (S78); GM nfd | single key | results/stage3_s77_a34/README.md |
| INDI v2 (meas.) 800 Hz, bld 1.0 | 15.8 | 68.9 | 46.5 (37.2) | 4.12 | as above | single key | results/stage3_s77_a34/README.md |
| INDI v2 (meas.) 800 Hz, S76 bld 1.0 / 0.3 / 0.1 | 15.7 / 16.0 / 16.0 | 68.5 / 68.4 / 68.2 | 45.9 / 45.5 / 43.3 | 4.15 / 4.18 / 4.37 | nfd | single key | results/stage3_s76_bld/README.md |
| INDI v2 (meas.) 800 Hz, S57 (pre da64bc26b3), 2 seeds | 16.6 / 16.3 | 77.5 / 77.0 | 70 / 72 | 3.08 / 2.99 | model PM 76.4 (S78, pre-lead model) | single key | results/stage3_s57/roll_m3a_meas800/README.md |
| INDI v2 (meas.) 400 Hz, HEAD 499e1df991, bld 0 / 1.0 | 13.3 / 13.3 | 70.5 / 70.4 | 50.8 (20.3) | 3.85 | nfd | single key | results/stage3_s77_400/README.md |
| INDI v2 (meas.) 267 Hz | nf | nf | nf | nf | nf | nf | (measured-rotor rows at 400/267 Hz moved to stage 6, route check 57) |
| INDI model-only 800 Hz, S53 (ACT_TC x1.5 plant, old binary) | 11.3 | 85.6 | nfd | nfd | nfd | nfd | results/stage3_s57/roll_m3a_267b/README.md (trend table), not a gate result |
| INDI model-only 400 Hz, S56, 2 seeds (pre-HEAD binary 296766019a) | 10.6 / 10.4 | 84.4 / 84.4 | 58 / 59 (23) | 4.01 / 4.00 | nfd | single key | results/stage3_s57_pre/roll_m3a_400/README.md |
| INDI model-only 267 Hz, S57, 2 seeds (pre-HEAD binary) | 10.2 / 10.0 | 83.2 / 83.6 | 57 / 57 (15) | 4.03 / 4.11 | nfd | single key | results/stage3_s57/roll_m3a_267b/README.md |
| INDI model-only at HEAD, any rate | nf | nf | nf | nf | nf | nf | - |
| PID reference (M1) | nf | nf | nf | nf | nf | nf | JOURNAL (S49): "no measured PID" |

Disagreement flagged (A-34, PARKED S79): the same param file gave PM 77.5 deg / f_c 3.08 Hz at S57 and PM 69.1 / 4.07 Hz
at HEAD. The change is the rate-setpoint lead (da64bc26b3), which raises the mid-frequency gain; the model with the lead
reproduces the shift (PM -9.7 vs -8.4 deg measured). The closing flight at da64bc26b3^ was not done. S57 rows are
therefore not the law to be frozen; the model-only rows are pre-lead and are kept only to show the path difference.
Bound stated in A-34: HEAD passes by 24 deg PM and 10 dB GM.

### 2.2 Rate loop, pitch and yaw (M3a, INDI)

| configuration | GM dB | PM deg | DM ms | f_c Hz | model | 2nd key | source |
|---|---|---|---|---|---|---|---|
| pitch, model-only 800 Hz, S53, 2 seeds (old defaults, old binary) | 11.9 / 12.0 | 86.9 / 86.8 | 61.4 / 61.6 | 3.93 / 3.91 | nfd | nfd | results/stage3_s53/pitch_m3a/README.md (not a gate result) |
| pitch v2 (meas.) any rate | nf | nf | nf | nf | nf | nf | - |
| yaw, model-only 800 Hz, S56/S57, 2 seeds | 18.5 / 18.3 (at 22 Hz, bins 5-40 Hz); 0.1-20 Hz run: none | 88.1 / 88.0 | 196 / 197 | 1.25 / 1.24 | model f_c 1.4 Hz, Ms 1.3 dB vs flown 1.6 dB (S56) | nfd | results/stage3_s56/yaw_m3a/README.md, results/stage3_s57_pre/yaw_m3a_hf/README.md |
| yaw v2 (meas.) 800 / 400 / 267 Hz, model-only 400 / 267 Hz | nf | nf | nf | nf | nf | nf | - |
| PID reference, pitch and yaw | nf | nf | nf | nf | nf | nf | - |

The yaw cells predate several firmware changes (A-34 applies to the setpoint path). Not re-flown at HEAD.

### 2.3 Attitude loop (break at the rate setpoint, INDI v2, outer loops closed)

All cells seed 1, RAMP 0.06, one flight each. Delay margin = PM / (360 f_c) as the README states. Source for every row:
results/stage5_s91_attbreak/README.md. Margins UNKEYED.

| axis, rate | GM dB | PM deg | DM s (periods) | f_c Hz | model PM / GM (with outer factor) | holes |
|---|---|---|---|---|---|---|
| roll 800 Hz | 21.9 | 57.3 | 0.121 (nfd) | 1.319 | 57.6 / 20.3 | PASS (coherence 0.88 at the lowest bins) |
| roll 400 Hz | 22.0 | 56.6 | 0.119 | 1.318 | 56.4 / 18.6 | PASS |
| roll 267 Hz (reported) | 21.8 | 55.5 | 0.113 (30) | 1.364 | 55.3 / 17.2 | FAIL: count-disagree flag only (2 intervals of 6.25 ms, 0 missing); coherence not computed |
| pitch 800 Hz | 21.9 | 58.1 | 0.123 | 1.311 | not modelled separately (identical to roll in model) | PASS |
| pitch 400 Hz | 22.1 | 56.8 | 0.119 | 1.332 | idem | PASS |
| yaw 800 Hz | 33.9 | 73.8 | 0.452 | 0.454 | not modelled | PASS |
| yaw 400 Hz | 34.3 | 73.4 | 0.448 | 0.455 | not modelled | PASS |
| pitch, yaw 267 Hz | nf | nf | nf | nf | nf | - |
| model-only path | nf | nf | nf | nf | nf | - |
| PID reference | nf (model only: roll PM 55.7-58.1 / GM 13.2-14.9 dB at 267-800 Hz, with outer factor, G1 1757) | | | | | |

Limits stated in the README: attitude loop measured with the outer loops closed; roll 267 Hz was flown at 800/3 Hz
(D-RATE267); a 250 Hz flight was rejected by the runner. The pre-test at RAMP 0.03 had a hole_report FAIL (a Docker
pytest ran in parallel) and low coherence at 0.2-0.3 Hz.

### 2.4 INDI acceleration loop (stage output break, PT 1) and velocity/position loop (stage input break, PT 0)

Stage runs at about 89 Hz (S84 README); delay margins are given in seconds, period counts are not derived. GM "none" means
no -180 deg crossing in 0.2-8 Hz; the GM column is then not a margin. Seeds 1 and 2 unless stated.

| loop, axis, rate | GM dB | PM deg | DM s | f_c Hz | model | 2nd key | source |
|---|---|---|---|---|---|---|---|
| vel/pos z (PT 0) 400 Hz, tb 1.0 / 0.33 | none | 57.3 / 59.1 | 0.237 / 0.264 | 0.67 / 0.62 | nfd | injector AGREE WITH MINOR (S82) | results/stage5_s83_velbreak/README.md |
| vel/pos z 400 Hz s1 / s2 | none | 57.3 (re-scored) / 64.5 | nfd / 0.291 | nfd / 0.62 | nfd | UNKEYED | results/stage5_s86_g2outer/README.md |
| vel/pos z 800 Hz s1 / s2 | none | 62.8 / 66.1 | 0.255 / 0.266 | 0.68 / 0.69 | nfd | UNKEYED | results/stage5_s86_g2outer/README.md |
| accel z (PT 1) 400 Hz s1 / s2 | none | 63.7 / 63.0 | 0.262 / 0.269 | 0.68 / 0.65 | nfd | UNKEYED | results/stage5_s86_g2outer/README.md |
| accel z 800 Hz s1 / s2 | none | 63.0 / 59.6 (S88 re-fly of s2; first flight 58.3) | 0.251 / 0.26 | 0.70 / nfd | nfd | UNKEYED | results/stage5_s86_g2outer/README.md |
| accel z, S84 pre-test 400 Hz | none (|L| -11.3 dB at 8 Hz) | 61.3 (re-scored; 58.7 before the S85 fix) | 0.26 (old) | 0.64 (0.62 old) | nfd | UNKEYED | results/stage5_s84_accbreak/README.md |
| accel z, 1.5-10 Hz band (D-GAP HF), 1 flight | > 17 dB bound, no crossing | nfd | nfd | nfd | nfd | AGREE (0.05 dB / 0.2 deg) | results/stage5_s84_accbreak/README.md |
| vel/pos x, y (PT 0), 400 / 800 Hz, 8 cells | 18.2-18.8 | 49.7-61.8 (range of 8 cells, after re-fly 56.6) | 0.427-0.554 | 0.31-0.34 | nfd | UNKEYED | results/stage5_s87_xy/README.md |
| accel x, y (PT 1), 400 / 800 Hz, 8 cells | 18.6-19.3 | 60.9-64.8 | 0.572-0.623 | 0.28-0.30 | nfd | UNKEYED | results/stage5_s87_xy/README.md |
| model-only path, any outer cell | nf | nf | nf | nf | nf | nf | - |
| 267 Hz outer cells | nf | nf | nf | nf | nf | nf | - |
| PID reference, outer loops | nf | nf | nf | nf | nf | nf | - |

Per-cell xy values and the 16-cell table: results/stage5_s87_xy/README.md. Seed spread up to 7 deg at pt0 (s1 54.4 vs s2
61.8 on ax1 r400). The s86 README gives GM "nan" for z: no phase crossing in band, so the z outer cells have no GM
(Ms 1.17-1.20 is reported instead); xy cells do report GM 18-19 dB. Both statements are from the sources and are not
reconciled here (different band edges and AMP/TP).

Source disagreement: the velocity z 400 Hz seed 1 PM is 57.3 deg in S83 and S86 (same flight, re-scored); the S82 pre-test
PM 54.4 deg overlapped the climb and is superseded.

## 3. Linear-model cross-check

Rate loop. `margins_models.L_indi` reproduces the S47 pre-lead measurement (PM 23.6 vs 22.3 deg, GM 4.7 vs 4.1 dB,
S48) and the S57-to-HEAD shift (S78). A-35 (OPEN, parked S79): model |L| is 0.2-1.7 dB high and the model phase leads the
measurement by +17 deg at 1 Hz, falling to -5 deg at 8 Hz, on both S57 and HEAD data; PM within 1.1 deg at crossover.
It touches the model cross-check, not the measured margins, and is flagged "blocking for the G2 freeze" in ANOMALIES.md.
No GM comparison for the measured-path rate cells was found.

Attitude loop (A-36, `results/stage5_s91_attbreak/model_vs_measured.md`). Without the outer loop the model PM was about 15 deg
higher than measured (outside the 10 deg rule; roll 400 Hz: model 71.4 vs measured 56.6). With the closed outer
velocity/position loop in the model (O(s), derived independently from the firmware in T195, `design/t195_att_outer_key.md`)
the PM matches within 0.3 deg at 267, 400 and 800 Hz (dPM +0.2, +0.2, -0.3). The GM residue: model GM 1.6-4.6 dB lower than
measured (dGM +1.6 at 800 Hz, +3.4 at 400 Hz, +4.6 at 267 Hz), i.e. the model is conservative; the 400 and 267 Hz
cells are outside the 3 dB rule. ANOMALIES A-36 records it as open residue, probably the A-35 rate-loop phase error near
the phase crossover (not shown), bounded by measured GM >= 21.8 dB and model GM >= 17.2 dB, accepted as conservative
and bounded in route check 93 (not chased unless a gate verdict depends on it, RC74). Unverified in the source: effective
`MPC_*` values in the flown runs, attitude latency (1 sample at the rate-loop rate in the model, the module runs at the
attitude callback rate), yaw is not modelled. A-35 is linked.

Outer loops. A linear model of the output-break and input-break L is not found; the S86 xy diagnosis only compares |L| at
three bins with the stock MPC_XY gains (predicted 0.60 / 0.29 / 0.14 at 0.5 / 1 / 2 Hz, measured 0.69 / 0.27 / 0.16, UNKEYED).

## 4. Status against the gate (preliminary evidence only)

Meeting the thresholds in the cells flown (GM >= 6 dB where a GM exists, PM >= 45 deg, delay margin well above 2 periods):
rate roll INDI v2 at 800 and 400 Hz (HEAD, one seed); attitude roll/pitch/yaw at 800 and 400 Hz (one seed, UNKEYED);
vel/pos and accel z, x, y at 400 and 800 Hz (PM 49.7-66.1 deg; the lowest, 49.7, is 4.7 deg above the threshold).
Reported: attitude roll 267 Hz (PM 55.5, GM 21.8, hole_report count flag).

Open or missing:
- Rate loop: pitch and yaw at HEAD and on the measured path; model-only path at HEAD (F-1/O-5 fallback); roll 267 Hz
  measured path; all PID reference cells; A-34 closing flight; GM comparison with the model (A-35 blocks the freeze).
- Attitude loop: model-only path, 267 Hz for pitch and yaw, second key of the margins, two-seed repeat (the gate takes the
  worst of 2 runs), yaw model, PID measured reference.
- Outer loops: model-only path, 267 Hz, two-seed worst-of rule applied to the final pair, margins UNKEYED, linear model,
  hole reporter evidence limit 1 (count cross-check and the 89 Hz topic limit were tool defects, fixed S88; all 16 xy cells
  PASS holes after re-fly; the 800 Hz z cells passed after the D-HOLE-EXCESS rule or re-fly).
- Telemetry latency value for the delay-margin threshold: not found.
- Yaw: rate and attitude yaw cells exist only partly (see 2.2, 2.3); no yaw outer-loop cell. Route check 93 states that
  if G2 has no verdict by S96 the owner may narrow G2 to rate + z + xy + attitude and move yaw to stage 6.
- All preliminary: binaries are not the frozen pair, no cell has the provenance of `--gate`. The gate is decided only on the
  frozen pair in stage 6 with `--gate`.

## 5. Reproduction

| item | command |
|---|---|
| rate roll M3a at 800 Hz (S76/S77) | `bash indi_flight/results/stage3_s77_a34/fly.sh`; analysis `bench/m3a_csv.py` + `bench/m3a_margins_pretest.py csv 1 60 10 800` |
| rate roll M3a at 400 Hz | `bash indi_flight/results/stage3_s77_400/fly.sh` (analysis `... 1 60 10 400`) |
| rate model-only 400 / 267 Hz, pitch, yaw | `run_all.sh` in results/stage3_s57_pre/roll_m3a_400, results/stage3_s57/roll_m3a_267b, results/stage3_s53/pitch_m3a, results/stage3_s56/yaw_m3a (old binaries) |
| attitude cells | `bash indi_flight/results/stage5_s91_attbreak/batch.sh` (267 Hz: `batch267.sh`; single cell `fly.sh AX RATE SEED RAMP`) |
| z cells | `results/stage5_s86_g2outer/fly.sh PT AX RATE SEED` (serial only) |
| xy cells | `results/stage5_s87_xy/batch.sh` (`fly.sh PT AX RATE SEED`) |
| accel / vel z pre-tests | commands in results/stage5_s83_velbreak/README.md and results/stage5_s82_velbreak/README.md |
| model cross-check, attitude | `bench/att_model_vs_measured.py` (output model_vs_measured.md) |
| model cross-check, rate | `python3 indi_flight/results/stage3_s78_a34/compare.py`, `table.py` |
| one command per item for the gate run | not yet defined (GATES.md: to be named when the G2 runner exists; route check 93 action 1) |
