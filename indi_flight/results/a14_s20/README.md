# A-14 : EKF vs ground-truth altitude offset during take-off (PID hover, seed 1)

Status: done (runs and check complete; not committed).

## Runs

| Run | Container | Out dir | Status |
|-----|-----------|---------|--------|
| original | (pre-existing) | indi_flight/results/a12_fix_s18/pretest_truth_topics/hover/ | reference, exit not re-run |
| r1 | a14_r1 | indi_flight/results/a14_s20/r1 | ok (exit 0, about 40 s) |
| r2 | a14_r2 | indi_flight/results/a14_s20/r2 | ok (exit 0, about 40 s) |

Command: `indi_project/docker/run.sh -n a14_rN -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller pid_default --model quad5in --seed 1 --speed 4 --rate-hz 800 --out indi_flight/results/a14_s20/rN`

Check script: `indi_flight/bench/a14_check.py` (pyulog + numpy, Agg plots).
Table file: `indi_flight/results/a14_s20/a14_table.md`.
Plots: `indi_flight/results/a14_s20/a14_orig_pretest_s18_arm_window.png`, `a14_r1_arm_window.png`, `a14_r2_arm_window.png` (z_ekf, z_true, baro-derived z over arm-5 s .. arm+20 s, plus residual panel).

Conventions: "arm" = first vehicle_status sample with arming_state == 2. All z values are NED down [m]. Hover window taken relative to arm (arm+55 .. arm+85 s). Each log starts at arm (first log sample = arm time), so there is no pre-arm data in these files.

## Table

| metric | orig_pretest_s18 | r1 | r2 |
|---|---|---|---|
| arm time (log s) | 30.01 | 30.02 | 30.01 |
| max abs(z_ekf - z_true), arm..arm+20 s [m] | 2.218 | 2.283 | 0.199 |
| time of that max, rel. arm [s] | +1.18 | +1.47 | +7.05 |
| signed residual at that max [m] | -2.218 | -2.283 | -0.199 |
| max abs residual, arm..arm+8 s [m] | 2.218 | 2.283 | 0.199 |
| z_ekf at arm [m, NED down] | -2.200 | -2.277 | -0.009 |
| z_true at arm [m, NED down] | +0.005 | +0.005 | +0.005 |
| z_reset_counter at arm | 2 | 2 | 2 |
| z_reset_counter changes in log | none | none | none |
| delta_z events, arm..arm+20 s | value at arm -488.040 m; 0 value changes in window | value at arm -488.017 m; 0 value changes in window | value at arm -488.022 m; 0 value changes in window |
| baro_alt_meter change, arm..arm+20 s [m, up] | +7.746 | +7.585 | +5.408 |
| truth altitude change, arm..arm+20 s [m, up] | +7.205 | +7.227 | +4.969 |
| EKF altitude change, arm..arm+20 s [m, up] | +5.032 | +5.003 | +5.002 |
| baro change minus truth change [m] | +0.541 | +0.358 | +0.439 |
| residual arm+55..arm+85 s: max abs [m] | 0.089 | 0.072 | 0.072 |
| residual arm+55..arm+85 s: mean [m] | +0.039 | -0.010 | -0.013 |
| residual arm+55..arm+85 s: rms [m] | 0.056 | 0.037 | 0.041 |

Extra residual by window (mean, from ad-hoc check, same interpolation):

| window rel. arm [s] | orig | r1 | r2 |
|---|---|---|---|
| [-5, 0) (1 EKF sample at arm) | -2.205 | -2.282 | -0.014 |
| [0, 1) | -2.212 | -2.279 | -0.006 |
| [1, 4) | -1.794 | -1.886 | -0.020 |
| [4, 8) | -0.649 | -0.705 | -0.152 |
| [8, 12) | -0.172 | -0.241 | -0.082 |
| [12, 20) | -0.048 | -0.072 | -0.032 |
| [20, 40) | -0.002 | -0.050 | -0.045 |

Other facts: `xy_reset_counter` ends at 4 (orig), 3 (r1), 4 (r2); `z_reset_counter` is 2 for the whole log in all three. `ref_alt` is 488.04 / 488.02 / 488.02 m. Truth z minimum over the log: -7.26 (orig), -7.29 (r1), -4.99 (r2) m.

Note on the script: the first version counted non-zero `delta_z` samples (1778 in window) which is misleading, because `delta_z` stays at about -488 m for the whole log. The metric was changed to count value changes (0 in window for all three); the table above reflects the corrected version.

## Interpretation

1. Not repeatable at seed 1: the original and r1 both show an EKF-minus-truth offset of about -2.2 to -2.3 m at the first logged sample (arm), decaying to under 0.1 m by about +12 to +20 s; r2 never exceeds -0.20 m (max at +7 s). Reruns with the same seed also produce different truth trajectories (truth minimum z -7.26 / -7.29 / -4.99 m), so the seed alone does not reproduce a flight.
2. Not a z reset at arm: `z_reset_counter` is 2 throughout every log and `delta_z` has no value change in the arm..arm+20 s window (it sits at a constant about -488 m, matching `ref_alt`). The logs begin at arm, so the EKF state before arm is not in these files: the offset is already present at the first sample, and whether it was created at arm or earlier cannot be decided from them.
3. Not a baro step: the baro-derived altitude shows no step at arm (about 0 m in the plot), and over 20 s the baro change minus truth change is +0.36 to +0.54 m in all three runs, far from a 2.2 m effect. The 20 s EKF altitude change is about 5.0 m in all three, against truth 7.2 m (orig, r1) and 5.0 m (r2); the difference comes from the initial offset. The accelerometer path was not analysed here (no IMU topics were checked), so an accelerometer effect is untested.
4. Take-off transient: in orig and r1 the offset relaxes during the climb (about -2.2 m flat for 2 s, then a bump toward -1.1 m near +4 s, then close to -0.1 m by +10 to +12 s), which fits an EKF z-state that is corrected as the vehicle climbs; this is a transient in form, but the data do not separate a bias present before arm from an arm-time transient.
5. Flags, not resolved: (a) the anomaly's "< 0.025 m in hover" is not reproduced by these files: the 55-85 s residual max abs is 0.07-0.09 m (rms 0.04-0.06 m); I read 55-85 s as relative to arm, and if it meant log time the window would be arm+25..arm+55 s, which I did not compute; (b) the baro-derived z is noisy (about +/-0.3 m scatter) so its use as a reference is only approximate; (c) n=2 reruns is too few to estimate a rate of occurrence.
