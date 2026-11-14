# INDI rate controller, independent control-law review (session 16)

Scope: `src/lib/indi_rate_control/indi_rate_control.{hpp,cpp}`, the integration in
`src/modules/mc_rate_control/`, the `MC_INDI_*` parameters and the unit tests, read fresh
and not anchored on `indi_project/plan/architecture.md`. No code was edited, built or run.

Severity scale: **bug** (wrong behaviour on a reachable path), **risk** (correct on the nominal
path, degrades or fails on a plausible one), **style** (readability, maintainability).
Each finding is marked **confirmed** (code path traced end to end) or **suspected** (reasoned
from the code, not traced to every consumer or not reproduced).

## 1. Incremental law: sign, units, filter matching, actuator state

Derivation from `indi_rate_control.cpp:217-243`: `nu = K.*(sp - rate)` [rad/s^2],
`dt_cmd = (nu - a_f) / G1` [rad/s^2 / (rad/s^2 per unit torque) = unit torque],
`t_cmd = t_f + dt_cmd`, with `t_f = alpha(lpf2p(delay(t_act)))`, `t_act` a ZOH first-order lag of the
previous allocated torque. Sign: `G1 >= kMinG1 > 0` is enforced (`paramsValid`, :63), so an
acceleration deficit gives a positive increment. Correct. Units are consistent on all three axes;
the yaw G2 form `(G1 + G2/dt) dt = nu - a_f + (G2/dt)(t_f - t_f_prev)` (:223-225) matches Smeur's
torque-space derivation with `u_f_dot ~ (t_f - t_f_prev)/dt`. Structurally, with an exact actuator
model the law collapses to `u = (K/G1) e` (pure P around the actuator state), so the increment itself
carries no integral action; the DC rejection comes from `1/(1 - H A_est)` acting as an integrator.

- **risk, confirmed** `indi_rate_control.cpp:86-87,100,158-164` and `MulticopterRateControl.cpp` (dt from
  `timestamp_sample`): the filter redesign trigger is a 10 % change of the *instantaneous* `1/dt`, and a
  redesign resets `_lpf/_alpha` to the current `_t_act` and re-settles the yaw filters at the unfiltered
  values. On hardware the gyro publication jitter regularly exceeds 10 %; every jittery cycle then
  discards the group-delay history of `t_f` (it jumps from the lagged value to `_t_act`) while `a_f`
  stays lagged by the sensor chain, so the pair desynchronises and `t_cmd` steps by `(t_act - t_f)`.
  The next nominal cycle differs again by > 10 % from the jittery design rate and resets a second time.
  The sensor side avoids this by designing on the configured sample rate. Fix: design on a low-pass
  filtered or nominal rate (as `VehicleAngularVelocity` does), require the deviation to persist, and
  do not reset the filter states on a coefficient-only redesign.
- **risk, suspected** `indi_rate_control.cpp:190-193` vs `VehicleAngularVelocity.cpp:768-786`: H is
  `LPF2p(IMU_GYRO_CUTOFF)` then `AlphaFilter(IMU_DGYRO_CUTOFF)`, same order as the sensor chain, but
  designed at the controller rate (IMU_GYRO_RATEMAX) while the sensor chain runs at the gyro sample
  rate (1-8 kHz); the bilinear prewarp keeps the magnitude close, the phase differs by a few degrees
  below the cutoff and more as IMU_GYRO_RATEMAX is lowered. The static and dynamic notch filters
  (`_notch_filter_velocity`, ESC/FFT notches) are not mirrored; a static notch placed below ~100 Hz
  adds phase to `a_f` that `t_f` lacks. Fix: document the rate assumption, and either mirror the static
  notch or warn when `IMU_GYRO_NF0_FRQ` is set with INDI active.
- **risk, confirmed** `MulticopterRateControl.cpp` `runIndiRateControl`: `torque_allocated_prev` only
  subtracts the unallocated torque if `_unallocated_torque_time > _prev_torque_setpoint_time`; the
  allocator publishes its status at most every 5 ms (`ControlAllocator.cpp:467-474`), so at a 400 Hz
  loop the saturation feedback is stale on half the cycles and the model integrates the full
  (clamped +-1) setpoint instead of the achieved torque. Bounded (one unit of torque), recovers in
  ~`ACT_TC` + H delay, but it is a windup-like offset at saturation. Fix: publish the status every
  cycle when INDI is selected, or carry the last unallocated value across cycles.
