# Stage-3 inner-loop items: design note (before code)

Scope: `src/modules/mc_indi_rate_control/` (module, `McIndiRateControl.cpp` = M, `IndiMeasuredTorque.cpp` = T),
`src/lib/indi_rate_control/indi_rate_control.cpp` (law = L), `ROMFS/px4fmu_common/init.d/rc.mc_apps` (rc).
Source of items: `indi_project/review/external_review_s59.md` sec. 4 and 5.2b (items there are partly untraced by
the reviewer; each was re-read here). Constraints: no PID fallback, stock modules/allocator/commander at zero diff,
PID stays default (MC_INDI_EN 0). New parameters go in `mc_indi_rate_control_params.yaml`.
Line numbers are from the working tree of branch feat/indi-flight at the time of writing.

## 1. Landed handling

(a) Current. M:276-277 copies `landed` and `maybe_landed`; M:336 passes `_maybe_landed || _landed` as one flag.
L:374 `t_fb = landed ? 0 : t_f` removes the measured/filtered feedback torque on the ground (comment L:371-373:
"at takeoff the law steps by the modelled torque ... bounded by the maximum increment"). L:323 freezes the blend
filter when landed (L:328 `_blend = t_gap`), L:343-344 restarts yaw filters each landed cycle, L:384 sets lead gain
to 0 when landed. Steps 3-5 still run (L:250). So the review's "zero the whole trim torque" (L:373 in its text) is
now: feedback term zero, modelled state still tracked. `MC_INDI_DT_MAX` default 1.0 (yaml) bounds the step only
at 1 normalised torque/cycle, i.e. effectively not at all. PID stock freezes only the integrator.
(b) Defect. (i) A false `maybe_landed` in flight (it toggles during hard descents, low-thrust hover, bounces) drops
the feedback torque, the lead and the yaw filter state in one cycle, then restores them in one cycle on release: two
torque steps of the size of the trim (F6 take-off jump is the same step at lift-off). (ii) `maybe_landed` is
treated like `landed`, but the stock PID treats only `landed` as hard reset (it freezes I-term on `landed`
/`maybe_landed` but keeps P/D). Consequence: attitude/rate kick of the order of trim/G1 at every flag edge.
(c) Proposal. Split the flag: pass `landed` (hard, state-restart as today) and `maybe_landed` (soft) separately
to `IndiRateControl::update`. Soft = hold, not zero: keep `t_fb`, keep lead, but freeze the blend integrator and
the yaw-filter restart (no reset), and clamp the per-cycle change of the published torque to
`MC_INDI_LND_SLEW` (new, float, normalised torque/s, default 5.0: roughly 0.0125 per 400 Hz cycle, below the
full-authority step of 1.0 in 0.2 s, well above any manoeuvre torque rate; flagged UNVERIFIED against flight logs).
Hard landed: unchanged zeroing, but on the falling edge of `landed` ramp `t_fb` from 0 with the same slew limit
(take-off jump) instead of stepping. Also require `flag_armed` for any edge logic (reset already in M:~318).
New state: `_t_fb_prev` (Vector3f), `_ground_prev` (bool). Log: add `ground_state` (0 air, 1 maybe, 2 landed) to
`indi_rate_status` (uORB msg edit in `msg/`; UNVERIFIED that the msg has a spare field).
(d) Alternatives. Zero all (today): kick. Ignore maybe_landed entirely: unsafe on touchdown (integrates on ground).
Reuse `MC_INDI_DT_MAX` as slew: it is per-increment, default unbounded, different meaning.
(e) Tests (lib `indi_rate_control_test.cpp`). `MaybeLandedPulseNoStep`: steady in-flight state with trim torque
0.1 N-norm, toggle maybe_landed true for 50 cycles then false; assert max |u_k - u_{k-1}| <= LND_SLEW*dt+1e-6 and
|u| at 10 cycles after release equals pre-pulse within 1%. `TakeoffRamp`: landed true 1 s with hover thrust
setpoint, then false; assert no single-cycle step > slew*dt and u reaches the law output within 0.5 s. Both fail
on the current code (step of full t_f at the edge).

