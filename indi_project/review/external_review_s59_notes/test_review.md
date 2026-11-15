# Test-quality review (read-only, mutation testing by reading)

Scope: indi_rate_control (40 tests), indi_accel_control (19), IndiMeasuredTorque (4). Not read in detail: tests at
indi_rate_control_test.cpp lines 480-640 (yaw cutoff noise tests), accel tests after line 453 (jerk FF / difference);
judged from names and the helpers. Nothing was built or run.

## 0. What the suites actually are

- Rate lib: ONE closed-loop harness (RollPlant, roll axis only, 400 Hz, delay 0, kG1True=100 == controller G1,
  plant tc == model tc == 20 ms, plant LPF2p 40 Hz + alpha 20 Hz == controller filters). Used by only 3 tests
  (RateStepResponse, ConstantDisturbance, SaturatedAllocator). Everything else is open-loop with scripted inputs, mostly
  constant or DC, asserting a value on axis 0.
- Accel lib: ZERO closed-loop tests, ZERO multi-axis dynamics. Every test is a 1 to 5 step feed-forward evaluation at
  kDt = 10 ms, level or yaw-only attitude, filters disabled except in two tests (100 Hz / 10 Hz).
- MeasuredTorque: the "plant" is the production allocator class itself; the tests invert the production formula
  (rpmFromThrust is the exact inverse of u=(w/wmax)^2).
- Consequence: the plant shares every assumption with the controller, so any error that is common to both (tc, filter
  design, G1, delay direction, frame convention) is invisible by construction. That is exactly the class of defect found
  later (aliasing, delay direction, reset every landed cycle, fallback).

## 1. Mutation table

K = killed, S = survives, W = killed only by a loose bound (likely survives for small mutations).

### indi_rate_control

| Behaviour / mutation | Result | Why |
|---|---|---|
| nu sign, `nu - a_f` sign flip | K | RateStep, Disturbance diverge |
| a_f missing (disturbance rejection) | K | ConstantDisturbance |
| numerator / G1 for roll (wrong index or scale) | K | Landed tests assert exactly 0.1 |
| G1 error x0.5 / x2 inside the plant | S1 | never varied; plant G1 == controller G1 |
| max_increment clamp removed / wrong | K | 0.05 tests |
| t_cmd clamp to +-1 removed | K | ASSERT_LE(abs(command),1) in saturated test |
| t_alloc clamp to +-1 removed | S2 | no |alloc|>1 input anywhere |
| meas input clamp +-1 removed | S3 | no |meas|>1 |
| actuator alpha formula (1-exp(-dt/tc) -> dt/tc) | S4 | plant uses same formula and loop is tolerant (<5 % error) |
| actuator tc clamp [0.001,0.2] / NaN default 0.02 | S5 | only 1 ms, 20 ms, 200 ms used; NaN never passed |
| setFilterCutoffs NaN / negative handling | S6 | only 0 tested for gyro/dgyro (yaw has its own invalid test) |
| LPF2p vs alpha order swapped | S7 | both LTI, commute in steady state; only reset values differ, no test sees it |
| gyro/dgyro cutoffs swapped in designSyncFilters (lpf=20, alpha=40) | S8 | step test tolerances (+-5 %, 20 % overshoot) absorb it; plant isn't re-derived |
| alpha filter dropped from MODEL path only (t_f desynchronised from a_f) | S9 | model-vs-plant sync never checked dynamically; only DC |
| model path delay actually applied (swap target vars model/meas) | S10 | MeasurementDelay test checks model output stays 0 but alloc is 0, so a delayed model is also 0 |
| delay direction head+samples | K | PassThroughFiltersAndDelay (but only open loop, constant input) |
| delay in closed loop (plant with delay vs model delay) | S11 | no closed loop with delay > 0 |
| delay change one sample per cycle | K | DelayChangeMidRun |
| measurement path sync with model (same filters) | K | MeasurementEqualToModel (1e-4) |
| meas valid counter (kMeasValidCycles), drop on any invalid | K | 3 tests |
| meas fed model torque while invalid (bumpless return) | K | InvalidFeedKeepsMeasurementFilters |
| NaN measurement invalid and not poisoning filters | K | |
| fallback from meas to model during a manoeuvre with a_f dynamics | S12 | only DC / constant alloc; no dropout while rates move |
| blend: sign, enabled/disabled bit-identical | K | Blend tests |
| blend alpha dt/(tb+dt) -> dt/tb or tb off by 2x | S13 | SteadyGap runs 10 Tb and tolerates 1 %; HF test only checks >=0.9 of ref |
| kMaxBlend clamp, kMaxBlendTimeConstant cap | S14 | gap never above 0.15 |
| blend/measurement on axes 1, 2 | S15 | blend tests assert axis 0 only |
| blend while landed (no accumulation) | K | LandedBlend |
| landed: t_fb = 0 | K | |
| landed: a_f ignored/kept (nonzero angular_accel while landed) | S16 | every landed test passes angular_accel = 0 |
| landed with yaw g2 spin-up term (uses t_f - t_f_prev, not t_fb) | S17 | g2 = 0 in all landed tests |
| landed->airborne with a trim torque (nonzero model torque at takeoff) | W | only alloc = own output, 0.05-0.1 magnitude; ok for increment bound, not for trim offset |
| landed yaw filter reset each cycle | K | LandedYawOutput (the previous defect, now covered) |
| yaw g2 term sign / magnitude | S18 | YawSpinUp asserts only `differs > 1e-6` |
| yaw LPF applied to a_f but not to t_f (or error) | S19 | noise tests are std comparisons; no dynamic sync check |
| yaw filter transient on enable | K | YawCutoffEnableHasNoTransient |
| fault: NaN input / bad dt / bad G1 hold then zero | K | |
| fault: gain_k negative / NaN | S20 | only G1 swept |
| fault: finite-huge input overflow -> faultOutput(true) branch | S21 | only inf (rejected earlier), never finite overflow |
| fault: g2_yaw NaN | S22 | |
| sample-rate change redesign: filter continuity | W | one 400->200 step, DC only, t_f only (a_f alpha state continuity unchecked) |
| redesign threshold kRedesignRatio / sample_freq low-pass | W | jitter test is open loop, one +-20 % alternating pattern |
| rates 250 / 800 / 1000 Hz in closed loop | S23 | only 400 Hz closed loop |
| setMaxIncrement invalid values | K | |
| normalisedThrustFromRpm | K | |