- **ok, confirmed** `indi_rate_control.cpp:181-182`: `alpha = 1 - exp(-dt/tc)` is the exact ZOH
  discretisation for an input held over the cycle, and the input is the command of cycle k-1 while the
  gyro sample is at t_k, which is the right one-cycle alignment. Output latency (PWM/DShot period,
  ESC, sensor batch) is only representable in whole cycles via `MC_INDI_DELAY`.
- **style** `indi_rate_control.cpp:228`: `_t_f_prev = t_f` is updated before the NaN check at :230;
  harmless because the fault path calls `reset()`.

## 2. Yaw path filters (MC_INDI_YAW_CUT on the rate error)

Structure (`indi_rate_control.cpp:198-216`): one `LowPassFilter2p` design F (Butterworth, same
`sample_freq`/`_yaw_cutoff_hz`, :93-97) is instantiated three times and applied to `a_f(2)`, `t_f(2)` and
`rate_error(2) = rate_sp - rate`. All three instances are (re)settled on the same cycle through
`_yaw_filter_reset_pending` (:205-211), so the `(a_f, t_f)` pair stays synchronised: both carry F's
group delay on top of H's. Commit 1d776dc6dc makes `resetStates()` set the pending flag (:128), so the
landed and fault paths now restart the three filters at the current inputs instead of at zero.

**Effective yaw law.** With F linear and identical on the three terms, and G2 included,
`dt_cmd_y = [K F e - F a_f + (G2/dt) F(t_f - t_f_prev)] / (G1 + G2/dt) = F(dt_cmd_y,unfiltered)` and
`t_cmd_y = F t_f + F dt_cmd = F(t_cmd_y,unfiltered)`: up to the two clamps (applied after F) the yaw
command is exactly the unfiltered INDI law followed by an output low-pass, i.e. the same thing
`MC_YAW_TQ_CUTOFF` does on the PID branch, including the setpoint prefilter effect. The incremental
structure is therefore not broken, but the increment is now referenced to `F H A u` instead of
`H A u`, so the closed loop becomes `u = F (K/G) e / (1 - F H dA)` (notation of section 5). The
denominator is helped (F lowers `|H dA|` at the 5-7 Hz band, section 5 mitigation 2); the numerator
adds F's phase at the yaw crossover `K_Y` rad/s.

- **risk, confirmed** `mc_rate_control_params.yaml:355-365` and `indi_rate_control.cpp:219`: no
  relation is enforced between `MC_INDI_YAW_CUT` (min 0, any positive value accepted, increment 1 Hz)
  and `MC_INDI_K_Y` (default 10 rad/s = 1.6 Hz crossover). A second-order Butterworth at 10 Hz costs
  ~13 deg at 1.6 Hz (fine); at 2 Hz, the value used by five of the unit tests, it costs ~75 deg of the
  ~80 deg nominal margin (plant 1/s, 20 ms actuator, H ~ -5 deg at 1.6 Hz), so the yaw loop oscillates
  or diverges before the clamps catch it, and the attitude loop closed around it (MC_YAW_P) loses the
  same phase. The tests only run at zero or constant rate so they cannot see it. Fix: document and
  enforce `YAW_CUT >= ~3 K_Y / (2 pi)` (e.g. param min 5 Hz, or disable the filter below that ratio
  as `kMaxYawCutoffRatio` does above).
- **risk, confirmed** `indi_rate_control.cpp:160-166,85-88`: a change of `MC_INDI_YAW_CUT` alone
  (enable, disable or retune in flight) goes through `designFilters()`, which also re-settles the
  roll and pitch H filters at the unfiltered `_t_act`. Whenever the torque is moving, `t_f` jumps by
  the H group delay (`t_act - t_f`) on all three axes and `t_cmd` steps by the same amount. The unit
  test `YawCutoffEnableHasNoTransient` uses a settled constant torque so `t_act == t_f` and the step is
  invisible. Fix: split `designFilters()` so a yaw-cutoff change only touches the yaw filters (and do
  not re-settle H on a coefficient-only redesign, section 1).
- **risk, confirmed** `indi_rate_control.cpp:91,100,226,230`: on a redesign that toggles
  `_yaw_filter_active` (dt clamped to 20 ms makes `0.45 * 50 Hz = 22.5 Hz` the ceiling, so a 30 Hz
  cutoff deactivates for that cycle and reactivates on the next), `t_f(2)` switches between the
  F-lagged and the raw value while `_t_f_prev(2)` holds the other kind, so the G2 term produces a
  one-cycle spike `(G2/dt)(t_f - t_f_prev)/(G1 + G2/dt)` of up to the full lag difference, and `a_f(2)`
  changes from filtered to raw noise. Bounded by `DT_MAX`, zero with the default `G2 = 0`. Fix: make the
  active/inactive decision hysteretic or key it on the nominal rate, and reset `_t_f_prev(2)` to the
  new-kind value on a toggle.
