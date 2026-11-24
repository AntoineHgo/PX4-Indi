# Falsifier probes S222 on draw 264 `joint` (saturation 0.351 + weak motor 3 at 0.709, rest nominal)

Same draw, seeds, speed 1, gate binary 903eae63, samples `../samples_joint` as the INDI joint run (`../indi_joint/`). Argv identical to it except the output paths (verified by comparing `g3_draw.json` commands). The only change is one line in the params file, passed with `G3_PARAMS=<file>` to `indi_flight/bench/g3_chain.sh start <dir> 24 24 --samples ../samples_joint --speed 1 --allow-binary 903eae63...` (`p1.params`, `p2.params` = `g5_freeze_s157/params.params` with that one line edited; start output in `p*_chain_start.txt`). One flight each, no retries. Raw .ulg untracked.

| | joint (original) | P1 `MC_INDI_ACT_BLD` 0.15 | P2 `MC_INDI_W_MAX` 0 |
|---|---|---|---|
| param in log (initial_parameters) | ACT_BLD 1.0, W_MAX 2700 | ACT_BLD 0.15, W_MAX 2700 | ACT_BLD 1.0, W_MAX 0 |
| fault t [s] (tilt.py) | 58.23 | 58.82 | 58.86 |
| max tilt after fault [deg] | 86.7 | 53.5 (at 61.19) | 45.3 (at 66.22) |
| LOC (tilt > 60 deg for 0.5 s) | yes | no | no |
| outcome / G3 keys | LOC | ok, key1/key2 FAIL (item2) | ok, key1/key2 FAIL (item2) |
| measured torque in use, 1 s after fault | 1.00 | 1.00 | 0.00 |

P2 switch: `MC_INDI_W_MAX` (rotor speed at full thrust). Yaml: "Zero disables the measured torque, INDI then uses its actuator model"; with it 0 the log shows `measured_torque_in_use` = 0 throughout the 1 s after the fault, so the rate loop runs on the modelled actuator state only (ACT_BLD and ERPM_* are documented as only used when W_MAX is set).

## 1 s after the fault (`../scripts/post_fault_err.py`, new small script; rate error = setpoint - gyro, torque error = torque_sp - torque_filtered, means over indi_rate_status samples)

| | roll rate err mean / mean abs [rad/s] | pitch rate err mean / mean abs | roll torque err mean / abs | pitch torque err mean / abs |
|---|---|---|---|---|
| joint | -2.74 / 2.80 | -2.40 / 3.29 | -0.0343 / 0.0362 | -0.0323 / 0.0419 |
| P1 | -1.29 / 1.31 | -1.22 / 1.82 | -0.0146 / 0.0160 | -0.0139 / 0.0215 |
| P2 | -0.24 / 0.68 | -0.28 / 0.88 | -0.0026 / 0.0113 | -0.0024 / 0.0134 |

Caveats: the original joint window already contains the divergence (its 1 s window, fault 58.23, ends near the 86.7 deg tilt), so its errors are partly a consequence of the LOC, not only a cause. Fault times differ by 0.6 s between joint and the probes (cause not checked, as in ../README.md). Single flights, no repeat, so flight-to-flight variation is unknown. Neither probe passes G3 keys (item2 fails); only the LOC question was tested.

## PID joint scored (S222)

Rescore of `pid_joint/run_024` (PID reference, draw 264 joint, no flight) with `g3_chain.sh rescore`; `chain_range` copied from p1_bld015. Key 1: FAIL (item2 only; item1 pass, item3 pass). Key 2: pass (all items pass; chatter False is not G3). Item 2 key 1, max_ratio / rms_at_max_ratio / max_rms_ratio_flagged, sustained: p 5.8e6 / 2.44 / 11.2 no; q 1.3e7 / 2.59 / 22.0 yes (2.0 Hz line from 21 s, 3 windows); r 3.4e5 / 0.65 / 6.0 no. p1_bld015 key 1 (item2 FAIL): p 6.0e7 / 14.5 / 15.5 yes (2.0 Hz line from 23 s, 3 windows); q 1.5e6 / 7.7 / 28.8 no; r 5.6e7 / 13.2 / 14.1 no. p2_nomeas key 1 (item2 FAIL): p 5.4e7 / 11.8 / 24.3 yes (2.0 Hz line from 29 s, 3 windows); q 4.4e7 / 11.0 / 32.2 yes (2.0 Hz lines from 22 s and 29 s); r 9.9e6 / 2.6 / 5.7 no. Key 2 item2: pass on PID, FAIL on p1 and p2.