### indi_accel_control

| Behaviour / mutation | Result | Why |
|---|---|---|
| R vs R^T (or wrong frame) in `a_f = R*f_bf + g` | S24 | q is identity or yaw-only with f_b along z only; tilted q with horizontal f_b never tested |
| accelerometer aliasing / sampling-rate related error | S25 | out of scope of the lib, no module test either |
| t_f = z_b * (-g_t*u_f) sign / uses z_b | W | only level or tilt via a_ref, z_b never tilted at input |
| gravity sign | K | Hover |
| INDI increment `t_f + a_c - a_f` signs | K | PureIndiIncrement, ModelError |
| delay direction (u delayed vs f delayed) | S26 | FilterMatching and Clamp assert the implemented direction; no physical plant with known lag to prove it right |
| delay indexing off by one | K | MeasurementDelayClamp (exact sample count) |
| lpf_f / lpf_u mismatch (cutoff or order) | K | FilterMatching 1e-5 |
| lpf_j cutoff | W | Test exists (JerkDifferenceFiltered), not read |
| tilt clamp, vertical priority | K | one angle only (0.5, 0.7) |
| thrust saturation, vertical priority | K | one case |
| tilt + thrust saturation together, horizontal-only saturation order | S27 | never combined |
| `c < c_min` branch (scale whole vector) | S28 | probably dead code: t_c(2) already forced <= -c_min so c >= c_min (equivalent mutant; remove or test) |
| t_c(2) > -kMinUpThrust floor | K | ThrustPointsUp |
| thrust normalisation with k_cmd, g_t | K | HoverEq 1.1 |
| thrust deficit (delivered 0.85 of commanded) | S29 | no closed loop |
| mean_u fallback to previous command | K | |
| NaN handling of inputs, NaN refs | K | one-shot; q(1..3) NaN, q norm < 0.5, mean_u_valid false with NaN not each tested | 
| q norm < 0.5 guard | S30 | |
| setGains / setLimits / setThrustModel invalid rejection | S31 | never called with invalid values |
| velocity limit xy norm / z | K | |
| yaw NaN keeps current yaw, yawspeed passthrough | K | |
| jerk FF sign, coordinated turn, clamp | K | |
| reset() semantics (zero first increment) | K | |
| different dt than kDt = 10 ms, jitter | S32 | |
| steady-state loop with real plant (position/velocity/thrust dynamics) | S33 | none |

