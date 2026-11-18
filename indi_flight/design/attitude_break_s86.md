# G2 attitude-loop break at the rate setpoint (S86 design note, before any code)

Status: DRAFT, needs a second key before the first flight (GATES.md G2 "Loops and break points", cell table row
"attitude ... to specify"). Nothing here is implemented. Anything not read in the code is marked UNVERIFIED.

## 0. Loop and constraint

- The attitude loop of the INDI stack is the stock `mc_att_control` (D-F-b rejected an outer-module attitude loop,
  DECISIONS.md ~line 80). Its output `rates_sp = _attitude_control.update(q)` is published as `vehicle_rates_setpoint`
  (`src/modules/mc_att_control/mc_att_control_main.cpp:366,382-389`) and received by `mc_indi_rate_control`.
- O-11: `mc_att_control`, `mc_rate_control`, `mc_pos_control`, `control_allocator`, `commander` stay at zero diff vs
  main (checked at the start: `git diff --stat main -- src/modules/mc_att_control src/modules/mc_rate_control` is empty).
  So the injection lives in `mc_indi_rate_control`, on the receiving side of the topic.
- Break point: the summation point between the attitude controller output and the rate loop input.
  x = rate setpoint as applied to the INDI rate loop (after d), y = attitude-controller output (before d).

## 1. Where the excitation is added

Files: `src/modules/mc_indi_rate_control/McIndiRateControl.cpp` / `.hpp`, `IndiInjection.*` (reused as is).

Current code:
- Subscription and storage of the setpoint: `Run()` lines 353-358 (`_rates_setpoint` <- `vehicle_rates_setpoint`; held
  until the next topic update, which comes at the attitude-loop rate).
- Watchdog zeroing: lines 364-382 (`wd.zero_rates` -> `_rates_setpoint.zero()` at 381; `_rate_sp_stale` set at 366).
- Call into the rate controller: line 406-407 `runIndiRateControl(..., angular_velocity.timestamp_sample, armed)`.
- `runIndiRateControl()` lines 211-251; the INDI call is at 231-232
  (`_indi.update(rates, _rates_setpoint, angular_accel, ...)`); the existing M3a torque injection is 234-243;
  the status message is filled 245-263.
- Injector parameters are pushed at lines 111-112 (`_injection.setParameters(...)`); members at `.hpp:125, 217-223`.

Proposed change (description only):
1. In `runIndiRateControl()`, before line 231, build a LOCAL `rates_sp_applied = _rates_setpoint + d_r`, where
   `d_r(axis) = _injection.update(timestamp_sample, armed, landed)` only when PT = 1 (section 3) and `!_rate_sp_stale`;
   all other components of `d_r` are exactly 0. Pass `rates_sp_applied` to `_indi.update()`. Never write d_r into the
   member `_rates_setpoint` and never publish it.
2. The torque injection (lines 234-243) is skipped when PT = 1 (one injector at a time), so `u == c` there.
3. With AX = 0 neither branch runs; `rates_sp_applied` is not computed (pass `_rates_setpoint` itself) so the flight is
   bit-identical to the current build (same promise as D-G2-INJ "adds exact zero").

Why this breaks the attitude loop and nothing else:
- Rate loop stays closed: the INDI rate law (`src/lib/indi_rate_control/indi_rate_control.cpp`) still computes u from
  gyro rate and angular acceleration; d_r only shifts its reference. The M3a feedback paths (torque model, measured
  torque, `_prev_torque_setpoint`) are untouched.
- The setpoint-lead path is INSIDE the cut: `_indi.update` differentiates the rate setpoint it is given
  (`indi_rate_control.cpp:387-404`, Tc 0.01 s, clamp 1000 rad/s^2, yaw LPF on the yaw error). It is fed x, so it
  differentiates y + d. That is correct for L: the lead is part of the path x -> u. (The loop closes through y, which
  the lead never sees alone.)
- The attitude controller does not see d_r except through the plant: d_r is not in `vehicle_rates_setpoint` (we never
  publish it; the ACRO branch republish at 344-350 is a different branch and carries `_rates_setpoint` only), and
  `mc_att_control` reads only `vehicle_attitude`, `vehicle_attitude_setpoint` etc. So y = f(q) responds to d only
  via rate -> attitude. Feedback L = -y/x then holds by construction.