- **ok, confirmed** G2 spin-up term with the filter: `t_f - t_f_prev` uses the F-filtered `t_f`
  (:226,230), i.e. the derivative of the filtered command, which is the form Smeur uses
  (`u_f_dot`), and by linearity it stays consistent with the F-filtered `a_f`. Note the term's
  weight is `G2/dt`: with the parameter range `MC_INDI_G2_Y` up to 100 and dt = 2.5 ms, `G2/dt = 4e4`
  against `G1_Y = 30`, so `dt_cmd_y ~ (t_f - t_f_prev)` and the error term `(nu - a_f)/4e4` vanishes:
  yaw authority is lost silently (bounded, but open loop). Sensible values are `G2 ~ G1 dt` (~0.1); the
  parameter max should be ~1 (**risk, confirmed**, `mc_rate_control_params.yaml:283-292`).
- **ok, confirmed** landed path after 1d776dc6dc: `resetStates()` (:108-130) runs every landed cycle
  and sets the pending flag, so each cycle resets F at `(a_f(2), 0, e(2))` then applies once;
  `LowPassFilter2p::reset()` settles the delay elements at `input/(1+a1+a2)` so the output is the input
  within rounding. Yaw on the ground is `(K e - a_f)/G1`, the same P form as roll/pitch; the first
  airborne cycle continues from the last landed states, no step. Side effects: the yaw rate-error
  filter is inactive during the `maybe_landed` phase of a takeoff (noise reduction absent, phase lag
  absent, so the loop is in fact better damped there); the fault path (:150,234) now also restarts
  without the `b0` scaling. The pending flag is also set when the filter is inactive and is simply
  never consumed, harmless. Doc mismatch: `indi_rate_control.hpp:135` still says the filter states
  are "held at zero" while landed.
- **style** `indi_rate_control.hpp:108-110` says the filter is applied to "the measured rate in nu"
  while the code and the file header (:47-50) filter the rate *error*, setpoint included.

## 3. Numerical and operational edge cases

- **bug, confirmed** `indi_rate_control.cpp:168-172,202-214`: while `landed` (which includes
  `maybe_landed`, set for the first ~1/3 s of every takeoff and whenever thrust is low), `resetStates()`
  zeroes the three yaw filters every cycle and then applies them once, so `a_f(2)`, `t_f(2)` and the
  yaw rate error are multiplied by `b0` (~0.005 at 10 Hz / 400 Hz): yaw control is effectively disabled
  on the ground and during the first part of the takeoff when `MC_INDI_YAW_CUT > 0`. Fix: bypass the
  yaw filters while landed (or reset them at the current values, as the pending-reset path does).
- **risk, confirmed** same lines: while landed roll/pitch degrade to `t_cmd = (K/G1) e`, a P gain of
  0.0625 (defaults) vs the PID default of 0.15, no integral; the transition to the incremental law
  starts the actuator model from zero. Acceptable for ground contact, weak during the
  `maybe_landed` phase of a takeoff with a CoM offset. Fix: keep the actuator model running while
  landed and only hold `t_f` out of the output, or gate on `landed` rather than `maybe_landed`.
- **risk, confirmed** `indi_rate_control.cpp:147-151,230-235`: any non-finite input faults the cycle,
  outputs zero torque and wipes all states, so a single bad sample becomes a zero-torque cycle
  followed by a from-zero transient. Inputs are already sanitised upstream, so the path is rarely
  reachable; still, holding the last output and skipping the update would be the gentler reaction.
- **ok, confirmed**: dt is clamped to [0.125 ms, 20 ms] in `Run()`, so `dt_valid` can only fail on
  NaN; a long gyro gap clamps to 20 ms and triggers the redesign issue of section 1 (one cycle at a
  50 Hz design where a 30 Hz cutoff is above Nyquist and the yaw filter deactivates/reactivates).
- **ok, confirmed**: `t_cmd` is bounded to +-1 and the increment to `MC_INDI_DT_MAX`; because the
  incremental state follows the (achieved) actuator torque there is no integrator to wind up,
  subject to the stale-status caveat above.
- **risk, suspected** `MulticopterRateControl.cpp` disarmed branch: `_use_indi` is latched only when
  disarmed *and* `flag_control_rates_enabled`; arming from a mode where rates were disabled keeps the
  previous latch (PID by default) silently. Fix: latch on the armed edge regardless of the rate flag.