### IndiMeasuredTorque

| Behaviour / mutation | Result | Why |
|---|---|---|
| actuator -> torque mapping | K | against allocator output |
| `actuator - trim` (trim ignored) | S34 | _trim and _linearization_point are zero-initialised and never set |
| weak-row zeroing threshold 0.05 | S35 | X500 matrix has no weak rows |
| normalize_rpy = false | S36 | |
| age check `<` vs `<=` SAMPLE_MAX_AGE, timestamp_good > now | S37 | only a clearly stale sample |
| error_count drop logic | K | single case; first-sample-with-nonzero-count not tested |
| rpm -> u mapping (omega^2) vs real motor thrust curve | S38 | test inverts the implementation |
| quantised / low-resolution rpm (eRPM scaling, pole pairs) | S39 | not at this layer |
| offline motor, NaN, implausible rpm, disabled | K | |
| num_rotors > MAX, motor index >= num_rotors | S40 | |

Surviving mutations identified: 40 (some are equivalent or low-value: S7, S28; the high-value ones are S1, S8, S9,
S10, S11, S12, S13, S16, S17, S18, S19, S24, S26, S29, S33).

## 2. Weak assertions

- Rate: `RateStepResponse` +-5 %, overshoot < 20 %, reach 0.95 by 0.5 s: for a 50 ms loop this is a 10x margin; it does
  not constrain any filter/gain detail. `SaturatedAllocatorDoesNotWindUp` ends with `|rate| < 0.05` only (also true if
  the controller did nothing useful after release).
- `ConstantDisturbance`: DC disturbance, needs only a_f path at DC; no frequency content.
- `YawSpinUpTermChangesYawOnly`: `differs` boolean. `YawCutoffReducesYawNoiseOnly` and the noise tests: std ratios
  (not read in detail), no phase/lag check.
- `DtJitter`: bound 1.5x one ramp step, open loop, alternating pattern (a periodic dt is not jitter: random jitter and
  occasional 2x dt not tested).
- Blend tests: axis 0 only, one gap value (0.15), one time constant (0.3 s), 1e-3 absolute tolerances relative to values
  of 0.35 to 0.5.
- `MeasurementDelay...` model-unchanged assertion is vacuous (alloc 0).
- `FollowsMeasurementWhenModelIsWrong` is the only model-mismatch test and it is zero-input DC: it shows the measured path
  wins at DC, not that the loop is stable when the model is wrong.
- Accel: all tests are algebraic spot checks; no `finite/bounded`-only tests but also no dynamic ones. FilterMatching
  and MeasurementDelayClamp assert the implemented direction.
- Same-assumption plants: RollPlant (tc, filter chain, G1, zero delay, sample rate all equal to the controller);
  MeasuredTorque (allocator class used as its own oracle, rpm map inverted from the implementation).
- Single sample rate: closed loop 400 Hz only; the module's 250 Hz yaw tests are open-loop; accel lib 100 Hz/10 ms only.

## 3. Missing closed-loop cases (none exists today)

All are cheap with the existing RollPlant if the plant is parametrised (plant tc, plant G1, plant delay, plant filter
cutoffs, dt sequence). Priority order:

1. Actuator tc mismatch: plant tc = 2x and 3x model tc (model 20 ms, plant 40 and 60 ms), with and without delay; assert
   decay of a rate step, overshoot bound, no limit cycle over 5 s.
2. Delay mismatch: plant pure delay 0..4 samples with controller setDelaySamples 0..4 (under- and over-compensated);
   assert stable and overshoot < X for matched, stable-but-oscillatory allowed for +-1 sample.
3. G1 error x0.5 and x2 (and x3 boundary): stability and settling time; this is the standard INDI robustness check.
4. dt jitter in closed loop (random +-20 %, occasional 2x), assert no fault and bounded rate error.
5. Sample rates 250 / 400 / 800 / 1000 Hz: same step response; checks redesign and filter cutoff vs Nyquist (1000 Hz also
   interacts with kMaxDt / kMinDt and kRedesignRatio).
6. Steady gap command/output (plant delivers 0.8 of command, or constant bias) with and without blend, measured torque
   from plant actuator: rate error to zero, no limit cycle, blend state bounded.
