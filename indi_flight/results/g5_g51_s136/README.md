# G5.1 flight-mode stick steps, S136 build and pre-test

## Built (all under indi_flight/bench, nothing committed)
- `scenarios.py`: `stick_steps` (mode stick, segments settle 3 s, stick 10.5 s, hold 3 s, `steps=True`, traj None).
- `stick_profile.py`: `step_sticks(t, mode)`, `STEP_AMP` (acro 1.0, stabilized 0.5), `stick_sample(..., steps=True)` (throttle = neutral/hover
  sample, x/y/r from the table). Per axis roll, pitch, yaw: +A 0.5 s, -A 0.5 s, 0 for 2.5 s (3.5 s per axis). Existing scenarios unchanged.
- `run_scenario.py`: the "stick" segment uses the steps sample when `sc["steps"]`; sticks.csv logs what was applied.
- `g51_check.py RUN_DIR...` -> `g51_check.json` + one PASS/FAIL/INVALID line. Edges from sticks.csv; acro RMS windows
  [e+0.1, next edge) for +A and -A, [release+0.1, release+1.0] for the 0 plateau (right end exclusive); stabilized tilt window
  [release+1.0, release+2.5], yaw rate in the same window after yaw; LOC = tilt >= 80 deg or truth height < 0.2 m in the step span;
  INVALID if nav_state in the steps is not [10] (acro) / [15] (stabilized). Truth: vehicle_angular_velocity_groundtruth,
  vehicle_attitude_groundtruth, vehicle_local_position_groundtruth (800 Hz in the log).
- `tests/test_g51_check.py` (5 tests, analytic first-order RMS, sign, gain, mode, stabilized tilt/yaw-rate, LOC) and
  `test_g51_steps` in `tests/test_stick_profile.py`. Host has no pytest: run `python3 tests/test_g51_check.py` (all pass); test_g51_steps passes when called directly.
- `run_batch.sh` (seeds 1-3 x acro/stab, resumable, `SEEDS="2 3"` override, runs the checker at the end). NOT run for seeds 2-3.

## Sign conventions (verified in source)
MANUAL_CONTROL y = roll (+ = roll right), x = pitch (mavlink_receiver: pitch = x/1000, roll = y/1000), r = yaw. mc_indi_rate_control acro:
rate sp = (roll, -pitch, yaw) x stick x MC_ACRO_{R,P,Y}_MAX, so +x (stick forward) = NEGATIVE body pitch rate q. Checker command for pitch = -x/1000 x MAX.
Values in effect (ULog initial_parameters): MC_ACRO_R/P/Y_MAX 100, EXPO 0, SUPEXPO 0, MPC_MAN_TILT_MAX 35, MPC_MAN_Y_MAX 150 (firmware defaults, not set by the scenario).

## Pre-test (seed 1), result: the test as defined is not flyable at 5 m
1. Watchdog-on runs (`wdtrip_acro_s1`, `wdtrip_stab_s1`): both tripped "> 3 m below hold altitude for 1 s" at sim t about 65.5 s (about 7 s into the steps, during
   the pitch/yaw doublets). The throttle is constant (vehicle_thrust_setpoint 0.137 all along, HTE 0.137) and there is no altitude loop, so each tilt
   costs thrust (stabilized 17.5 deg = 4.6 %, acro roll +50 deg for 0.5 s) and the vehicle accumulates sink (0.4 m/s after the roll doublet, 5 m take-off height).
2. Diagnostic runs with `--watchdog off` (`wdoff_acro_s1`, `wdoff_stab_s1`, NEVER in a batch): the vehicle reaches the ground at step time +7.0 s (acro) / +8.2 s (stab),
   i.e. right when the yaw doublet starts, so loc=True and the yaw numbers are on the ground (not meaningful).
   - acro (nav_state 10 only): roll RMS 13.60 deg/s, pitch RMS 13.03, yaw 34.14 (invalid, ground); off-axis RMS 0.2/0.8/2.5. Rise 90 %: roll 0.21 s, pitch 0.21 s, yaw 0.47 s
     (GATES assumes about 0.1 s for the transient: the real response is about 2x slower, so the RMS over [edge+0.1, ...] is dominated by the rise). Overshoot < 0.9 deg/s.
   - stabilized (nav_state 15 only): residual tilt in [release+1, +2.5]: roll 0.25 deg, pitch 0.20 deg (pass <= 3), yaw tilt 0.00, yaw rate 0.54 deg/s (pass <= 10; but on the ground).
