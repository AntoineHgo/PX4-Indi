# CAUSE_S189: G5.7 hold-edge attitude jump regression (freeze-6 -> freeze-9)

Note on the metric: g57_check "max attitude jump" = tilt_err = max angle between measured z axis and attitude-setpoint z over
[edge+0.3, edge+1.0] s, i.e. TRACKING error, not a setpoint step. Scorer is blind to setpoint size.

## Per-edge decomposition (script scratchpad dec.py; exc = max angle of setpoint z from its value at edge-0.05 s over +1 s;
## sprate = max setpoint tilt rate deg/s over +1 s; err = scorer tilt_err; lag ~ err/sprate)
| edge | s | INDI f9 exc/sprate/err | INDI f6 exc/sprate/err | PID f9 exc/sprate/err |
|---|---|---|---|---|
| posctl>hold | 1 | 23.9 / 119 / 5.83 | 21.1 / 125 / 2.46 | 20.6 / 89 / 4.50 |
| posctl>hold | 2 | 23.9 / 130 / 5.95 | 21.1 / 123 / 2.78 | 20.3 / 96 / 4.54 |
| posctl>hold | 3 | 24.2 / 120 / 6.05 | 20.7 / 123 / 2.44 | 20.3 / 94 / 4.45 |
| stab>hold | 1 | 6.0 / 423 / 5.70 | 5.4 / 545 / 2.62 | 6.5 / 95 / 4.29 |
| stab>hold | 2 | 5.9 / 130 / 5.43 | 5.9 / 114 / 1.59 | 5.9 / 435 / 4.38 |
| stab>hold | 3 | 6.1 / 483 / 5.51 | 5.7 / 98 / 4.15 | 6.0 / 102 / 4.88 |
| hold>posctl (e6) | 1/2/3 | err 4.79 / 4.11 / 4.26 (exc 13.3-13.7) | err 2.69 / 2.55 / 2.64 (exc 13.1-13.7) | 3.89 / 3.74 / 3.19 |
| hold>posctl (e10) | 1/2/3 | err 4.68 / 5.36 / 5.63 (exc 12.6-13.1) | err 2.48 / 2.41 / 2.76 | 3.79 / 4.04 / 4.52 |
Other failing/near edges at f9: 15>2 (stab>posctl) 5.07 / 9.30 / 6.20 (f6 3.05 / 3.01 / 3.30; PID 2.13/0.81/0.61);
altctl>posctl 1>2 s3 10.66 (PID s3 also 7.50, one-off setpoint step 23 deg, both stacks: sim/pilot artefact, not the regression).

Reading: setpoint excursion grew only +3 deg (21 -> 24 deg, rate unchanged 120-130 deg/s) on posctl>hold; tracking error grew
x2.0-2.4 (2.5 -> 5.9 deg) at equal setpoint rate, i.e. effective lag err/sprate ~20 ms -> ~48 ms. PID f9 ~50 ms. So the
regression is TRACKING (inner path), not a bigger outer-loop excursion. The same error rise appears on stab>hold, hold>posctl.

## Freeze-6 -> freeze-9 changes on the path (src commits after 23acbdef67)
| change | f6 | f9 | param? |
|---|---|---|---|
| horizontal gains (7dd352bae2, own params) | MPC_XY_P 0.95, MPC_XY_VEL_P_ACC 1.8 (stock defaults; params.params sets neither) | MC_INDI_XY_P 1.2 (was 1.9 at f7), MC_INDI_XY_VP 2.4 (was 3.6 at f7) | yes |
| jerk FF only from accel difference (20b4a41b22), body-rate FF offboard only (aa4fd2654a) | n/a | on | no |
| F2 setpoint extrapolation (9dd5f76382), applies in every mode | off | on | no |
| F4 kSetpointLeadTc (d65111154b, src/lib/indi_rate_control) | 0.01 s | 0.03 s | no (constexpr) |
| gz_bridge vibration/eRPM (0f56d56bf1, 10c741af4b, c3cf151420) | sim only | | |
Note: f9 outer gains are HIGHER than f6 (1.2/2.4 vs 0.95/1.8).

## Probes (seed 3, mode_switch10 posctl, f9 firmware 83976c5099, params = g5_freeze_s157 + override; probe_s189/, run.json confirms applied)
Seed-3 reference f9 default (1.2 / 2.4): posctl>hold 6.05, stab>hold 5.51, hold>posctl 4.26 / 5.63, stab>posctl 6.20.
| probe | XY_P / XY_VP | posctl>hold | stab>hold | hold>posctl (e6/e10) | stab>posctl | score |
|---|---|---|---|---|---|---|
| both | 0.95 / 1.8 (f6 values) | 5.76 | 5.34 | 4.78 / 5.31 | 7.31 | FAIL |
| ponly | 0.95 / 2.4 | 5.87 | 5.28 | 4.76 / 5.18 | 1.81 | FAIL (altctl>posctl 10.88 one-off, as f9 s3 10.66) |
| vonly | 1.2 / 1.8 | 5.52 | 6.23 | 3.50 / 3.81 | 9.16 | FAIL |
Setpoint excursion/rate unchanged in all probes (exc 23-24 deg, rate ~120 deg/s). Hold-edge error stays 5.3-6.2 deg
whatever the XY gains: the failure is NOT caused by MC_INDI_XY_P / XY_VP.

## Cause
Tracking lag of the attitude/rate path to the attitude setpoint rose from ~20 ms (f6) to ~48 ms (f9) at equal setpoint
(21-24 deg over 1 s, ~120 deg/s); XY gains ruled out by probes. Remaining non-param candidates: F4 kSetpointLeadTc
0.01 -> 0.03 s (d65111154b), which delays the rate-setpoint derivative lead by 20 ms (fits the +28 ms), and F2 setpoint
extrapolation (9dd5f76382), jerk-FF change (20b4a41b22). Points to D-FREEZE-8 F4 (also the D-XY-PICK/D-FREEZE-9 "F4 revert
probe first" second lever). PID f9 (4.5 deg) sits at the same lag as f9 INDI, so f6 INDI was better than PID by the lead.
Edge stab>posctl also elevated (3.0 -> 5-9 deg) and fails in 2 of 3 f9 seeds, same direction.

## Unverified
- F4 vs F2 vs jerk-FF attribution: needs a firmware build with kSetpointLeadTc 0.01 (not allowed here, no source change).
  Next probe: F4 revert alone, seed 3, then F2 off if still failing. Note F4 was introduced for G4 chatter (89 Hz line,
  limit 5e-4): reverting trades G4 against G5.7; a rate-limited/hold-aware lead is a design question.
- Only seed 3 probed (worst seed; hold-edge errors of s1/s2 equal within 0.3 deg).
- Lag estimate err/sprate is a rough ratio, not an identified delay. 1>2 altctl>posctl s3 outlier (10.7) also in PID (7.5): not part of this cause.