- Not cut, and so left in the measurement: the outer loops (mc_indi_pos_control -> attitude setpoint) stay closed.
  They have crossover near 0.6 Hz (S83: velocity PM point 0.6-0.7 Hz), so the measured L is "attitude loop with outer
  loops closed", same as the M3a result is "rate loop with the attitude loop closed" (margins_models.py `att_p` term).
  Report the lowest accepted bin; do not claim L below ~0.3 Hz is the isolated attitude loop.
- Yaw: the yaw rate setpoint passes the yaw error LPF inside the library; it is inside the cut. Heading setpoint is
  constant in hover_long, so no extra path.

## 2. Signals, convention, logging

Convention (same as `pinj_csv.py:6`, `margins_est.py` docstring): x = applied signal after injection, y = controller
output returned to the summation point before injection, d = injected, L = -G_yd/G_xd (so y = -L x for the estimator's
frf; sign of the loop is the one the estimator already uses for every other break).
- d: `rates_sp_inject[axis]` (rad/s)
- x: `rates_sp_applied[axis]` = y + d
- y: `rates_sp_pre_inject[axis]` = `_rates_setpoint[axis]` as held in the rate module (post watchdog)

What must be logged and at what rate:
- Not `vehicle_rates_setpoint`: it is logged only on topic update (attitude rate, UNVERIFIED value in SITL), carries
  y only (d is not in it), and the default profile logs it at 20 ms (`logged_topics.cpp:159`). It is useful only as
  an independent second source of y (below).
- New fields in `msg/IndiRateStatus.msg` (next to `torque_sp_pre_inject / inject / torque_sp`, lines 17-19):
  `float32[3] rates_sp_pre_inject`, `float32[3] rates_sp_inject`, `float32[3] rates_sp_applied`. One sample per rate
  cycle (800 Hz / 400 Hz, gyro-driven). `indi_rate_status` is logged at interval 0 by the bench
  (`run_scenario.py:86`, LOG_TOPICS) and as `add_optional_topic("indi_rate_status")` with no interval in the profile
  (`logged_topics.cpp:90`), so the rate is the cycle rate. These are the same rate-cycle samples the analysis needs
  (frf at the controller rate); no resampling of a held 100-250 Hz signal.
- y is a zero-order hold of the attitude loop output (changes at the attitude update instants, constant in between).
  That is physically the signal the rate loop consumes; L therefore includes the hold. The estimator's coherence at
  high bins tells whether this is clean; if coherence is poor above ~attitude-rate/4, report that band as limited.
- Timestamps: x, y, d are indexed by `indi_rate_status.timestamp_sample` (gyro sample time = simulation time under the
  D-SIM-STEP lockstep, UNVERIFIED that `timestamp_sample` equals sim time in the current sim bridge for every
  `--sim`; the validity check "d equals the generator on timestamp_sample" is the one already required in GATES.md).
  `indi_rate_status.timestamp` is `hrt_absolute_time()` at publish and is not the key.
- Also log (already present): `fault`, `rate_sp_stale` (line 366 / msg), `vehicle_land_detected`.

Second source of y: join the last `vehicle_rates_setpoint` sample at or before each cycle (the module's
`_last_rates_sp_time` is its `.timestamp`); the held value must equal `rates_sp_pre_inject` to 1e-6 except in
watchdog-zeroed cycles. A mismatch means the module stores or zeroes something other than the topic.

## 3. Parameters, gating, amplitude

Recommendation: reuse `MC_INDI_INJ_AX/TP/FMIN/FMAX/NP/DLY` (`mc_indi_rate_control_params.yaml:220-293`) and the
`IndiInjection` object, and add TWO parameters:
- `MC_INDI_INJ_PT` enum (0 = M3a torque setpoint, default, current behaviour; 1 = rate setpoint, attitude-loop break).
  Mirrors `MC_INDI_PINJ_PT` (`mc_indi_pos_control_params.yaml:100-108`).
