# Review r1: rate_lead_note.md against src/lib/indi_rate_control (one interface)

Reviewer: independent (opus), read-only except this file.
Files read: `indi_flight/design/rate_lead_note.md`, `src/lib/indi_rate_control/indi_rate_control.cpp` (412 l.),
`indi_rate_control.hpp` (326 l.), `src/modules/mc_indi_rate_control/McIndiRateControl.cpp` l.182-221 plus a grep.
Numbers marked [calc] come from a continuous-time rate-loop-only model (no attitude loop, no ZOH, no discrete
derivative): plant G1 A_p e^{-sTd}/s, A = 1/(tau s+1), H = LPF2p 40 Hz x first order 20 Hz, Td = 1.25 ms (one sample
at 800 Hz) or 5.25 ms (plus 4 ms unmodelled). They show trends, not the S48 absolute figures, which include the
attitude loop.

## Derivation check (item 1)

Loop broken at the plant input u, as the bench does it: McIndiRateControl.cpp l.212-213 publishes u = c + d and stores it
as `_prev_torque_setpoint`, which becomes `torque_allocated_prev` (l.186-190), so the model t_act (cpp l.254-258) is
driven by u, not by the controller output c. With the code's law (cpp l.373, 380-381, 396) and the lead
num = nu - (1+c) a_f, a_f = H s w, s w = G1 D_p A_p u, t_f = H D_m A_m u:

    L_u(s) = D_p A_p (K + c H s)/s  +  H (D_p A_p - D_m A_m)

The first term is the note's L = K A (1 + tau_c H s)/s (note l.24-25, l.91); it is K/s for tau_c = tau and H = 1. The
second term is the pre-existing model mismatch residual; it does not depend on c. So for roll/pitch the note's
equation is right at this interface, including H on the lead path (the lead uses the same local `a_f`, cpp l.348,
l.380). "No new state" holds: the only addition is a parameter member; the optional `getLeadFeedback()` needs a stored
logging vector like `_a_f` (hpp l.319), which is not dynamic state. The z^-1 of `torque_allocated_prev` is in D_m, and
the gyro response to u_{k-1} is in D_p, so the note's Q2 one-sample question is a property of both members, not of the
lead.

## Findings

