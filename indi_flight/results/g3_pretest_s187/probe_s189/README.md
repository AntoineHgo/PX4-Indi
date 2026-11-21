# S189 probe (param-only)

## Task 1 (run_016 ulog, 40-50 s, line 6.84 Hz; ad-hoc script, inline)
- Line is HORIZONTAL: indi_pos_status a_f[0]/a_f[1] 0.256/0.246 m/s2, t_c[0]/[1] 0.31/0.31; vertical a_f[2] 0.0016, t_c[2] 0.0016, thrust setpoint z 2e-5 (collective quiet). vehicle_thrust_setpoint x/y = 0.
- Ground truth (vehicle_local_position_groundtruth) ax/ay 0.40/0.35 m/s2 at 6.84 Hz (vx 9 mm/s): the horizontal acceleration is REAL in the sim, not a filter artefact. sensor_accel/vehicle_acceleration body x/y show only 0.0012-0.0025 m/s2 at the line (expected: accel does not sense horizontal acceleration with thrust along body z), so a_f must come from the model (thrust vector x attitude, mean_u) not from the accelerometer.
- Plant draw run_016: tau_up 0.50 / tau_down 0.84, dly act 3 ms / imu 3 ms, GNSS latency 203 ms (ekf delay 240), G1 mult R/P/Y 0.80/1.13/1.21, inertia 1.19/0.97/0.92, mass x1.16, mode stabilized, no fault/wind.

## Probe 1: MC_INDI_POS_LPF 10 -> 5 (params_lpf5.params = freeze params with only that line changed), run 16 draw (seed 173 n 300 idx 16), out indi_flight/results/g3_pretest_s187/probe_s189/lpf5
Why: line is horizontal, in the a_f -> t_c -> q_d path; the only filter in that path with a param is POS_LPF (acceleration and thrust filter cut-off). Z params irrelevant (vertical quiet).

### Probe 1 result (run 16 draw, LPF 5): key-1 g3_checks pass=True; item 2 p,q sustained=false, no lines (orig: sustained, p line 7.25 Hz, rms 5.8 dps; q 6.75 Hz, 5.1 dps). Max flagged-window rms now p 3.3 / q 3.0 dps (below the detector line threshold). Flight is a new sim realisation (same draw/seed, nondeterministic gz), window 63.0-66.0 vs 62.55-65.55.

## Probe 2: same override (POS_LPF 5), run 10 draw (out $P/lpf5/run_010; scores SCORE_KEY1_lpf5.txt, per-run g3_checks.json)
Result: key-1 pass=True, item 2 p,q not sustained, no lines (orig: p,q line 5.5 Hz sustained, 12 windows, flagged rms 6.8-6.9 dps; now max flagged-window rms 4.8-4.95 dps, 0 flagged windows).

## Summary table (item 2, key 1, same scorer)
| run | orig | LPF 5 | plain FFT peak p/q, 30-60 s (dps @ Hz) orig -> LPF5 |
|---|---|---|---|
| 16 | FAIL, p 7.25 Hz 6.0 dps rms, q 6.75 Hz 5.3 | PASS, no sustained line | 3.4/2.9 @6.8 -> 2.2/1.9 @6.8 |
| 10 | FAIL, p,q 5.5 Hz 6.8-6.9 dps | PASS, no sustained line | 4.4/4.5 @5.3 -> 3.2/3.3 @5.3 |

## Caveats / unverified
- The line is NOT gone: same frequency remains in the spectrum, amplitude down only ~30 % (plain FFT) / ~45 % (detector rms); the detector no longer flags it because it falls under its threshold (5 dps rms-class). Reads as a reduction of loop gain at 5-7 Hz, not removal of the cause.
- n=1 flight per probe, different sim realisation than the originals (no seed-identical replay; windows shifted ~0.4 s); noise in pass/fail near the threshold is not quantified.
- Source of the real 0.35-0.4 m/s2 horizontal acceleration at 7 Hz (ground truth) still unverified (CoM/rotor line offset in sim vs. true vehicle response to q_d); a_f derivation (modelled-acceleration mode, McIndiPosControl.cpp stage) not traced.
- Other runs (000, 005, 017 position-mode 2.5-4.5 Hz) not probed; LPF 5 adds lag to the position/thrust path, side effects on tracking items (item 1/other checks, position-mode runs) not tested.
- Docker containers used: px4-indi g3p189_16, g3p189_10, g3score (all exited by script). No commit, no firmware change.