- `MC_INDI_INJ_RAMP` (rad/s per sine component, default 0.05, min 0, max 1). Reason: `MC_INDI_INJ_AMP` is normalised
  torque with default 0.02 and max 0.2; reinterpreting it as rad/s per PT would make a stale params file inject 4x
  to 10x too much or too little without an error. Separate units, separate param.
- Alternative: no new parameters, reinterpret AMP by PT (smaller diff, but the unit change is silent, and the existing
  bounds are wrong for rad/s). Alternative 2: a separate new enum AX values (4-6). Rejected: axis and break point are
  independent choices.

Gating (unchanged semantics from `IndiInjection::update`, `IndiInjection.hpp`): d = 0 unless armed, not landed, inside
[0, NP*Tp) after the origin (DLY after the first armed, airborne cycle). Added for PT 1: d = 0 while `_rate_sp_stale`
(setpoint timed out, rates zeroed) and when `fault` is set; both are logged so the validity rule "fault == 0" in
GATES.md still applies. No change to the injection while landed (c does not depend on x while landed, r2).

Per axis: AX 1 roll, 2 pitch, 3 yaw, one axis per flight (same as torque; D-G2-INJ).

Band and amplitude:
- Frequency: FMIN 0.2 Hz, FMAX 20 Hz for roll/pitch, Tp 10 s (grid 0.1 Hz). Roll/pitch attitude crossover is near
  MC_ROLL_P/(2 pi) = 1.3 Hz (`MC_ROLL_P 8`, `4040_gz_quad5in`:79) so 0.2-20 gives about one decade below and above
  (GATES.md excitation wording needs the crossover decade). Yaw: `MC_YAW_P 3` -> ~0.5 Hz crossover, use FMIN 0.1 Hz,
  FMAX 10 Hz. FMAX <= 0.4 x controller rate holds (GATES.md). The 64-component cap (IndiInjection.hpp
  MAX_COMPONENTS) is not hit at 10 bins/decade over 2-3 decades (~21 comps for 0.2-20 Hz).
  Below ~0.3 Hz the outer position loop shares the band (section 1): report, do not use for margins.
- Amplitude: default 0.05 rad/s per component (about 3 deg/s rms for 21 components, Schroeder peak about 5x the per
  component amplitude, ~0.27 rad/s ~ 15 deg/s). Resulting attitude excursion: a component at f gives amp/(2 pi f), i.e.
  0.04 rad at 0.2 Hz if the loop did not attenuate; the closed loop reduces it (|1/(1+L)|) so a few degrees at most
  (estimate, not computed). Linear range: the rate-setpoint limits MC_*RATE_MAX (value UNVERIFIED, grep found none in the
  airframe file) and the 1000 rad/s^2 lead clamp (at 20 Hz one component is 6 rad/s^2, far from it) must not be hit.
  Pre-test per GATES.md: two amplitudes (0.03 and 0.06 rad/s), |L| within 1 dB and arg L within 5 deg over the decade
  around crossover. Choose the smaller if coherence passes.

## 4. PID reference at the same break

- mc_rate_control is not touched and has no injector. But the stock mechanism exists in `mc_att_control`:
  `mc_att_control_main.cpp:371-379` adds `autotune_attitude_control_status.rate_sp` to `rates_sp` before publishing
  `vehicle_rates_setpoint` while the status state is ROLL/PITCH/YAW/TEST. It is the same break point (attitude output
  -> rate loop), usable with the PID stack with zero code change.
- Limits (read in `mc_autotune_attitude_control.cpp:603-625`): the signal is a state-machine step/filter sequence with
  `MC_AT_SYSID_AMP` (default 0.7, min 0.1, max 6.0 rad/s), not a periodic multisine on our grid; the module runs its own
  identification and parameter write-back (side effects: UNVERIFIED which parameters it changes in SITL; it must not be
  allowed to apply gains); the pre-injection y is not logged, only d (`status.rate_sp`), so y = x - d with x =
  `vehicle_rates_setpoint` at the att update rate (hold at the rate loop). Estimation with `margins_est.frf_periodic`
  needs a periodic input, so the existing mechanism cannot feed our estimator (at best a non-parametric spectral
  estimate, which is a different estimator and would need its own self-test).