### F1 - MAJOR - The lead does not cancel the actuator lag in the reference path; tracking lag grows by tau_c
- Claim: note l.24-25 ("L = K/s") and l.60-61 ("steady K tau_c a_f/G1 torque, the intended prediction offset, not a
  gap") suggest the rate loop becomes K/(s+K). The lead acts on the measured rate only (nu - (1+c) a_f, cpp l.380),
  not on the setpoint. Matched, H = 1, tau_c = tau: w/r = K A/(s + K) = K/((tau s + 1)(s + K)) with lead, versus
  K/(tau s^2 + s + K) without. The actuator pole is removed from the loop (margins) but stays in the reference
  response. Steady rate-ramp error: R/K without lead, (1 + K tau_c) R/K = R (1/K + tau_c) with lead (x1.66 at K 20,
  tau 0.033). From the law: steady t_cmd = t_f gives K e = (1+c) a_f.
- Evidence: cpp l.368 (nu = K e only), l.380; [calc] rate-loop phase lag at 2 Hz: K 20 56 -> 72 ms, K 40 28 -> 52 ms;
  |T(2 Hz)| 1.04 -> 0.77 (K 20).
- Fix: write T(s) in the note next to L(s); the closed-loop test must also assert the tracking cost (ramp error,
  lag at 1-2 Hz), not only overshoot; check G2 against T, not L. If the lag is not acceptable, the 2-DOF variant
  nu = K e + K tau_c (d rate_sp/dt - a_f) restores it but needs a setpoint derivative (new state, impulse on
  setpoint steps, clipped by max_inc l.395): a separate decision.

### F2 - MAJOR - Gain margin falls strongly with the lead; the GM >= 10 dB test assertion is not safe at K 40 or with over-estimated tau_c
- Claim: note 2d discusses PM only; at high frequency |L| goes from K/(tau w^2) (no lead) to c|H|/(tau w) (lead), so GM
  drops. Over-estimating tau_c (ACT_TC > plant) is the dangerous direction for GM; under-estimating costs PM.
- Evidence [calc, H on, Td 1.25 / 5.25 ms]: K 20 matched: GM 32 -> 18 / 20 -> 14 dB, PM 59 -> 82 / 55 -> 76.
  K 40 matched: GM 26 -> 12 / 14 -> 7.7 dB. K 40 tau_c +40 % (0.046 vs 0.033): GM 8.8 / 5.0 dB, PM 54 / 39.
  K 20 tau_c 0.02 (default) vs plant 0.033: PM 62 / 57, GM 12 / 9.8. H on the lead path costs about 7 deg PM but
  12-18 dB GM (answers note Q1 partially: H matters mainly for GM). Crossover with lead and H is 13 % (K 20) to 19 %
  (K 40) above K/(2 pi); 61 % above at K 40 tau_c +40 %.
- Fix: in the note replace "UNVERIFIED how much PM that costs at +-40 percent" (l.38-39) with a GM and PM table over
  tau_c error and delay; keep the test's GM bound but state the K and delay it is valid for; add a cap on c (F8);
  identify ACT_TC before flight with lead 1 (note l.184 item 2 is a precondition, not optional).

### F3 - MAJOR - Yaw: the pole cancellation does not hold when G2 > 0
- Claim: with P = G1 + G2'(1 - z^-1), G2' = G2/dt, Dn = G1 + G2' (cpp l.379-381), the same derivation gives
  L_yaw = [K P A/s + c H P A - G2' H A]/Dn (matched, no delay). The lead's share relative to the K term is
  tau_c H s, as on roll (note l.68-69 "same factor" is right), but the existing -G2' H A/Dn term is untouched by the
  lead and keeps the actuator pole. The fraction left uncancelled is G2'/Dn = G2/(G1 dt + G2), which is large at
  800 Hz-1 kHz for any non-trivial G2. Also note l.71-72 is misleading: the yaw LPF filters a_f(2), t_f(2) and
  rate_error(2) together (cpp l.362-364), so the lead lags exactly as K e does; the yaw LPF does not specifically
  "lose" the lead.
- Evidence: cpp l.362-364, l.379-381.
- Fix: before applying the lead to yaw by default, add the yaw model row (note l.185 item 3) with this L_yaw; until
  then either gate the yaw lead to 0 when G2 > 0 or make test 7 (note l.142) also check the loop benefit, not only
  the formula. Decide Q3 on the model row.

### F4 - MINOR - Measured path (resolves note 2a UNVERIFIED): the lead does not interact with the t_f source
- Claim: from L_u above, the c term never contains t_f; the path choice only changes the c-independent residual
  H (D_p A_p - D_m A_m). With the measured path, A_m -> A_p (if delay and H match, cpp l.284-309), so the residual
  vanishes and the loop is D_p A_p (K + c H s)/s. [calc] K 20, ACT_TC 0.02 vs plant 0.033, lead 1: model path PM 62
  GM 12.3 dB; measured path PM 74.5 GM 21 dB. So the measured path does not lower GM, it removes the model error.
  Missing in the note: a G1 error ratio r = G1_true/G1 turns the a_f coefficient into r(1+c) - 1, i.e. an effective
  lead c_eff = r c + (r - 1): r = 1.2, c = 0.66 gives c_eff = 0.99 (+50 %), which pushes toward the F2 over-lead side.
- Fix: replace the UNVERIFIED in 2a by this derivation; keep a blend-on flight check; add the G1 sensitivity line.

### F5 - MINOR - Insertion snippet is inconsistent
- Claim: note l.42-43 computes a scalar `const float lead_i` "before the loop" but uses `lead(i)` per axis inside it.
- Evidence: cpp l.378-381.
- Fix: compute `const float lead = landed ? 0.f : _lead_scale * _gain_k(i) * _actuator_tc;` inside the loop, or a
  Vector3f before it.

### F6 - MINOR - Landed gating: toggles with maybe_landed; the takeoff step is only partly bounded
- Claim: `landed` is `_maybe_landed || _landed` (McIndiRateControl.cpp l.334), so c switches 0 <-> c on every
  maybe_landed toggle, stepping t_cmd by c a_f/G1 (inside the dt_cmd clamp, cpp l.395: bounded, e.g. 0.066 at c 0.66,
  a_f 10 rad/s^2, G1 100). The note's "bounded by _max_increment" (l.80) is true for the lead part; the larger
  existing step t_fb 0 -> t_f at liftoff (cpp l.373, l.396) is NOT bounded by max_inc, contrary to the comment
  cpp l.371-372 (pre-existing, not introduced here).
- Fix: keep the hard gate (bit-identical landed output is worth it), add a test toggling `landed` with a_f != 0 that
  checks the step is <= max_inc; optionally fix the l.371-372 comment.

### F7 - MINOR - Saturation, clamp, steady state, dt jitter, parameter changes: note claims confirmed, with caveats
- No wind-up: confirmed; t_fb comes from `torque_allocated_prev` minus unallocated torque (McIndi l.186-190), so the
  model follows achieved torque, and the lead has no state (cpp l.380).
- Clamp: the lead shares the max_inc budget (cpp l.395) with K e; with noise x(1+c), symmetric clipping of a noisy
  dt_cmd with nonzero mean reduces its mean (gain loss in transients, no bias at zero mean). Q7 stands.
- Steady state: a_f is a derivative of the filtered gyro, so gyro bias drops out; at constant body rate (hover,
  steady turn) a_f -> 0 and the command/trim is unchanged. Not true during ramps (F1).
- dt jitter: c = K tau_c is dimensionless and dt-free; on yaw the lead is divided by the jittering G1 + G2/dt like
  every other term (pre-existing).
- In-flight change of MC_INDI_LEAD, MC_INDI_K_* or MC_INDI_ACT_TC steps the output by delta_c a_f/G1, bounded by
  max_inc; small at a_f ~ 0. Note it in 2c.

### F8 - MINOR - c is unbounded (note Q6 verified)
- Claim: `setGainK` stores any value (hpp l.94), `paramsValid` checks only >= 0 and finite (cpp l.73), ACT_TC up to
  0.2 (cpp l.49), so c up to 0.2 K. F2 shows GM falls with c.
- Fix: clamp c (e.g. <= 2, i.e. above K 40 x tau 0.05) in update() or the setter, with a test.

### F9 - MINOR - Closed-loop unit test must close through u like the bench
- Claim: the test (note l.149-157) must feed the injected u (not the controller output) as `torque_allocated_prev`,
  as McIndiRateControl.cpp l.212-213 does; otherwise the measured "L" is a different transfer (the model loop
  1/(1 - H D_m A_m) enters) and the PM/GM assertions do not compare with the bench or S48.
- Fix: state it in the test spec.

### F10 - MINOR - Logging/analysis
- `getNu()` stays K e (note l.49) but `indi_rate_status` logs nu, a_f and dt_cmd (McIndi l.220-221); any script
  reconstructing dt_cmd = (nu - a_f)/G1 will disagree by c a_f/G1 when the lead is on. Log the lead scale or the lead
  term, or note it in the analysis scripts (Q4).

VERDICT: NOT BLOCKING

## Disposition (orchestrator, S51)
- F1 ACCEPTED as a property, not a defect: the lead is feedback-only, so the setpoint path keeps the actuator lag
  (closed loop K/((tau s+1)(s+K)), real poles, vs the lightly damped K/(tau s^2+s+K) today). Note section on
  "not a gap" to be corrected at implementation. Optional later increment: setpoint feedforward K tau_c d(rate_sp)/dt
  (noise of the attitude-loop derivative to be checked); tracking is judged in G3/G5, not here.
- F2 ACCEPTED, changes the plan: the closed-loop unit test and the first flights sweep ACT_TC error -40/0/+40 %
  at K_R 20; if GM < 6 dB at +40 % (overestimated tau_c), the default MC_INDI_LEAD drops below 1 (candidate 0.7) or
  the identification procedure (stage 4) must bound tau_c from below. Flight data S49 at K20/400 Hz: GM 10.5 dB.
- F3 ACCEPTED: yaw lead leaves the G2 path lag; yaw margins measured separately before yaw lead is on by default.
- F5, F8, F9, F10 to be applied in the implementation brief (per-axis vector, cap c <= 2, test feeds back the
  command as torque_allocated_prev, log scripts aware of the lead term).
- F6 is a pre-existing defect (take-off jump 0 -> t_f not limited by max_inc; maybe_landed toggles): goes to the
  stage-3 landed-handling item (review section 4), not to this change.
- F4: no action.
