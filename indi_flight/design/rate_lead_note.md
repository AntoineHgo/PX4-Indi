# Stage-3 design note: rate-prediction lead in the INDI rate law (D-RATE-LEAD)

Status: implemented S52 (reviewed r1 in S51, dispositions in `design/rate_lead_review_r1.md`; see `results/stage3_s52/lead_impl.md`). Sources: `indi_flight/DECISIONS.md` D-RATE-LEAD,
`indi_flight/results/stage2_s48/README.md`, `src/lib/indi_rate_control/indi_rate_control.{hpp,cpp}`,
`src/modules/mc_indi_rate_control/`. Line numbers refer to the tree at commit 0d61daaed4. Every statement not checked
against code or a result file is marked UNVERIFIED.

## 1. Law

### 1.1 Equations as they will be in code
Existing (cpp l.368, l.378-382):

    nu_i      = K_i (rate_sp_i - rate_i)                      (rate_error from l.351, yaw filtered l.364)
    num_i     = nu_i - a_f_i + g2_over_dt_i (t_f_i - t_f_prev_i)    (g2_over_dt = 0 for roll, pitch)
    dt_cmd_i  = num_i / (G1_i + g2_over_dt_i)
    t_cmd_i   = clamp(t_fb_i + clamp(dt_cmd_i, +-max_inc), -1, 1)

New: one extra term in the numerator, nothing else changes.

    c_i       = lead_scale * K_i * tau_c            (dimensionless, "K tau_c"; 0 when landed)
    num_i     = nu_i - (1 + c_i) a_f_i + g2_over_dt_i (t_f_i - t_f_prev_i)

Equivalent to nu_eff = K (rate_sp - w) - K tau_c a_f, then the unchanged incremental inversion. Matched check (roll,
pitch, a_f = G1 t_f): t_cmd = (K e - K tau_c a_f)/G1, plant a = G1 A(s) t_cmd, A = 1/(tau s + 1), a = s w, so
L(s) = K A(s) (1 + tau_c s)/s, and with tau_c = tau, L = K/s (the model of S48 section 3).

### 1.2 Sources
- a_f: the `angular_accel` argument of `update()` (hpp l.~176 docs, cpp l.209, l.348). It is `xyz_derivative` of
  `vehicle_angular_velocity` (McIndiRateControl.cpp l.265), i.e. the gyro derivative after the sensor chain (LPF2p
  IMU_GYRO_CUTOFF, then alpha filter IMU_DGYRO_CUTOFF). `update()` only adds the optional yaw LPF2p on a_f(2) (l.362).
  The lead uses the same local `a_f` (after the yaw filter), so no new filter and no new state.
- K per axis: `_gain_k` = (MC_INDI_K_R, MC_INDI_K_P, MC_INDI_K_Y) set at McIndiRateControl.cpp l.85. The lead on axis i
  uses K_i of that axis (yaw: K_Y).
- tau_c: the SAME variable as the actuator model, `_actuator_tc` (MC_INDI_ACT_TC, yaml l.102-112, default 0.02, range
  0.001-0.2, clamped in `setActuatorTimeConstant`), used in cpp l.257 for `_t_act`. No second time constant. Rationale:
  the lead cancels the physical actuator pole, the same quantity the model must match; one identified number.
  Consequence: the default 0.02 vs the plant 0.033 is a mismatch the lead inherits (S48: ACT_TC is a physical parameter,
  to be identified). A mismatch of tau_c vs tau leaves a residual (1+ s tau_c)/(1+ s tau) on L. UNVERIFIED how much PM that
  costs at +-40 percent; `lead_model_s48.py` should be run by the reviewer or in the closed-loop test (section 4).

### 1.3 Insertion points
- `indi_rate_control.cpp` l.378-382 (the `for` loop of step 8): replace `nu(i) - a_f(i)` by `nu(i) - (1.f + lead(i)) * a_f(i)`
  with `lead(i)` computed just before the loop (after l.373): `const float lead_i = landed ? 0.f : _lead_scale * _gain_k(i) * _actuator_tc;`.
- `indi_rate_control.hpp`: member `float _lead_scale{1.f}` next to `_blend_tc` (l.~236), setter
  `setLeadScale(float)` next to `setActuatorBlendTimeConstant` (non finite or < 0 -> 0, clamp to 1), getter
  `getLeadFeedback()` returning `K tau_c a_f` per axis for logging (optional, UNVERIFIED if the uORB status message has room).
- `McIndiRateControl.cpp` l.85-93 `parameters_updated()`: `_indi.setLeadScale(_param_mc_indi_lead.get());` plus the
  `DEFINE_PARAMETERS` entry and the yaml entry (section 3).