- Recommendation: report the PID attitude-loop margins from the linear model only (labelled "model, not measured") in
  the cell table, and run the autotune signal once as a plausibility cross-check, not as a gate cell, unless the owner
  accepts a bench-only publisher of `autotune_attitude_control_status` with our multisine in `rate_sp` (new module; not
  verified feasible with logging of y). Do not invent more: no other PX4 mechanism found.

## 5. Linear-model cross-check

`bench/margins_models.py` today: `L_indi` (lines 81-117) is the rate loop at M3a, with an optional parallel attitude
path (params `att_p`, `att_lat`, `sp_lead`, lines 38, 108-116): L = L_rate + (K + lead) att_p z^-att_lat T z/(1-z) Pn,
a proportional attitude law with a one-sample latency, the 1000 rad/s^2 clamp ignored, `HEAD_FLIGHT` has att_p 8.
`L_pid` (120-141) has no attitude path. `simulate_loop` / `L_timedomain` (232-308): time-domain check of the rate loop;
whether it supports `att_p` is UNVERIFIED.

Missing for the attitude break (to write after the second key, not now):
- `L_att_indi(w, ...)`: with A = (K + lead) att_p z^-att_lat T z/(1-z) Pn and L_rate the att_p = 0 loop,
  L_att = A/(1 + L_rate) (closed rate loop from rate setpoint to rate, times attitude integrator and gain). Exact
  identity usable as a test: 1 + L_M3a(att_p) = (1 + L_rate)(1 + L_att). Pn scaling (G1 units) must be re-derived: UNVERIFIED.
- Yaw: `MC_YAW_P`, the yaw error LPF (`_yaw_error_lpf`) and the yaw cutoff `MC_INDI_YAW_CUT`; the model has none.
- The real attitude law is quaternion-based with a tilt-first yaw weight (`MC_YAW_WEIGHT`) and rate limits; the model is
  linearised about hover (small angles): state this in the result; nonlinearity is only handled by the two-amplitude test.
- Attitude-loop latency `att_lat` (1 sample is a placeholder; the true latency is rate-setpoint topic age, UNVERIFIED).
- The attitude-rate sample-and-hold in y (section 2) at the attitude loop rate.
- PID: `L_att_pid` = same A with Kp/Ki/Kd closed rate loop (needs `att_p` in `L_pid`).
Acceptance (GATES.md): measured PM within 10 deg and GM within 3 dB of the model, or an ANOMALIES.md entry.

## 6. Tests that fail when the injector is broken, and the pre-test

Unit / module (gtest, `CMakeLists.txt` of the module lists tests with `px4_add_unit_gtest`):
- Extract the application of d to a pure function (e.g. `applyRateSetpointInjection(rates_sp, axis, d)` in
  `IndiInjection`, or free function), because `runIndiRateControl` needs the module context. Tests in
  `IndiInjectionTest.cpp` style:
  - OffIsBitIdentical: AX = 0 gives the input vector byte-for-byte (memcmp), and the function is never evaluated.
  - OnlyTheSelectedAxis: for each axis k, out - in is d on k and exactly 0.0 on the other two (fails if axis index
    off by one, or d added to all axes).
  - SignAndPoint: out = in + d (fails on y - d, or on injection at the wrong point: torque instead of rate setpoint
    when PT = 1, and conversely PT = 0 leaves the rate setpoint untouched).
  - Gating: disarmed, landed, stale setpoint, outside window, all give exact input.
  - Waveform identity: d(t) equals the existing MatchesMarginsEst constants (`IndiInjectionTest.cpp:61-64`), with
    amplitude from RAMP, not AMP (fails if the wrong parameter is passed).
  - Lib-level (`src/lib/indi_rate_control` functional test): with fixed gyro/accel, `update(rates, sp + d)` changes u by
    the same amount as `update(rates, sp)` with sp + d, i.e. d reaches u through the setpoint path and the lead sees it
    (fails if the injection is applied after `_indi.update`, which would be an M3a torque break).
