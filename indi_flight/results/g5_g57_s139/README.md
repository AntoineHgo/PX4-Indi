# S139 G5.7 mode_switch10 and G5.3 hold probes

Definition: `indi_flight/GATES.md` 5b "G5.7 exact test (S139 ...)" and the Hold part of "G5.3 exact test (S139 ...)". No threshold or window changed.
Config: `params.params` (copy of g5_g52_s138: identified-gain INDI, K_Y 20), `--stick-mode posctl --sim v2 --speed 4`, seeds 1-3, `run_batch.sh`
(serial, `timeout 600`, docker stop filtered to `px4-indi-g5g57` only: another session ran `px4-indi-g55offb1` at the same time).

## Built
- `bench/run_scenario.py`: scenario key `seg_modes` {segment: mode}; at the segment start the runner sends MAV_CMD_DO_SET_MODE (`SEG_MODE_CUSTOM`:
  altctl 2/0, posctl 3/0, stabilized 7/0, hold = AUTO_LOITER main 4 sub 3) and writes `run.json["mode_switches"]` (segment, mode, t_cmd_us, t_done_us, ack).
  Scenario key `seg_sticks` {segment: (mode, pitch)} gives the sticks (`stick_profile.seg_sample`: pitch stick for 3 m/s = G5.2 value, else centred).
  No key = old behaviour. The re-send logic `main_mode != STICK_MAIN_MODE` exists only in the --stick-pilot path (not used here); the startup wait is before the scenario.
- `bench/scenarios.py`: `mode_switch10` (settle 3, p0 4, e1..e10 2.0 each, end 3), `hold_wind` (settle 3 posctl, hsettle 2 hold, dist 28 hold, tail 1; gust_x onset = start of `dist`
  = 2 s after the hold switch; 13 s ramp/hold/gust fit, the 15 s tail fits too, 28 s). Wind via `hold_wind_overrides.json` {steady 5, peak 8, dir_deg 0}.
- `bench/stick_profile.py`: `seg_sample`. `bench/g57_check.py`, `bench/g53_hold_check.py` (json per run: `g57_check.json`, `g53_hold_check.json`),
  self-test `bench/tests/test_g57_check.py` (5 tests incl. failing cases: thrust step 30 %, tilt 8 deg, slow speed, wrong states, hold RMS 0.4, nav leaves 4).
  Break-checks done: tilt limit 5 -> 50 and RMS -> mean both make the test fail; code restored, test passes.
- Truth = vehicle_local_position_groundtruth / vehicle_attitude_groundtruth, thrust = -vehicle_thrust_setpoint.xyz[2], setpoint = vehicle_attitude_setpoint q_d.
  Time per topic: timestamp_sample if present and non-zero, else timestamp (vehicle_status has only timestamp, nav edges use it). Hover = mean collective settle+1..settle+3 s.

## Pre-test findings (seed 1, then seeds 2, 3)
- Switches happened with the commanded nav_states: ack true for all 10 (and the hold one); edges ALTCTL 1, POSCTL 2, STAB 15, POSCTL 2, LOITER 4, POSCTL 2, ALTCTL 1, STAB 15, LOITER 4, POSCTL 2.
  Set-up fault fixed in the checker: stabilized is nav_state 15 (7 is the custom main mode), first checker run had 7.
- hold_wind: switch to hold at 58.29 s, wind onset 60.27 s (edge to wind 1.98 s), disturbance.csv force 0.18 N steady, 0.46 N peak, fy ~0: wind applied.
- COM_RC_OVERRIDE is NOT in the log's initial parameters (None) in this build, so it could not be read; in hold the sticks are centred (raw 500, x 0) and
  nav_state stayed 4 for the whole 28 s window in all three runs, so no kick-back occurred. UNVERIFIED which value it has.
- **mode_switch10 cannot reach the validity rule as written.** Truth speed at the 10 edges (same in all seeds): 2.4, 1.0, 2.3, 1.0, 2.2, 0.1, 1.9, 0.8, 0.3, 0.0 m/s.
  Only the 4 edges that leave a posctl segment are >= 1.5 m/s (2 s of centred sticks in A / S / H bleeds the speed: A 2.3 -> 1.0, H 2.2 -> 0.1, S -> 1.0);
  the rule needs >= 8 of 10. This is a property of the stated sequence (centred sticks in A, S, H, 2 s apart), not a set-up fault, so I did not alter sticks, durations or the rule.
  All three runs are INVALID by the rule. Per-edge numbers below are reported anyway.

## Results (gated numbers)
G5.3 hold (RMS <= 0.3 m over 28 s from wind start, nav 4 throughout, reference = mean truth over 1.0 s before wind):
| run | hold RMS m | max m | nav states | verdict |
|---|---|---|---|---|
| hold_wind_s1 | 0.036 | 0.062 | [4] | PASS |
| hold_wind_s2 | 0.052 | 0.086 | [4] | PASS |
| hold_wind_s3 | 0.048 | 0.080 | [4] | PASS |