- `getNu()` (logging) stays K e, so existing log analysis of nu is unchanged. The lead enters only dt_cmd.
- Header comment block of the .hpp (control law, l.~38-42) must show the new nu line.

### 1.4 Max increment and bounds
The lead enlarges the a_f term, so for a given a_f the increment grows by (1 + c). `dt_cmd` is still clamped at
`_max_increment` (l.395) and `t_cmd` at +-1 (l.396); the lead adds no state, hence no wind-up path.

## 2. Interactions

(a) Measured-rotor-speed path and blend. The lead term depends only on a_f and K, never on t_f, `t_f_model`, `t_f_meas`
or `_blend`. Blend (l.320-340) removes a steady gap between command and output through t_f; at steady state a_f = 0 so the
lead is zero and the DC action of the blend is unchanged. During a constant angular acceleration (rate ramp) the lead
contributes a steady K tau_c a_f/G1 torque, which is feedback-only: the setpoint path keeps the actuator lag (closed loop K/((tau s + 1)(s + K))), the lead only reshapes the loop gain L. Matched in both sources
(t_f_meas = a_f/G1 when the model is right): t_cmd = (K e - K tau_c a_f)/G1 in either, so the loop shape is the same.
Mismatch case: with G1 or tau error, the disturbance estimate (a_f - G1 t_f)/G1 is unchanged, but the lead adds K tau_c
a_f/G1, which depends on the real a_f only. Whether the lead lowers GM when the measured path is in use (the real motor
lag is already visible in t_f_meas) is UNVERIFIED: no model of the measured path exists in S48. Needs a flight with
MC_INDI_W_MAX set and the blend on and off.

(b) Yaw. Denominator is G1_Y + G2_Y/dt (l.381), so the lead on yaw gives -c_Y a_f/(G1_Y + G2_Y/dt), attenuated at low
frequency relative to roll by the same factor that attenuates K_Y e (existing behaviour, not introduced here). UNVERIFIED:
whether the yaw lead then still cancels the actuator pole; the yaw plant a = G1 A t + G2 s A t is not first order in the
same sense, so the cancellation is approximate. Also a_f(2) is the yaw-LPF2p output when MC_INDI_YAW_CUT > 0, so the
lead phase lags (MC_INDI_YAW_CUT cutoff) and may be partly lost at crossover; G2_Y must be evaluated with the lead on and
off separately (hence the scale parameter, section 3). In the first implementation the lead applies to yaw like the
other axes, with c_Y = lead * K_Y * tau_c; if the yaw flight check fails, set a per-axis gate (open question Q3).

(c) Saturation, landed, resets. The lead has no state. Consequences:
- landed: step 7b holds t_fb to zero and `dt_cmd` is still computed from a_f (l.373, 396): amplifying a_f by (1+c) on the
  ground would raise vibration pickup into the landed output. Proposal: `lead_i = 0` when `landed`, so the landed output is
  bit-identical to the current law and existing landed tests (l.187, l.686, l.706) stay green. The step at liftoff is
  K tau_c a_f/G1, with a_f near zero, and bounded by `_max_increment`. UNVERIFIED that a_f on a running ground vehicle is small.
- saturation: if the allocator saturates, a_f stops following t_f; (1+c) a_f in the increment makes the corrective
  term larger by the same factor as the rest of the a_f feedback. The anti-wind-up test (l.157) must keep passing
  unmodified. UNVERIFIED if recovery after saturation overshoots more.
- reset / first sample / fault: `resetStates()` (l.134) and `reset()` (l.179) zero model states; a_f is an argument and is
  never stored (only `_a_f` for logging). First sample uses the a_f supplied, validated finite (l.218). The yaw filter
  restart (l.353-360) gives a_f(2) = input at reset. No new state, so no new reset line; `faultOutput()` holding the last
  output is unchanged. If `a_f` is huge but finite, `(1+c) a_f` can overflow only for absurd inputs, which l.386 catches.

(d) Filter matching. The lead cancels the actuator pole; the filter H (LPF2p 40 Hz, alpha 20-50 Hz) sits on a_f and on
t_f identically, so the cancellation a_f - G1 t_f stays matched (unchanged). The lead term itself, K tau_c H s, is not
canceled by anything, so H appears in L as L = K A (1 + tau_c H s)/s. At crossover 3-8 Hz H lags by a few to ten
degrees (alpha at 20 Hz: atan(8/20) = 22 deg at 8 Hz on the derivative term) and the lead gain falls above the filter
cutoff. S48 reports PM changes below 0.2 deg from filters in the matched case without the lead; with the lead this is
UNVERIFIED. Does `lead_model_s48.py` include H on the lead path? UNVERIFIED (asked in Q1). The delay samples
(MC_INDI_DELAY) apply to t_act only (l.260-272): a_f is not delayed, so with MC_INDI_DELAY > 0 the matched pair already
accounts for the sensor latency; the lead has the same latency as a_f. No new delay parameter is needed.