3. Sticks reached the vehicle: manual_control_setpoint max |roll,pitch,yaw| = 1.0 (acro) / 0.5 (stab), 1666 / 1415 samples; mode main mode confirmed from nav_state; truth rate and attitude 800 Hz.

## Unverified / needs a decision
- "Throttle stick held at hover" cannot hold 5 m for 10.5 s with 100 deg/s acro doublets and 17.5 deg stabilized doublets. Options for the owner (definition change, not made here):
  start higher (take-off alt), tilt-compensated throttle in the profile (thr = hover / cos of the commanded tilt, open loop), or a short altitude-restoring throttle between axes.
  Also unverified: whether the hover thrust (0.137) is slightly low (sink 0.025 m/s over the settle).
- The acro RMS window skips only 0.1 s; with a measured 90 % rise of 0.21 s the roll/pitch RMS of 13 deg/s would FAIL <= 10 on this seed even without the crash (the plateaus before the crash are valid).
- No seed 2-3 runs. `wdtrip_*` directories were renamed so that run_batch.sh does not skip them as done.

## S136 orchestrator follow-up
- Diagnosis of the wdoff runs: rate setpoint reaches 100 deg/s in 1.5 ms after the stick edge; truth t90 = 208 ms =
  2.3 / (0.5 x K 20 rad/s): the params file had MC_INDI_ID_OK 0 (pre-identification half gains). G5 uses the identified
  configuration: `params.params` here = s133_passthrough with MC_INDI_ID_OK 1. Expected acro plateau RMS at K 20 about 3-4 deg/s.
- Altitude sink fixed by `--stick-pilot` with steps: the pilot drives the throttle only (run_scenario.make_pilot_sp, steps flag).
- Second key (key2/, haiku, blind): per-plateau RMS roll 11.23/23.30/7.41, pitch 11.74/21.13/7.52; pooled over the
  0.4/0.4/0.9 s windows = 13.7 / 12.9 deg/s vs checker 13.6 / 13.0: AGREE. Stabilized tilt 0.25/0.20 deg: AGREE.
- First pilot pre-test (failed_s136/): both runs ended "TypeError: 'NoneType' object is not subscriptable" before the
  stick segment (353 neutral rows, pilot never active). Runner now records the traceback in run.json; re-fly pending.

## S136 probe batch (3 seeds x 2 modes, fixed runner, ID_OK 1, --stick-pilot throttle only) -- PROBE, RC113
| run | verdict | numbers |
|---|---|---|
| acro s1-s3 | FAIL (yaw) | roll RMS 1.48-1.55, pitch 1.52-6.44 (s2, off-axis 1.8), yaw 15.0-16.0 deg/s (limit 10); max tilt 48-51 deg, no LOC |
| stab s1-s3 | PASS | residual tilt <= 0.12 deg, yaw rate <= 0.20 deg/s after release (limits 3 deg, 10 deg/s); no LOC |
Full lines: g51_summary.txt. G5.1 acro yaw is a gate-test failure: one session of cause search (yaw bandwidth K_Y vs
measured yaw t90, yaw saturation/allocation priority), then re-open decision 5 (yaw) if not explained.
Cause lead (arithmetic, not yet checked on the log): MC_INDI_K_Y 10 rad/s -> first-order tau 0.1 s -> plateau RMS
over the gate windows about 13 deg/s from the bandwidth alone (same arithmetic gave 13.6 vs 13.6 measured for roll at
0.5 x 20). So the yaw miss is the yaw bandwidth default, not a fault. Options for next session: raise K_Y if yaw
authority and G2 yaw margins allow (decision 4/5), or a justified yaw-specific limit (gate change -> owner question).