G5.7 (all runs: 10 edges, states as commanded, 4 of 10 at speed >= 1.5 -> INVALID, no LOC, hover collective 0.137; per edge thrust step in % of hover, tilt error deg over [e+0.3, e+1.0], limits 20 % / 5 deg):
| edge (from>to nav_state) | speed m/s | thrust % s1 / s2 / s3 | tilt err deg s1 / s2 / s3 | rise peak err s1 deg |
|---|---|---|---|---|
| e1 P>A (2>1) | 2.4 | 1.0 / 0.9 / 0.8 | 0.36 / 0.32 / 0.47 | 8.7 |
| e2 A>P (1>2) | 1.0 | 0.3 / 0.4 / 0.4 | 1.45 / 1.79 / 1.46 | 8.4 |
| e3 P>S (2>15) | 2.3 | 0.0 / 0.3 / 0.5 | 0.24 / 0.32 / 0.39 | 8.6 |
| e4 S>P (15>2) | 1.0 | 3.0 / 3.0 / 3.1 | 4.35 / 4.99 / 4.29 | 16.3 |
| e5 P>H (2>4) | 2.2 | 0.3 / 0.3 / 0.4 | 4.65 / 4.79 / 4.77 | 4.0 |
| e6 H>P (4>2) | 0.1 | 0.0 / 0.3 / 0.1 | 4.44 / 3.86 / 5.17 FAIL | 7.7 |
| e7 P>A (2>1) | 1.9 | 1.1 / 1.0 / 0.9 | 0.22 / 0.30 / 0.36 | 8.6 |
| e8 A>S (1>15) | 0.8 | 0.6 / 0.5 / 0.4 | 0.09 / 0.06 / 0.10 | 0.1 |
| e9 S>H (15>4) | 0.3 | 1.4 / 1.2 / 1.4 | 2.99 / 2.96 / 2.96 | 3.8 |
| e10 H>P (4>2) | 0.0 | 0.3 / 0.3 / 0.2 | 4.97 / 5.24 FAIL / 5.25 FAIL | 8.1 |
Thrust step <= 3.1 % everywhere (limit 20 %). Tilt error would fail at e6 (s3) and e10 (s2, s3), borderline 4.3-5.0 at H edges, if the runs were valid; they are not. Verdicts: s1, s2, s3 INVALID.
Summaries: `g57_summary.txt`, `g53_hold_summary.txt`; per-run json in each run dir. Raw logs, ulg and gz files are untracked.

## UNVERIFIED / open
- COM_RC_OVERRIDE value (not in the logged parameters). G5.3 mission part (`auto_tour`) is not part of this probe.
- G5.7: the validity rule (>= 8 of 10 edges at >= 1.5 m/s) is unreachable with centred sticks and 2 s segments; owner decision needed (keep INVALID, or amend the test, e.g. pitch stick held in A/S, or longer P segments) before it is a gate result.
- The tilt measure uses the logged vehicle_attitude_setpoint, interpolated linearly in z-axis vector; second key at the freeze not done.

## S139 re-score and lag comparison
Tool: `bench/g57_check.py --validity leaveP` (default rule unchanged; json `g57_check_leaveP.json` per run; self-test `test_validity_leaveP`, all tests pass). Validity = states ok and truth speed >= 1.5 m/s at the 4 edges leaving posctl (e1 P>A, e3 P>S, e5 P>H, e7 P>A: 2.4, 2.3, ... m/s); thrust (20 % hover) and tilt (5 deg over [e+0.3, e+1.0]) stay gated on all 10 edges.
Verdicts under leaveP: s1 PASS (max H>P tilt 4.97), s2 FAIL (tilt 5.24 at e10), s3 FAIL (tilt 5.17 e6, 5.25 e10). Thrust step <= 3.1 % everywhere; no LOC. Rule leaveP accepted by the owner (Q7 answer A, 2026-11-20; GATES 5b G5.7 AMENDED S140): these are the official probe verdicts, G5.7 FAIL 2/3 seeds.

Lag comparison, same measure (`bench/g57_lag_compare.py`; err = max angle truth body z vs attitude setpoint over [e+0.3, e+1.0], peak = max over [e, e+0.3), rate = max attitude-setpoint tilt rate over [e, e+1.0]):
| edge | err deg | peak0.3 deg | sp rate deg/s |
|---|---|---|---|
| g57 e6 H>P s1/s2/s3 | 4.44 / 3.86 / 5.17 | 7.74 / 7.87 / 7.63 | 124 / 114 / 113 |
| g57 e10 H>P s1/s2/s3 | 4.97 / 5.24 / 5.25 | 8.11 / 8.19 / 8.27 | 116 / 115 / 129 |
| g52 posctl x-step s1/s2/s3 (no switch) | 0.95 / 0.84 / 1.07 | 7.06 / 7.07 / 7.05 | 127 / 114 / 119 |
Reading: the first-0.3 s peak (7-8 deg) and setpoint tilt rate (about 115-130 deg/s) are the same with and without the switch, so the initial lag to the stick step is normal attitude-loop lag. The residual in [0.3, 1.0] s is 4-5 deg after H>P but about 1 deg for the same stick step in posctl, so the persistent part is specific to the switch (not explained by lag alone). Cause not identified; candidates not tested here: velocity/position setpoint re-initialisation on H>P, or different setpoint evolution after the switch.