- Python self-test of the extractor (the open item in S83 README, "pinj_csv.py synthetic self-test"): build a synthetic
  pyulog-like table of a known loop (y = -L0 x with L0 a known delay/integrator), run extract + `margins_est`, compare
  PM/GM with the closed-form value; also a case with x and y swapped, which must fail on the sign (PM changes or L
  inverse).
- Runner validity checks per run (new, in the extractor): max |x - y - d| <= 1e-6; max |y - held vehicle_rates_setpoint|
  <= 1e-6 outside stale cycles; d equals the generator on `timestamp_sample`; `fault == 0`, `landed == 0`; no gap > 3
  periods (hole reporter). AX = 0 flight: all three new fields zero and the rest of the log identical to the previous
  build (G1.7 / bit-identical check used for the PINJ injector).

One-flight pre-test (copy of `results/stage5_s83_velbreak/README.md` pattern; paths are placeholders, directory to be
created: `indi_flight/results/stage5_s86_attbreak/`). Params file `roll_a05.params` (INDI stack, v2, quad5in, roll):
`MC_INDI_INJ_AX 1`, `MC_INDI_INJ_PT 1`, `MC_INDI_INJ_RAMP 0.05`, `MC_INDI_INJ_TP 10`, `MC_INDI_INJ_FMIN 0.2`,
`MC_INDI_INJ_FMAX 20`, `MC_INDI_INJ_NP 5`, `MC_INDI_INJ_DLY 20`.
```
indi_project/docker/run.sh -n s86att1 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long \
  --controller indi --model quad5in --sim v2 --rate-hz 400 --seed 1 --speed 4 \
  --params indi_flight/results/stage5_s86_attbreak/roll_a05.params --out indi_flight/results/stage5_s86_attbreak/roll_a05
indi_project/docker/run.sh -n s86an1 -t 240 -- python3 indi_flight/bench/ratesp_csv.py \
  indi_flight/results/stage5_s86_attbreak/roll_a05/flight.ulg 0 indi_flight/results/stage5_s86_attbreak/roll_a05_att.csv \
  --Tp 10 --fmin 0.2 --fmax 20 --margins > indi_flight/results/stage5_s86_attbreak/roll_a05_margins.json
```
`ratesp_csv.py` does not exist: either a `--point ratesp` branch of `pinj_csv.py` (reads `indi_rate_status`,
`window()` as at `pinj_csv.py:22-37`) or a copy of `m3a_csv.py`. 400 Hz first (as S83), 800 Hz after the pre-test.
Pre-test pass: injected window with d != 0 for 50 s; two flights (amplitude 0.03 / 0.06) linear within 1 dB / 5 deg;
estimator coherence >= 0.9 within a decade of the crossover; validity checks above; the PM (and sign of arg L) is
plausible against the model of section 5 (expected PM from the lag of the rate loop plus the attitude hold: not computed
here). Hover_long is a 60 s hold (`scenarios.py:66`); DLY 20 + NP 5 x Tp 10 = 70 s may exceed it: UNVERIFIED how
S83 (also DLY 20, NP 5) fit, check `meta` before the flight or use NP 4.

## 7. Open questions

1. Attitude-loop update rate and the latency from the `mc_att_control` update to the rate module in SITL (UNVERIFIED);
   it sets `att_lat`, the y hold, and the top of the useful band.
2. Is L "attitude loop with the outer loops closed" acceptable for the gate wording "Attitude" in GATES.md, or does the
   owner want the outer loops opened (would need the PINJ break in addition, more flights)?
3. Yaw: the yaw filter and `MC_YAW_WEIGHT` (UNVERIFIED value in quad5in) make the yaw break different from roll/pitch;
   flown in the same campaign or reported separately?
4. PID cell: model-only, or accept a bench publisher of the autotune status topic (section 4)?
5. Does the first-sample behaviour of the setpoint lead (reset flag, `indi_rate_control.cpp:392-395`) create a transient
   at the window start (d begins at ~0 so likely not, the Schroeder start is ~0: UNVERIFIED), and is it excluded by the
   discarded first period?