- **ok, confirmed**: PID/INDI switching is impossible in flight; VTOL transitions reset and re-latch.
  Parameter changes in flight (G1, K, ACT_TC, DELAY, DT_MAX) take effect immediately and are
  state-safe; cutoff changes trigger a settled redesign. Battery scaling and gain compression are
  bypassed for INDI (see section 5 for the latter).
- **risk, suspected**: no thrust-dependent effectiveness; with a quadratic ESC curve the true G1
  rises with throttle and drops with voltage sag, so the law is under-geared at low throttle and
  over-geared at high throttle relative to a hover-identified G1 (stable up to roughly 2x).

## 4. Boundedness, allocation, readability

Not covered in this pass.

## 5. Robustness to actuator time constant mismatch (5-7 Hz roll limit cycle)

**suspected** (derived from the code structure, not reproduced). With `t_f = H A_est u` and
`a_f = H G A_true u`, the code gives `u (1 - H A_est) = dt_cmd = (K e - H G A_true u)/G`, i.e.
`u = (K/G) e / (1 - H (A_est - A_true))`. With a matched model this is a plain P law and the loop is
`K A_true / s`. The mismatch term `dA = A_est - A_true = (tau_t - tau_e) s / ((tau_e s+1)(tau_t s+1))`
is a band-pass centred at `f* = 1/(2 pi sqrt(tau_e tau_t))` with peak `(tau_t - tau_e)/(sqrt(..)..)`:
for 20/40 ms, f* = 5.6 Hz with peak 0.33, so the controller gain rises by ~1.5 at 5-6 Hz; for
12.5/25 ms (gz x500 up/down) or 25/50 ms the band is 5-9 Hz. This is exactly the observed band, and it
sits below the 30 Hz H filters, so H neither causes nor suppresses it. Together with the extra
actuator phase (-55 deg at 35 rad/s for 40 ms), H phase (-26 deg) and 2-3 cycles of pipeline delay,
the phase margin near crossover (~3 Hz) collapses and the plant saturations (increment clamp,
allocator, asymmetric up/down motor constants) turn it into a limit cycle rather than divergence.

Why `MC_INDI_ACT_TC` alone does not reproduce it: (a) a slower model than the plant (1.5x-3x) gives a
negative `dA`, so `1 - H dA > 1` is a gain *reduction* (sluggish but safe); (b) a faster model (0.33x,
tau_e = 6.7 ms vs 20 ms) puts f* at ~14 Hz where `|L|` is already ~0.25 and H's -60 deg phase
de-tunes the term, so the boost is small and far from crossover. The dangerous case is specifically
*plant slower than model* with f* near crossover, which only the doubled-plant experiment creates.

Code-level mitigations, in order of preference:
1. Use the measured actuator state (ESC rpm from `esc_status`, torque ~ omega^2 through the
   effectiveness) instead of the first-order model for `t_act`; this removes `A_est` from the loop.
2. Generalise the yaw-only sync low-pass (`_yaw_lpf_*`, `MC_INDI_YAW_CUT`) to a per-axis cutoff on
   the `(a_f, t_f)` pair: lowering H at f* reduces `|1/(1 - H dA)|` without touching the P-equivalent
   path. 3. Re-enable an oscillation detector for INDI (`GainCompression` is bypassed in the INDI
   branch); it must scale `K`/`nu`, not `t_cmd`, to keep the increment consistent. 4. Model the
   asymmetric up/down time constants (gz uses 12.5/25 ms) and document that over-estimating
   `MC_INDI_ACT_TC` is the safe side.

## 6. Test coverage gaps

Not covered in this pass.

## Summary ranked by severity

1. **bug, confirmed** (s3): yaw filters zeroed every landed cycle, yaw control disabled on the ground
   and early takeoff when `MC_INDI_YAW_CUT > 0`.
2. **risk, confirmed** (s1): dt-jitter filter redesign resets `t_f` to `_t_act`, desynchronising the
   feedback pair and stepping the torque on hardware.
3. **risk, suspected** (s5): plant-slower-than-model mismatch is a band-pass gain boost at
   `1/(2 pi sqrt(tau_e tau_t))` = 5-7 Hz; mitigations: measured actuator state, per-axis sync
   low-pass, INDI-aware gain compression.
4. **risk, confirmed** (s1): allocator saturation feedback is stale on half the cycles (5 ms status
   cadence), windup-like offset at saturation.
5. **risk, confirmed** (s3): P-only weak law while `maybe_landed`, no actuator model running.
6. **risk, suspected** (s1): H designed at the controller rate, notches not mirrored.
7. **risk, suspected** (s3): `_use_indi` latch needs the rate flag while disarmed; fault path resets
   all states on a single bad sample; no thrust/voltage effectiveness scaling.