## 2. Start-up exclusion of the two rate modules

(a) Current. rc:17-22: `if param compare -s MC_INDI_EN 1; mc_indi_rate_control start; else mc_rate_control start`.
`print_usage` in M says "only one of the two is started". The code of the module does not check the other
(review 5.2b; separate ModuleBase descriptors). MC_INDI_EN is read only here (grep'd rc; module code reading it
UNVERIFIED). Both modules publish `vehicle_torque_setpoint`/`vehicle_thrust_setpoint`.
(b) Defect. `mc_rate_control start` typed by hand/an rc.board script while INDI runs gives two publishers on the
same topics: torque alternates between two controllers at a combined rate 2x; flight consequence = undefined
oscillation, not detectable from either log.
(c) Proposal. In `McIndiRateControl::init()` (M:67) query the other module, with no change to its source: a
`vehicle_torque_setpoint` publisher check is impossible from uORB without a topic change, so use
`orb_group_count`-style detection UNVERIFIED; the concrete option that needs only INDI code: INDI module
advertises its own presence by publishing `indi_rate_status` (exists, M:228) and, on init, checks
`orb_exists(ORB_ID(vehicle_torque_setpoint), 0)` with a fresh sample (< 0.1 s) before it starts publishing;
if yes: `PX4_ERR("another rate controller is publishing")`, return false from `init()` (start refused). At run
time, if `vehicle_torque_setpoint` of a foreign publisher is seen: the module cannot tell publishers apart
(UNVERIFIED), so the run-time part is only a log. Second line of defence in rc: add `mc_indi_rate_control
status`-style guard is not available; keep the if/else and add an rc comment. Parameter: none.
(d) Alternatives. Modify mc_rate_control to refuse (forbidden, zero diff). Commander arming check (forbidden).
Shared lock file under /fs: not portable to NuttX.
(e) Test. SITL shell test (`indi_flight` scripts): start `mc_rate_control` first, then `mc_indi_rate_control start`,
assert exit code != 0 and `listener vehicle_torque_setpoint` rate == one controller's rate (+-5 %).
Unit test of init is not possible without a uORB mock (UNVERIFIED that test infrastructure offers one).

## 3. Rate setpoint timeout

(a) Current. M:300ff: non-acro branch `_vehicle_rates_setpoint_sub.update(...)` stores `_rates_setpoint`,
`_thrust_setpoint` only on a new message; no age tracking anywhere in M. Stock `mc_rate_control` behaves the same
(holds last), so no stock reference to copy.
(b) Defect. If `mc_att_control` or `mc_indi_pos_control` stops (crash, scheduling stall, mode switch edge), the last
rate and thrust are held forever: constant yaw rate / climb thrust until failsafe by commander (which uses other
topics, UNVERIFIED that a stale rates setpoint triggers any failsafe).
(c) Proposal. Store `_rates_setpoint_time` (hrt_abstime, `vehicle_rates_setpoint.timestamp` at receipt). In each
cycle (non-acro): `age = now - time`; if `age > MC_INDI_SP_TO` (new param, float s, default 0.2, min 0.05, max 2;
= 5 attitude cycles at 25 Hz minimum offboard-like rates, longer than mc_att_control period 4 ms by 50x so no false
trips; UNVERIFIED against slowest publisher) then `_rates_setpoint = 0`, `_thrust_setpoint` held as is for
`MC_INDI_SP_TO` more and then decays at 0.5/s (controlled descent, not zero: a zero thrust would drop the vehicle),
set `stale_setpoint` flag in `indi_rate_status`, one PX4_WARN rate-limited. Recovers on the next message. Not
active in acro (the sticks branch publishes its own setpoint M:306). Disarmed/landed: no action.
(d) Alternatives. Set thrust to zero: crash. Do nothing: today. Publish nothing: allocator holds old output.
(e) Tests (module-level unit test with the rate-setpoint injection; if no mock, SITL): `SetpointStaleDecays`:
publish rate 1 rad/s yaw + thrust 0.5, kill publisher at t0; assert rates_setpoint used = 0 for t > t0+0.2+1 cycle
and thrust < 0.5 for t > t0+0.4, and stale flag true; resume publishing -> flag clears within 1 cycle.