7. Saturation on one axis (roll allocator clipped) while pitch/yaw track: the other axes must keep their response
   (each axis independent) and recover without wind-up.
8. Measured-torque dropouts in the middle of a rate manoeuvre (sine setpoint): source switches model/measurement, assert
   the torque command has no step bigger than a bound at the switch (existing bumpless test is DC only).
9. Quantised rpm (e.g. 10-50 rpm steps, or eRPM at 1 kHz): measured torque noise into the high-frequency blend; assert
   rate noise std not amplified over the model-only path.
10. Landed -> airborne with a trim torque (e.g. alloc 0.2 offset, a_f from gravity-balanced hover): command step at
    takeoff bounded by max_increment, no yaw filter glitch, g2 != 0.
11. Outer loop (accel lib) with thrust deficit: plant thrust = 0.85 * k_cmd * command; assert altitude/velocity converges
    (INDI measured-acceleration path should remove it) and thrust hits thr_max correctly.
12. Outer loop with tilt and thrust saturation simultaneously (aggressive a_ref): vertical priority holds across cycles,
    no oscillation between branches.
13. Outer loop with EKF-like delayed velocity (100-200 ms) and noisy accelerometer: bounded position response.
14. Accel lib at 50/100/250 Hz with real dt jitter.

## 4. Untested modules: 8 behaviours worth a module-level or SITL test

McIndiRateControl.cpp (rate module):
1. `torque_allocated_prev` composition: `_prev_torque_setpoint - _unallocated_torque` only when the allocator feedback is
   newer than the setpoint (timestamp comparison, first cycle, stale feedback).
2. Measurement validity gate: `_torque_measured.valid`, age < MC_INDI_ERPM_TO, `now >= timestamp_sample`, non finite;
   behaviour when the topic never arrives (must stay on the model: `measured_torque_in_use` false).
3. Landed handling: `_maybe_landed || _landed` passed as landed; transition at takeoff; reset while disarmed and when
   vehicle_type != rotary wing (indi.reset + zero prev torque).
4. dt computation: `timestamp_sample` difference with constraint [0.125 ms, 20 ms], first cycle (`_last_run = 0`), and
   the library jitter filter on hardware gyro publication rates.
5. Rate setpoint handling: acro sticks branch vs topic branch, NaN fields replaced by current rate, thrust_setpoint
   sign/scale.

McIndiPosControl.cpp (position module):
6. Accelerometer path: the integral-dv window (`accelerometer_integral_dt`) aligned with the mean_u window, bias
   subtraction, filtered-rate measurement (`measureRate` 5..1000 Hz), and the aliasing issue (window mismatch vs
   `_filter_rate_hz`, resets at rate change).
7. Failure paths: `update()` returning false, stale local_position / ESC (`esc_fresh`), `hold()` behaviour: must command a
   level attitude / bounded thrust, not hold the last tilt (the previous defect); non-finite rates or thrust -> hold.
8. Landed branch and re-entry: zero rates and minimum thrust while landed, `_indi.reset(f_b, mean_u)` on re-entry with
   no step in thrust at takeoff; dt fallback (`1/_filter_rate_hz`, 0.02) and the trajectory_setpoint NaN fields (yaw,
   yawspeed, jerk) mapping to Input.

Preferred vehicle for 1-8: a small gtest fixture with the uORB mocks is heavy; a SITL replay with fault injection (stop
ESC status, drop control_allocator_status, freeze local_position, kill a motor) and log assertions on indi_rate_status /
the pos status topics is the cheapest.

## 5. Can the existing tests host a small linear closed-loop margin check?

Yes. `RollPlant` + `makeController()` in indi_rate_control_test.cpp is already a linear, saturation-free loop
(max_increment 1, small signals, g2 = 0). Parametrise RollPlant (plant tc, G1 scale, delay buffer, filter cutoffs, dt) and
(a) run a gain sweep: scale the plant G1 by 0.25..4 and the delay 0..4 samples, assert the step response decays
(|rate| envelope shrinks over the last 2 s); or (b) measure the loop transfer function: break the loop at the allocated
torque, drive a small sinusoid (0.5-60 Hz) through the controller+plant, estimate gain/phase by correlation, and assert
gain margin >= 6 dB and phase margin >= 35 deg at nominal, and >= 0 dB (stable) at G1 x2 and tc x2. No new infrastructure
besides the plant parametrisation.