6. New msg fields grow `indi_rate_status`: size/rate impact on the log at 800 Hz (UNVERIFIED), plus the msg change touches
   a shared uORB definition; confirm it is acceptable under O-11 (msg is not in the frozen module list).
7. Amplitude default depends on `MC_*RATE_MAX` and the real airframe saturation margins; confirm in the pre-test with the
   fraction of saturated motors in `actuator_motors`.

## 8. S90 amendments (T185)

Resolves review `attitude_break_s86_review.md`. Implementation: `src/modules/mc_indi_rate_control/IndiInjectionStep.{hpp,cpp}`
(the step `runIndiRateControl` runs: law call + injection), tests `IndiInjectionStepTest.cpp`, check `bench/attitude_break_check.py`.

- MAJOR 1 (call-site test), accepted. The application of d and the `_indi.update` call were extracted into
  `runIndiInjectionStep()`; `runIndiRateControl` calls only that, so the test runs the module's code with the real
  `IndiRateControl`. `RateSetpointBreakFeedsLawTheInjectedSetpoint` compares, cycle by cycle and bit-exact, the law output and
  its lead state `rate_sp_dot` against a second law fed `y + d` by hand, and requires that a law fed `y` would differ (test can
  tell). Replaces the tautological "lib-level" test of section 6 (dropped). Break-it-once results in `t190_impl_log.md`.
- MAJOR 2 (independent check), accepted. Replaces the circular `x - y - d` check (kept as an informative line only):
  `attitude_break_check.py` (a) one-step prediction of the logged `rate_sp_dot` from the logged x with the library filter,
  alpha = dt/(Tc+dt), Tc = `kSetpointLeadTc` = 0.01 s, clamp `kMaxRateSpDot` = 1000 rad/s^2 (constants read in
  `indi_rate_control.hpp:279,283`, `.cpp:399-404`), relative rms error <= 2 %; (b) power of `torque_sp_pre_inject` at the excited
  bins k/Tp >= 4x the median power at the unexcited integer bins of the band. Yaw: (a) is SKIPPED (the law differentiates
  the yaw-LPF'd setpoint); use (b) and a yaw-specific check later.
- MINOR accepted: gate d = 0 unless `flag_control_attitude_enabled` (so not in ACRO) and `!rate_sp_stale`, and while the law
  reports `fault` from the previous cycle (d is needed before the update, so the same-cycle fault cannot be used).
- MINOR accepted: with PT = 1 `MC_INDI_INJ_AMP` is ignored (amplitude = `MC_INDI_INJ_RAMP`); the amplitude actually used is
  visible in the logged `rates_sp_inject`. Torque injection is off at PT = 1 (u == c).
- MINOR accepted: the three new fields are zero unless PT = 1 and AX != 0 (AX = 0 logs unchanged apart from three zero fields).
- MINOR accepted: scenario `hover_xlong` (150 s, `scenarios.py:67`) instead of `hover_long`. Window arithmetic: DLY 20 s +
  NP x Tp must fit in 150 s minus a tail: NP 5 x Tp 10 = 50 s ends at 70 s, leaving 80 s; the earlier "70 s vs 60 s" overrun
  was against the 60 s scenario and does not apply. The window arrives after take-off settling, which is part of the 150 s
  scenario (UNVERIFIED how long the scenario spends in take-off before `hold`: read `meta` of the first flight).
- MINOR accepted (wording): the y check against `vehicle_rates_setpoint` is flagged by the non-finite substitution case
  (`rates(i)` stored instead of NaN); document in the validity list, and state the profile interval of the second source.
- MINOR accepted (wording): section 5 factor A is not L/(1+L); it carries (K + lead) Pn.
- MINOR not acted on here (out of scope for this change, no code): ZOH staircase of y in the lead (model item for section 5);
  PID reference through the stock autotune hook (model-only cell stays); outer-loop closure and gate wording (open question 2);
  msg size/drop check, which is a first-flight item.
- Pre-test fix: use `--scenario hover_xlong` and the params of section 6 with `MC_INDI_INJ_PT 1`.
