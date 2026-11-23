# G3 C212 chain idx 22 (source draw 262): speed-1 re-fly, INDI and PID (S213)

Rule: GATES.md speed-1 rule (S208 / S211b). The chain C212 (speed 4) halted on run_022 (item 2 FAIL on both keys, plus item 3).
Method copied from `../../g3_refly_s199/`: one single-index chain dir per stack.

## What was run (repo root)
- INDI s1: `bash indi_flight/bench/g3_chain.sh start indi_flight/results/g3_refly_actc_s212/speed1_s213/indi_022 22 22 --samples indi_flight/results/g3_refly_actc_s212/samples --speed 1`
  (same samples dir, same params pin chain_params = g5_freeze_s157/params.params, same binary d220e19315c2; no --halt-on-fail). Start log `chain_start_022.txt`.
- PID s1: `python3 indi_flight/results/g3_refly_actc_s212/speed1_s213/fly_pid_run.py 22` (S199 `fly_pid_run.py` with the draw taken from this
  chain's samples via `g3_sample.load_samples(samples, 173, 300)`; base params `g3_pretest_s187/pid_refs/pid_base.params`, controller pid_default),
  then `g3_score_docker.sh pid_022` (key 1) and `g3_checks_key2.py` with the key-1 args (key 2), as in S199. Dry run beforehand.
- Draw check: draw of indi_022/run_022 and pid_022/run_022 == `../run_022/g3_draw.json` draw (equal, incl. `actc`); g3_params.txt and
  g3_scenario_overrides.json of indi_022 identical to `../run_022` (MC_INDI_ACT_TC 0.059881 in all; PID ignores it). The PID script also asserts argv
  equality (except controller/speed) against the speed-4 run and the speed-1 INDI run: both True. Only `--speed` differs (4 vs 1).
- Both flights ran once, no infra aborts, no retry. C212 files untouched (CHAIN_HALTED / HALT_ON_FAIL.json kept).

## Result (idx 022 / draw 262, C3 corner, position mode, wind, saturation)
Item 2 cells: axis, line Hz, RMS dps of the failing detector line. Key 1 value = `max_rms_ratio_flagged` of the axis (the field
that matches key 2 `max_rms_dps` in size; `rms_at_max_ratio` is ~2 dps there and was not used). Where nothing is sustained the
largest flagged-window value is given in brackets.

| idx | INDI s4 (campaign C212) | INDI s1 | PID s1 |
|---|---|---|---|
| item 1 (LOC) | k1 PASS / k2 PASS (tilt max 47.1 deg) | k1 PASS / k2 PASS (46.6 deg) | k1 PASS / k2 PASS (40.5 deg) |
| item 2 k1 | FAIL q 2.0 Hz 47.4 (also r 2.5 Hz 18.8) | PASS (nothing sustained; max flagged q 14.9, p 13.4, r 12.3) | FAIL p 2.0 Hz 31.1, q 2.0 Hz 24.9 |
| item 2 k2 | FAIL q 2.0 Hz 52.0 | PASS (max q 13.0, p 10.9, r 10.2) | FAIL p 2.0 Hz 30.5, q 2.0 Hz 24.8 |
| item 3 k1 | FAIL horiz RMS 0.317 vs 0.30 | FAIL 0.308 vs 0.30 | PASS 0.138 vs 0.30 |
| item 3 k2 | FAIL 0.317 vs 0.30 | FAIL 0.308 vs 0.30 | PASS 2.568 vs 0.15 but ungated, see caveat |

Key-1 windows: s4 54.4-57.4 s, INDI s1 60.2-63.2 s, PID s1 60.7-63.7 s (window start follows the flight timeline, not a fixed time).

## Draw (g3_draw.json)
corner C3, position mode, airframe quad5in, flight 100 s. G1 error e (controller G1 / plant G1): roll 0.986, pitch 1.186, yaw 1.062.
Plant tau up x1.525, down x2.058 (tau_scale 2.058, asym 1.349; model-variant tau_up 0.741 rel). Controller ACT_TC ratio r = 1.0128 on
tau_mean 1.792 -> MC_INDI_ACT_TC 0.059881 s. Loop delay 1.25 ms total (0.625 act + 0.625 IMU). Mass x1.3, inertia ixx 1.256, iyy 1.013, izz 0.796.
Thrust available scale 0.351 (saturation, hover margin 2.0); weak motor 3 (index 2) scale 0.990. Telemetry: latency 0 frames, loss off,
frozen off, dropout 0. Vibration x1.470 (acc 1.47 m/s2, gyr 0.0735 rad/s). GNSS latency 228 ms, EKF delay 178 ms (unmatched, -50 ms).
Wind 1.66 m/s steady + gust amp 7.34 m/s (peak 9.0 m/s), towards 164.9 deg. Thrust sag off (replaced by saturation).

## Conclusion
- Item 2 does NOT reproduce at speed 1 for INDI: no sustained line on either key (largest flagged windows 10-15 dps, vs 2.0 Hz q 47-52 dps at speed 4),
  so the 2.0 Hz q / 2.5 Hz r lines of the campaign flight are not a reproducible property of this draw at speed 1 (single flight, one noise realisation).
  Item 3 does reproduce marginally on both keys (0.308 vs limit 0.30; campaign 0.317).
- PID on the same draw fails item 2 on both keys with a 2.0 Hz line (p and q, 24-31 dps), the same frequency as the INDI s4 line, but passes item 3
  (0.138): the draw excites a ~2 Hz roll/pitch line in the PID reference as well, so it is a draw property not specific to INDI.

## Unverified / caveats
- PID key 2 item 3: g3_checks_key2.py picked mode trajectory, no wind/sag, window 69.65-79.65 s, ungated (limits 0.15/0.10), unlike INDI (position, gated,
  75.8-78.8 s). The PID item 3 k2 value (2.568) is not a position-hold score; the key-2 verdict "item 3 PASS" for PID only means "not gated".
  Cause not investigated (same S199 procedure; key-2 args for PID are the key-1 args, mode is inferred by key 2).
- Key-1 RMS numbers use `max_rms_ratio_flagged`; if the S199 convention was another field the key-1 number may differ.
- One flight per stack; INDI s1 vs s4 difference is one sample each, run-to-run spread at speed 1 not measured.
- Not committed.

## idx 024 / draw 264 (S213, abort_flight halt of C212)
Run as for 022: `g3_chain.sh start .../indi_024 24 24 --samples .../samples --speed 1` and `fly_pid_run.py 24` (dry run: argv equal to speed-4 run_024
and to the speed-1 INDI run). One attempt each, no retry. Draw, g3_params.txt and g3_scenario_overrides.json of indi_024 and pid_024 equal `../run_024`
(MC_INDI_ACT_TC 0.017749 in all).

Plant check vs freeze-10 draw 264 (`g3_campaign_f10/run_264/g3_draw.json`): `factors`, `hooks`, `gz_seed` identical (same plant, wind, delays, vibration,
weak motor, saturation). Only `actc`, block, run_index and source_run differ. ACT_TC: freeze-10 0.033 s (params file); C212 run_024 0.017749 s
(r = 0.9755 x tau_mean 0.5513 x 0.033; fast plant, tau_up 0.5 / tau_down 0.603).

Weak motor: index 3 (4th motor, 0-based `weak_motor.motor` 3), available thrust scale 0.709 (-29.1 %). Saturation: available thrust scale 0.351
(2.0 x hover margin, 0.27 x mass 1.3); motor command saturates at 1.0, so the weak motor's effective ceiling is 0.351 x 0.709 = 0.249 of nominal max thrust.
Other draw values: mass x1.3, inertia ixx 1.165 iyy 1.167 izz 0.815, delays 5 steps (act and IMU).

| | INDI s4 freeze-10 (S199 campaign, ACT_TC 0.033) | INDI s1 S199 (ACT_TC 0.033) | INDI s4 C212 (ACT_TC 0.017749) | INDI s1 C212 (this) | PID s1 (this) |
|---|---|---|---|---|---|
| outcome | ABORT tilt > 60 deg at 60.67 s | ABORT tilt > 60 deg at 60.91 s | ABORT tilt > 60 deg 0.5 s at 60.78 s (74.4 deg) | ABORT tilt > 60 deg 0.5 s at 61.03 s (114 deg) | flies, no LOC; item 1 PASS tilt max 40.4 deg, height drop 0.0 m (k1 and k2) |
| scoring | unscored | unscored | INVALID/INVALID | INVALID/INVALID | k1 FAIL item 2 p 2.0 Hz 21.3 dps (item 3 PASS 0.136); k2 FAIL item 2 p 2.0 Hz 22.1 dps (item 3 k2 ungated, mode trajectory, 2.448 m, as in 022) |

The tilt watchdog trips within 0.4 s in all four INDI flights (60.67-61.03 s): the loss of control happens at the same point of the trajectory for both
ACT_TC values and both speeds. PID on the same draw does not lose control.

INDI, last 2 s before the abort (pyulog, actuator_motors and vehicle_angular_velocity, 0.25 s bins; log time, the log ends at the abort):
- s1 C212: max motor command 1.00, reached only by motor index 3 (the weak one); the others peak 0.69-0.70. Motor 3 is >= 0.99 in 15 % of the samples of the
  last 2 s, so 1 motor at the cap at any time. Rates are calm until 1.2 s before the end (max 16-54 dps), then pitch rate q reaches 195-206 dps first
  (p 95, r 153 in the same bin), motor 3 at 1.0 from about 0.5 s before the end. First diverging axis: pitch (q), yaw rate rising at the same time.
- s4 C212: max command 1.00 (motor 3, 26 % of samples >= 0.99, others <= 0.77). Already oscillating at the start of the window (p 179, q 156 dps, then r 147,
  q 180 dps): first diverging axis not readable from a 2 s window.
- "At the cap" is read as command >= 0.99; 0.351 is a thrust scale, not a command level.
Unverified: the first-axis call for s1 rests on one 0.25 s bin where p, q and r grow together; no longer window or setpoint comparison was done.
The ulog script was kept in the session scratchpad only, not in the repo.
