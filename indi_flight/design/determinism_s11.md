# Determinism check, session 11 (gate G1.6, anomalies A-2 / A-7)

**Command** (3 runs, sequential, foreground; i = 1..3):
`indi_project/docker/run.sh -n det_s11_r$i -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller pid_default --model quad5in --seed 1 --speed 1 --out indi_flight/results/det_s11/r$i > indi_flight/results/det_s11_r$i_stdout.log 2>&1`

**Status**: all 3 flights completed. Exit code 0, `run.json` `exit_status` "ok", `error` null, `flight.ulg` present. No stray `det_s11*` / `pretest*` containers were running at start.
**Wall time** (`run.json` `wall_time_s`): r1 84.2 s, r2 86.5 s, r3 85.5 s. Reference r0 83.1 s.
**Reference**: r0 = `indi_flight/results/pretest_logging_s10`.
**metrics.json**: not written by `run_scenario.py`. Produced by `indi_flight/bench/metrics.py <flight.ulg>`, which I ran for r1..r3. Re-running it on r0 into the scratchpad reproduced the existing r0 `metrics.json` byte for byte.
**Comparison script**: `/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/169f0c68-9559-4531-8dd3-639c3d6d7e1a/scratchpad/compare_det.py`

**Reference caveat**: r0 `run.json` has `git.commit` 361fdbf0 with `dirty: true`. r1..r3 have b8d60a5c with `dirty: false`. r0 is therefore not from the same code state. The clean run-to-run spread is the r1..r3 figure below.

**Leaves**: 33 numeric leaves in `metrics.json`. 8 are identical across all four runs (seed, speed, `effort.n_motors`, saturation fractions, allocator fractions at 0). 19 of 33 exceed 2 % spread over r0..r3.

**15 largest relative spread (r0..r3)**
| leaf | rel. spread |
|---|---|
| position.ref_ned.1 | 2072 % (mean ~0; ill-conditioned, abs spread 4.6 cm) |
| position.ref_ned.0 | 345 % (mean ~0; ill-conditioned, abs spread 4.6 cm) |
| attitude_tracking.roll_rms_deg | 43.4 % |
| position.max_dev_3d_m | 34.2 % |
| position.max_dev_vertical_m | 32.4 % |
| position.max_dev_horizontal_m | 32.4 % |
| position.rms_vertical_m | 28.5 % |
| attitude_tracking.rotation_angle_rms_deg | 24.3 % |
| attitude_tracking.yaw_rms_deg | 20.1 % |
| position.rms_3d_m | 17.2 % |
| attitude_tracking.pitch_rms_deg | 16.2 % |
| position.rms_horizontal_m | 14.8 % |
| window.start_s | 9.3 % |
| rate_tracking.roll_rms_rad_s | 8.1 % |
| window.offboard_span_s.0 | 7.4 % |

**Main groups** (r0..r3 / r1..r3 only, relative spread)
- rate_tracking: roll 8.1 / 8.1 %, pitch 3.6 / 1.5 %, yaw 2.4 / 2.4 %
- attitude_tracking: rotation_angle 24.3 / 23.8 %, roll 43.4 / 37.4 %, pitch 16.2 / 14.6 %, yaw 20.1 / 19.6 %
- position: rms_3d 17.2 / 5.9 %, rms_horizontal 14.8 / 6.6 %, rms_vertical 28.5 / 14.7 %, max_dev_3d 34.2 / 13.1 %
- effort: motor_rate_rms 2.0 / 2.0 %, motor_spread 1.4 / 1.4 %, motor_mean 0.01 / 0.01 %

**Timing confound**: `window.start_s` ranges 33.30 to 36.57 s. The metrics window follows the hold event, so each run measures a different time slice. `run.json` `t_arm_us` is 15.30, 15.37, 17.57, 17.54 s (r0..r3). `t_offboard_us` is 30.30, 31.37, 33.57, 32.54 s. Within r1..r3 the arm time spread is 2.2 s with an identical seed.

**Hold state** (`run.json`): `hold_pos_ned` N spread 4.6 cm, E spread 4.6 cm, D spread 5.0 cm across r0..r3. `hold_yaw_rad` spread 0.0081 rad (0.46 deg).

**Warnings**: `metrics.json` `warnings` = [] in all four runs. `steps` = [] in all four. r1 `gz.log` has 4 SDF warnings (`gz_frame_id` not defined in SDF on the sensors). These are not in metrics.

**Abnormal**: none found. No crash, no missing file in the three new run directories, no non-zero exit. `det_s11_r1_stdout.log` is empty (0 lines). I did not check the r2/r3 stdout logs for content.

**Not verified**: whether the r0 vs rN differences come from the code-state change (dirty tree in r0) or from run noise. Run-to-run noise on the same commit is only measured over three runs (r1..r3).