(e) Noise. In the matched case the motor command from a_f noise is (1 + K tau_c)/G1 times a_f, previously 1/G1: gain
factor 1.66 at K 20, tau 0.033 and 2.3 at K 40 (S48), 1.4 at K 20 with default tau 0.02. In words: the motor-command
noise that comes from the angular-acceleration estimate, normally the dominant noise source of INDI, rises by 1.4 to 2.3
times (3 to 7 dB) on the roll and pitch axes, 2x or so on yaw with K_Y 10-20 (UNVERIFIED, depends on the yaw LPF).
Noise from the rate error (K e, gyro rate noise) is unchanged. The noise rises mainly above the loop bandwidth, so it
hits ESC heating and motor audible noise before it hits control. G4 (motor-command noise limit, open in
STATE.md; definition in `GATES.md`, not re-read here, UNVERIFIED) is the check: with lead_scale 1 vs 0 on the same flight
and seed, the motor-command spectral power above 50 Hz and the rms of `actuator_motors` change must stay below the G4 limit
at the K that meets G2. DECISIONS D-RATE-LEAD "overturn if" already ties the decision to this.

## 3. Parameters

Recommendation: one new float parameter `MC_INDI_LEAD` (12 characters, group of the other MC_INDI_*), scale of the lead,
range 0..1, default 1, increment 0.05, decimals 2, unit none. `lead_i = MC_INDI_LEAD * K_i * MC_INDI_ACT_TC`.
- Why a scale and not a flag: 0 reproduces the current law exactly (bisect, A/B on the same airframe, and the noise
  trade-off in G4: a value below 1 partially cancels the pole and gives less noise); 1 is the model-derived value; flag
  only offers 0 or 1. Cost: one more number to explain; a value above 1 is excluded (over-lead, UNVERIFIED not modelled).
- Why default 1: owner direction (memory): no PID fallback, generic quad defaults, the law is the stage-3 design. A default 0
  would leave G2 unreachable by default (S48). Trade-off: default 1 changes the behaviour of every existing log and
  test using the defaults; existing unit tests that depend on the exact output (e.g. RateStepResponse l.110, the
  yaw tests l.282-333) must be updated or set `setLeadScale(0.f)` in `makeController()` and get dedicated lead tests.
  Recommendation: `makeController()` keeps lead 0 (old tests untouched), new tests set lead explicitly.
- Alternative: no parameter, tied permanently to ACT_TC. Rejected: no way to measure the benefit on the same build and
  no knob if G4 fails.
- ACT_TC default stays 0.02 (identification is a separate item), but the note recommends the identified 0.033 for the
  vehicle used in S47/S48, otherwise the lead is mismatched (see 1.2).
- Parameter yaml entry: short "INDI rate lead scale", long "Scale of the rate prediction lead K*MC_INDI_ACT_TC*angular_accel that cancels the actuator lag in the rate loop. 1 = full, 0 = off (previous law). Adds (1 + scale*K*ACT_TC) to the angular acceleration feedback gain, so raises motor command noise."
  Bounds min 0, max 1.
- Not exposed as a per-axis scale in this step (Q3).

## 4. Tests

Unit tests in `indi_rate_control_test.cpp` (helpers: `makeController()` l.82 with K 20, G1 100, ACT_TC 0.02, filters
40/20 Hz; `RollPlant` l.53; kDt 0.0025; `Vector3f` update() calls as in l.110):
1. LeadZeroIsBitIdentical: scale 0 vs a controller that never called `setLeadScale`: exactly equal outputs on a noisy
   multi-axis sequence. Fails if the term is not gated by the scale.
2. LeadAddsKTauAccel: single call, rate = rate_sp, a_f = 5 on roll, t_alloc 0, lead 1: t_cmd(0) = -(1 + K tau_c) 5/G1
   (floating tolerance). Fails on sign flip (would give -(1 - K tau_c) 5/G1) and if tau is ignored (1 + K only/ missing).
3. LeadUsesActuatorTc: repeat 2 with `setActuatorTimeConstant(0.05)`: expected -(1 + 20*0.05) 5/G1. Fails if tau_c is a
   hard-coded or separate value.
4. LeadPerAxisGain: a_f = (5, 5, 5), K = (20, 40, 10): each axis equals its own K_i: fails if applied with the wrong
   axis index or one gain used for all three. Also a_f only on pitch must leave the roll and yaw outputs unchanged.
5. LeadRateErrorUnchanged: a_f = 0, rate error 1: output equal to the scale 0 output (the lead does not touch K e).
6. LeadOffWhenLanded: landed true with a_f nonzero: output equal to the scale 0 output (bit-identical).
7. LeadYawWithSpinUp: G2_Y > 0, a_f on yaw only: t_cmd(2) = ((1 + c_Y) a_f term)/(G1_Y + G2/dt) as in the equation;
   fails if the lead is added outside the denominator.