## 4. Frozen rotor-speed telemetry

(a) Current. M:148-163 forwards `esc.esc_rpm` and `esc.timestamp` into T `setMotorSample`; T:122 stores
`timestamp_good = timestamp` on every call; T:141-142 freshness is `now - timestamp_good < SAMPLE_MAX_AGE_US` and
`online`, `has_value`, `u_valid`; T:156 `valid=false` if any motor is not fresh (one bad motor invalidates the
whole vector). M:197-200 additionally requires `now - timestamp_sample < MC_INDI_ERPM_TO` (0.02 s default).
Fallback when invalid: `setMeasuredTorque(..., false)` -> L:315 `_meas_in_use` false after
`kMeasValidCycles` -> modelled state path (L:225, L:339). L:315 has a hysteresis count of valid cycles
(value of `kMeasValidCycles` UNVERIFIED here).
(b) Defect. The DShot driver refreshes `esc.timestamp` at every publication even when the rpm is the previous
frame (review 5.2b, driver UNVERIFIED here, not traced). A frozen rpm (no capture, extended telemetry frame)
looks fresh and valid, the measured-torque path then feeds a constant torque: with a blend the loop sees a
constant disturbance-free measurement and loses the actuator-feedback, in flight the vehicle behaves as with a
broken gain; no log flag shows it.
(c) Proposal. In T per motor keep `last_rpm`, `timestamp_change` (time rpm last differed by more than
`kRpmEps` = 1 rpm). In `setMotorSample` set `timestamp_good = timestamp` only if |rpm - last_rpm| > kRpmEps, else
leave it; then freshness T:142 uses the unchanged age. A motor at constant true speed must not trip: only
declare frozen when `now - timestamp_change > MC_INDI_ERPM_FRZ` (new param, float s, default 0.5, min 0.1 max 5)
AND the commanded motor value changed (commanded u derived from the torque setpoint swing > 5 % of range over
that window; simpler UNVERIFIED variant: frozen iff all 4 rpm identical at the integer level for the window, since
four real rotors never stay bit-identical under noise). Chosen: per-motor "no change in `FRZ` while thrust
setpoint std over the window > 2 %". Frozen motor => `setMotorOffline` semantics (mask bit cleared, vector
invalid) -> existing modelled path with its hysteresis; publish `frozen_mask` in `actuator_torque_measured`
(uORB msg field UNVERIFIED: may need a new field) and in `indi_rate_status`. Also fix index assumption: use
`esc.actuator_function` (already used M:153) for the online bit: test `esc_online_flags & (1u << j)` uses j, not
`motor` (M:157): contiguous motors only (review item), keep but add a comment/assert for non-contiguous.
(d) Alternatives. Require every rpm to change every sample: false trips at steady hover with 1 rpm quantisation.
Use the DShot error counter only: does not catch frozen values (the review's point). Drop the measured path:
loses the feature.
(e) Tests (`IndiMeasuredTorqueTest.cpp`): `FrozenRpmFallsBack`: feed 4 motors rpm 5000 with timestamps advancing
every 2.5 ms and the thrust varying, for 0.6 s; assert `result.valid == false` after FRZ and `motor_valid_mask`
excludes the frozen motor; `ConstantButNoisyRpmValid`: rpm 5000 +-3 random, assert valid for 5 s;
`FrozenRecovers`: rpm changes again -> valid returns within one sample. Lib test: with `meas_valid=false` after
valid, `_meas_in_use` goes false and output is finite and continuous (|step| < 1e-3 at the switch, blend path).

## 5. Autotune start

(a) Current. rc:30-33 starts `mc_autotune_attitude_control` when `MC_AT_EN > 0`, independent of `MC_INDI_EN`. The
autotune module (mc_autotune_attitude_control.cpp:100-116) starts on `VEHICLE_CMD_DO_AUTOTUNE_ENABLE` (param1==1)
and identifies from `vehicle_torque_setpoint` and `vehicle_angular_velocity`, then writes `MC_ROLLRATE_*` etc.
(parameter names UNVERIFIED here). INDI ignores those parameters.
(b) Defect. With INDI active the autotune would excite the vehicle with its own injected rate setpoints
(it publishes through `vehicle_rates_setpoint`/torque path UNVERIFIED), fit PID gains for a controller that is not
running, then save them: confusion for the pilot, and the excitation runs through an unvalidated INDI gain.
(c) Proposal. rc only: `if param greater -s MC_AT_EN 0 && !(MC_INDI_EN==1)` -> in rc.mc_apps, nest:
`if param compare -s MC_INDI_EN 1; then (skip, echo "autotune disabled with INDI") else start; fi`. Do not touch
the autotune module or commander (zero diff). On the INDI side: add an INDI warning once if
`parameter MC_AT_EN > 0` at init (param read UNVERIFIED if in module deps). Boards without the INDI module:
`MC_INDI_EN` absent -> `param compare` false -> unchanged behaviour (as rc:15 states).
(d) Alternatives. Let autotune run and write INDI gains: identification target differs (G1, tau), a separate
project. Refuse DO_AUTOTUNE_ENABLE in INDI module: a vehicle_command ack from a second node conflicts with the
autotune ack. Document only: leaves the trap.
(e) Test. rc-script syntax test via SITL start with `MC_INDI_EN=1 MC_AT_EN=1`: assert `mc_autotune_attitude_control
status` reports not running; with `MC_INDI_EN=0 MC_AT_EN=1` assert running (regression).

## 6. Firmware defaults (listing only; ACT_TC and LEAD decided elsewhere)

Values from `mc_indi_rate_control_params.yaml`. Validation status: only SITL, generic quad; no flight data.
- MC_INDI_EN 0 (correct, PID stays default).
- MC_INDI_W_MAX 0: telemetry path off; the vehicle-specific value is required for the measured path; unvalidated
  for any airframe (same for MC_INDI_ERPM_*).
- MC_INDI_G1_R 320, G1_P 210: SITL-identified generic quad, not hardware. MC_INDI_G1_Y 30: yaml says "not identified
  for any airframe". MC_INDI_G2_Y 0 (off).
- MC_INDI_K_R 20, K_P 20, K_Y 10: random-search (review 4.1), no measured margins at these values on hardware;
  review sec. 4.4: yaw slower than PID.
- MC_INDI_ACT_TC 0.02 and MC_INDI_LEAD 1: not touched here (decided separately).
- MC_INDI_DELAY 0 (samples), MC_INDI_ERPM_DLY 1 (samples), MC_INDI_ERPM_TO 0.02 s: SITL values, hardware latency
  unverified.
- MC_INDI_ACT_BLD 0.0: blend OFF by default; review 4.2 says the blend restores model-based integral action below
  0.53 Hz and Tb 0.1 crashed: the default is the pure-measured path with no steady-state correction: unvalidated.
- MC_INDI_DT_MAX 1.0: effectively no bound on the per-cycle increment (review 4.5): should become a real limit; a
  value is a decision for the implementation task after the slew item above (suggest tying to the LND_SLEW test).
- MC_INDI_YAW_CUT 0 (yaw filter cutoff off): yaw filter chain not validated at hardware rates (review 4.6).
- MC_INDI_INJ_* : bench-only; INJ_AX 0 (off) is correct: must stay 0 in release, add a startup PX4_WARN if > 0
  (UNVERIFIED if present).
Test: a param-default regression test (`px4_params` YAML check or SITL `param show`) that asserts EN==0 and
INJ_AX==0 so a default change is flagged.

## UNVERIFIED (consolidated)
kMeasValidCycles value; DShot driver refresh behaviour; whether a stale `vehicle_rates_setpoint` triggers any
commander failsafe; existence of spare fields in `indi_rate_status` / `actuator_torque_measured`; availability
of a uORB mock for module unit tests; whether foreign publishers on `vehicle_torque_setpoint` are detectable;
autotune module's parameter writes; SP_TO / LND_SLEW / FRZ thresholds against flight data; whether the module
code reads MC_INDI_EN itself.
