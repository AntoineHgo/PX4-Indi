# G5.5 gain probe (S176): does 2x horizontal pos/vel gain fix the o1 lemniscate RMS?
Command: `bash indi_flight/results/g55_gain_probe_s176/fly.sh` (freeze fly.sh o1_lemniscate seed 1 command, only `--params`
and `--out` differ; rc=0, 1 flight). Checker: `bench/g55_check.py <run> --json` (analytic reference, truth), host python3.
Params: `params.params` = g5_freeze_s157/params.params (no MPC_XY_* there) + `MPC_XY_P 1.9`, `MPC_XY_VEL_P_ACC 3.6`
(2x firmware defaults 0.95/1.8). Verified in flight.ulg initial_parameters: 1.9 / 3.6 (freeze log: 0.95 / 1.8), MC_INDI_ID_OK 1.
Build: build/px4_sitl_default/bin/px4 is newer than every file under src/ at run time (no rebuild). NOTE the freeze flight
used firmware 23acbdef67; HEAD adds D-JFF-SOURCE/D-JFF-OFFB (jerk FF differenced, rate FF offboard only) in McIndiPosControl,
so the comparison changes gain AND firmware. No gx1 flight on HEAD was flown (one-flight rule).

| o1 seed 1 (scripts: scratchpad an.py) | freeze (gain 1x) | probe (gain 2x, HEAD) |
|---|---|---|
| horizontal RMS (G5.5 <= 0.5) | 0.606 m FAIL | **0.289 m PASS** |
| horizontal max error | 0.900 m | 0.476 m |
| vertical RMS / max | 0.040 / 0.079 m | 0.051 / 0.116 m (PASS <= limit) |
| tilt max (truth) | 41.5 deg | 44.1 deg |
| rate RMS above 2 Hz p/q/r | 3.06/3.41/0.97 deg/s | 3.38/3.63/0.84 deg/s |
| motors (actuator_motors, traj window) | 0.114-0.176, no saturation | 0.111-0.187, none at 0.99 or 0.01 |

Oscillation: truth p,q,r and vx,vy spectra peak at 0.56-0.79 Hz (the lemniscate itself), no line above 2 Hz; the freeze
had a 1.74 Hz p peak, the probe none. Not run: the formal g3_checks window detector (needs --t0/--t1 steady window).
Reading: gain is a strong lever (0.61 -> 0.29 m, margin 0.21 m) with no sign of oscillation or saturation at 2x, tilt
+2.6 deg. Caveat: firmware change confounds; a gx1 flight on HEAD would split the two. Other trajectories (o2-o4, o7) and seeds untested.

## Control flight gx1 (HEAD)
Command: `bash indi_flight/results/g55_gain_probe_s176/fly_gx1.sh` = fly.sh with `--params params_gx1.params` (params.params minus the two
MPC_XY_* lines) and `--out indi_o1_s1_gx1`; rc=0, 1 flight. Build: build/px4_sitl_default/bin/px4 newer than every file under src/ (current with HEAD).
Checker: `bench/g55_check.py <run> --json <run>/g55.json` and `an.py <run>`, both in Docker (output: indi_o1_s1_gx1.check.txt, .an.txt).
Params verified in flight.ulg initial_parameters: MPC_XY_P 0.95, MPC_XY_VEL_P_ACC 1.8, MC_INDI_ID_OK 1.

| o1 seed 1 | freeze (23acbdef67, 1x) | gx1 (HEAD, 1x) | gx2 (HEAD, 2x) |
|---|---|---|---|
| horizontal RMS / max | 0.606 / 0.900 m | 0.587 / 0.920 m (FAIL <= 0.5) | 0.289 / 0.476 m |
| vertical RMS / max | 0.040 / 0.079 m | 0.035 / 0.087 m | 0.051 / 0.116 m |
| tilt max | 41.5 deg | 41.3 deg | 44.1 deg |
| rate RMS >2 Hz p/q/r | 3.06/3.41/0.97 | 3.07/3.77/1.02 | 3.38/3.63/0.84 |
| spectrum line above 2 Hz | 1.74 Hz p peak | no (p peak 1.74 Hz again, below 2 Hz; same as freeze) | no |
| motors | no saturation | 0.111-0.177, no saturation | none |

Reading: HEAD firmware at 1x gain gives 0.587 m vs freeze 0.606 m, so the firmware change is worth about 0.02 m and does not fix the RMS.
The improvement to 0.289 m comes almost entirely from the doubled MPC_XY_P / MPC_XY_VEL_P_ACC gains (single seed, o1 only).

## gx2 on o2-o4, o7 (seed 1)
Flown by a loop equal to fly.sh with `--scenario` swapped (o2_circle_z, o3_lemniscate_gust, o4_lemniscate_payload, o7_lemniscate_tau2),
`--out indi_<oN>_s1_gx2`, same params.params (verified MPC_XY_P 1.9 / MPC_XY_VEL_P_ACC 3.6, MC_INDI_ID_OK 1), HEAD build current
(px4 binary newer than all of src/), 4 flights sequential, all rc=0, no set-up failure, no refly. Scored with `g55_check.py <run> --json <run>/g55.json`
and `an.py <run>` in Docker (output: indi_<oN>_s1_gx2.chk_an.txt). Freeze = g5_freeze_s157 (firmware 23acbdef67, 1x gain); max error not recomputed for freeze.

| scenario | freeze horiz RMS | gx2 horiz RMS | gx2 max err | gx2 vert RMS | tilt max | line > 2 Hz | motors min-max |
|---|---|---|---|---|---|---|---|
| o2_circle_z | 0.794 m FAIL | **0.268 m PASS** | 0.362 m | 0.088 m | 34.1 deg | no (p/q peak 0.50 Hz) | 0.122-0.171 |
| o3_lemniscate_gust | 0.622 m FAIL | **0.315 m PASS** | 0.525 m | 0.074 m | 43.9 deg | no (peaks 0.56-0.67 Hz) | 0.110-0.191 |
| o4_lemniscate_payload | 0.582 m FAIL | **0.282 m PASS** | 0.466 m | 0.054 m | 37.6 deg | yes, weak (p 2.30 Hz, q 3.09 Hz; rms>2 Hz p/q 4.6/5.0 deg/s) | 0.136-0.213 |
| o7_lemniscate_tau2 | 0.591 m FAIL | **0.288 m PASS** | 0.467 m | 0.073 m | 43.8 deg | yes, weak (p 2.41 Hz; rms>2 Hz p/q 3.8/3.3 deg/s) | 0.109-0.190 |

Reading: doubled XY gains bring all four rows to 0.27-0.32 m (limit 0.5), vertical RMS stays <= 0.09 m, no motor saturation (max 0.213, min 0.109).
Caveat: o4/o7 show a spectral peak above 2 Hz (rate rms >2 Hz 3-5 deg/s, comparable to the 3-4 deg/s of o1 gx2 and the freeze), no sign of growth; seed 1 only, firmware differs from freeze.