8. LeadScaleInvalid: NaN, negative, > 1 -> setter clamps to 0 / 0 / 1; no fault.
9. LeadKeepsFaultHold: non finite a_f still holds the last output and sets the fault (l.203 test extended with lead 1).
10. Measured path: `MeasurementEqualToModel...` (l.850) with lead 1: still bumpless at the switch (a_f is the same input in both
    paths, so the output must not step beyond the existing tolerance).

Closed-loop test `LeadImprovesPhaseMargin` (uses `RollPlant` with kActuatorTc 0.033 and the matched ACT_TC, a pure delay
of 1 sample on the command, MC_ROLL_P equivalent P_att = 8 as an outer rate_sp = P (att_sp - att) loop, K = 20, kDt 0.00125
for 800 Hz; the plant needs a delay and a different tau than the file default, hence a new plant class `RollPlantLag`).
It breaks the loop numerically (small-signal sinusoidal injection at the command, as in the bench) at ~12 log-spaced
frequencies 0.5-30 Hz, computes L(jw) = ratio of the signals, finds crossover and the phase margin and gain margin, and
asserts: PM(lead 1) >= 50 deg; PM(lead 1) - PM(lead 0) >= 20 deg (S48 model: 28.6 -> 60.8 at K 20); GM(lead 1) >= 10 dB;
crossover of lead 1 within 30 percent of K/(2 pi). Also a step test: the rate step overshoot with lead 1 is lower than with
lead 0. Bounds are loose to a model-vs-sim difference (S48: 3 deg PM, GM 3.5 dB optimistic). If the discrete loop with
H does not reach PM 50 (see 2d), the assertions are what is wrong, not the test, and the reviewer decides.

## 5. Open questions for the reviewer
- Q1. Does `bench/lead_model_s48.py` put H (LPF2p + alpha) on the lead path (2d)? If not, the PM 56-61 deg of the summary is
  optimistic, UNVERIFIED by how much. Check against the L(jw) of the closed-loop test.
- Q2. The summary and the code agree on sign and structure (nu_eff = K e - K tau_c a_f, ACT_TC as tau_c), but the
  summary says "feedback gain (1 + K tau_c)" on a_f: confirmed in code as the coefficient on `a_f` in the numerator only if
  the (1 + c) multiplies the existing -a_f term; a lead applied as an extra term in `nu` (without the existing -a_f)
  would be the same number, so no contradiction found. UNVERIFIED that the S48 model includes the one-sample delay
  of t_act vs a_f.
- Q3. Yaw: the G2 denominator (G1 + G2/dt) and the yaw LPF make the yaw lead different (2b). Gate yaw lead off until a yaw flight
  check, or apply it? The note proposes apply, with MC_INDI_LEAD as the one switch. A per-axis scale would be a second
  parameter (MC_INDI_LEAD_Y).
- Q4. Landed gating (2c) and whether `getNu()` should include the lead for logs/analysis scripts that reconstruct the law
  from `indi_rate_status` (a script keyed to nu - a_f would be wrong with lead 1: UNVERIFIED which scripts).
- Q5. Measured path with the blend on: no model, no flight (2a). Is a flight check a precondition of the merge?
- Q6. Cap on c = lead K tau_c: K up to the parameter maximum and ACT_TC up to 0.2 s give c up to tens; nothing bounds the noise
  gain. Add a clamp (e.g. c <= 3) in the setter/update? UNVERIFIED what the K parameter maximum is (yaml l.69-100 not read).
- Q7. `dt_cmd` clamp at `_max_increment` (l.395) is applied after the lead; with a small MC_INDI_DT_MAX the lead can be
  clipped in a transient and the loop gain falls (nonlinear). UNVERIFIED how often it triggers in flight data.
- Q8. ACT_TC default (0.02) vs identified (0.033) (1.2): should the default change in the same commit? Separate decision.

## Orchestrator check (S49)
- Risk 1 (filter H on the lead path) is in the model: `bench/lead_model_s48.py` line 19 builds the lead as
  rt x tau_c x tf_alpha(D-term alpha) x discrete derivative, on the same gyro-filtered rate term rt. The PM 56-61 deg
  figures include H; they omit the unmodelled 3-5 ms loop delay (GM 2.3-3.5 dB optimistic, S48 flight checks).
- Before code: (1) opus review r1 of this note against `src/lib/indi_rate_control` (one interface); (2) identify ACT_TC
  from a rotor step (default 0.02 vs plant 0.033); (3) yaw and blend-on cases need a model row each before flight.
