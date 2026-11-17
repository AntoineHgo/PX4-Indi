# D-GAP review r1 (S71, independent reviewer)

Scope: `DECISIONS.md` `## D-GAP` (lines 416-431) vs `design/outer_loop_candidates_r3.md` A11, evidence
`results/stage5_s70/README.md`, and the code listed in `design/dgap_review_brief_s70.md`. Read-only review; nothing else modified.

Notation: T = normalised collective command (`out.thrust`), u_m = measured mean u = mean (omega/omega_max)^2, k = gap
(u_m = k P T at DC, P = motor lag), G = g/ht (`McIndiPosControl.cpp`, `G = kGravity / max(ht, 0.05)`, then
`setThrustModel(G, 1)`, so k_cmd = 1), H = matched LPF, D = sample delay, L = 1/(tb s + 1) the proposed blend.

## Q1. Steady z error, coll_model, units: OK (two text fixes, MINOR)
- What coll_model is in this module: NOT "commanded thrust through an actuator model". The library's model input is
  `u_in = _thrust_prev * _k_cmd` (`src/lib/indi_accel_control/indi_accel_control.cpp:265`), i.e. the previous clamped
  collective command (`:322`, `:345`), run through the same delay and LPF as mean_u. There is no motor-lag model in the
  outer loop (unlike the rate loop, `indi_rate_control.hpp:60-72`). Today model and measurement share ONE filter/delay
  path selected by `mean_u_valid`; (d) needs a second parallel path (as rate-loop step 5b,
  `indi_rate_control.cpp:296-329`). D-GAP must say so.
- Loop algebra (vertical, linearised, a_f = H D a, plant a = G u_m - g, INDI T = coll_f + (a_c - a_f)/G):
  coll_f = H D T [ (1 - L) k P + L ]  =>  T [1 - H D L (1 - k P)] = a_c / G  =>
  A(s) = a/a_c = k P / (1 - H D L (1 - k P)).
  L = 0 (today, measured): A(0) = k, standing a_c = (1 - k) G T, z error (1-k) g/(Z_P Z_VEL_P_ACC) = 0.368 m, as
  measured (README rows ii/ii-b). L(0) = 1 (blend): A(0) = k / (1 - 1 + k) = 1, so at DC a_f = a_c = a_ref.
  Through the chain a_ref = Kv (Kp e_z - v_z): a = 0, v = 0 => e_z = 0. This holds for any constant k, so for the
  4-motor scale 0.85 AND for one motor at 0.8 (mean k = 0.95; the extra 0.07 m measured over the 0.12 m P-only
  prediction is also integrated out, whatever its origin, unless it is a saturation, see Q3). Verdict: zero steady
  error, provided (i) b is not bounded below the largest gap (the rate loop bounds at kMaxBlend = 2,
  `indi_rate_control.hpp:303`; the collective bound must be stated in u units, e.g. >= 0.5 T_hover), (ii) the collective
  is not saturated, (iii) a_f is unbiased: with integral action on the accelerometer, a z accel bias beta leaves
  e_z = beta/(Kp Kv). Check that `_f_b` is the bias-corrected vehicle_acceleration (not verified here).
- Units: G T (model) and G u_m (measured) are the same quantity only if the actuator map gives u = T at hover
  (command-to-omega^2 identity, THR_MDL_FAC / rate-stack linearisation). Indirect check from the README (HTE frozen,
  G ~ g/0.140): G (T - u_f) = Kp Kv e = 4 x 0.372 => T - u_f = 0.021, u_f = 0.140 vs true 0.85 x 0.1608 = 0.137:
  units agree within ~2 %. With (d) a DC unit mismatch is SILENTLY absorbed by b (the model wins at DC); only the
  high-frequency increment gain (d u_m / d T) would be off. D-GAP should log b (u units) so a non-zero b at healthy
  hover flags a unit/map error instead of hiding it. Also: HTE-adapted G (ht -> T_hover/k) makes G u_m = k g biased
  while G T = g stays consistent, so the model path is the one consistent with HTE units (another argument for
  model-at-DC).

## Q2. Margin cost and tb bounds: MINOR (overturn criterion aims at the wrong frequency)
- Low frequency (P = H = D = 1 near 1/tb): A(s) = k (tb s + 1)/(tb s + k): a lag doublet, pole k/tb, zero 1/tb,
  DC 1, HF k. Maximum phase lag asin((1-k)/(1+k)) at omega = sqrt(k)/tb: 4.7 deg for k = 0.85, 1.5 deg for k = 0.95,
  19.5 deg only at k = 0.5. It is INDEPENDENT of tb, so the "< 45 deg phase margin" overturn (DECISIONS.md:429-430)
  essentially cannot fire: velocity loop Kv A(s)/s with Kv = 4 rad/s gives PM ~ 90 - 4.7 deg minus the other
  vertical lags. Not falsifiable as written.
- Real risk is high frequency. The model path has no motor lag (Q1), so with P = 1/(tau_m s + 1) and k = 1:
  A = P / (1 - H D L (1 - P)); with L = 1 this is 1/(1 + tau_m s (1 - H D)) ~ 1/(1 + tau_m (tau_H + d) s^2), a lightly
  damped mode at omega_r ~ 1/sqrt(tau_m (tau_H + d)) (order 30-50 rad/s for a 5" quad, numbers UNVERIFIED). The blend
  attenuates it by |L(j omega_r)| ~ 1/(tb omega_r). Lower bound: tb omega_r >> 1, say tb >= 5/omega_r (~0.1-0.2 s with
  the guessed numbers), which is the region where the stage-1 rate-loop blend failed at 0.1 s and was frozen at 0.3 s
  without a loop-gain measurement (LESSONS.md:38). Plausible common cause, not proven. Upper bound from "gap removed
  within 10 s": the slow closed-loop pole lies between k/tb and 1/tb, so 3 tb/k <= 10 s => tb <= ~2.5 s.
  Window roughly [0.3, 2.5] s.
- Required text change: overturn on (1) the measured acceleration-loop response (peak |A| or overshoot of a_f vs a_ref,
  or collective-channel loop gain) at the chosen tb AND at tb/3, and (2) G2 velocity-loop PM >= 45 deg from a sweep or
  step; keep "gap removed within 10 s". Optional: model the motor lag in the model path (u_mod = P_hat T), which removes
  the HF mode and relaxes the lower bound.

## Q3. HTE, bypass/landed, telemetry loss, saturation: BLOCKING (edge semantics unspecified; the cited mechanism does the opposite of A16)
- "One mechanism in both loops (rate: setActuatorBlendTimeConstant)" (DECISIONS.md:424) imports the rate-loop edge
  behaviour, `src/lib/indi_rate_control/indi_rate_control.cpp:336-345`: when landed, blend disabled or measurement not
  in use, `_blend = t_gap` (snap to the instantaneous gap); only maybe_landed freezes. In the collective channel:
  - Landed / bypass: snap = re-initialisation. A16 (`design/outer_loop_candidates_r4.md:30`) requires integrators
    frozen, not reset, across e7 and on open groups (and A3/A8 state bypass wins). On ground the idle gap is
    meaningless, so a snap re-learns from a wrong value after every takeoff (tb-long sag transient with the full gap).
  - Telemetry loss: in the rate loop the measured path is fed the model while invalid, so t_gap -> 0 and b -> 0; at
    recovery coll_f = coll_meas + 0 = pure measurement, i.e. the whole gap (0.37 m sag at k = 0.85) comes back and
    decays over ~tb. Must be: b frozen while mean_u is invalid, coll_f = coll_model (bumpless at DC since
    meas + b ~ model), and on recovery coll_f = meas + b_frozen.
  - Bypass edge: the module calls `_indi.reset(...)` on every bypass cycle (`McIndiPosControl.cpp`, bypass branch after
    `_indi.update`). If b lives in the library, reset() must not touch it. Airborne bypass: the gap stays observable
    (stock command vs mean_u), so continuing the LP (not snapping) is acceptable and arguably better than freezing;
    on ground: freeze. D-GAP must pick and state.
  - Saturation: the model path uses the clamped T (`indi_accel_control.cpp:322`), so INDI-level clamps do not wind b.
    Downstream saturation (allocator/airmode, a weak motor at 100 % in s5_loss08) is invisible to `_thrust_prev`: b then
    accumulates the saturation deficit as if it were a gap, and after desaturation coll_f overestimates thrust for ~tb
    (windup-like sag). Require: b frozen when T is at thr_min/thr_max or allocator status reports unallocated
    collective; b bounded in u units.
- HTE: OK. At DC coll_f -> T_prev and G cancels (t_c/G = u_f + (a_c - a_f)/G), so the z error no longer depends on the
  HTE estimate; HTE only sets the increment gain. No two-integrator fight on the same error (README: HTE on reduces the
  gap today only through G, 0.31 vs 0.37 m). Keep b in u units (not m/s^2) so G updates do not rescale it.
- Acceleration-only groups (A10/A15): (d) runs inside INDI, so it also removes the standing acceleration error there,
  which (c) cannot. D-GAP should state that b runs in those groups and freezes across e7.

## Q4. Alternatives: OK (choice of (d) justified), MINOR text
- (a) per-motor command-to-omega^2 correction: removes the same gap source (command -> omega; a k_f loss in
  omega^2 -> thrust leaves model and measurement equal and is already integrated out), corrects rate-loop torque
  effectiveness per motor and gives a motor-health signal (G3 diagnostics). But it needs per-motor estimators with
  their own freeze/saturation logic and per-airframe maps (worse for G6), and the rate loop already has its blend.
  Not clearly better for G3 or G6; keep as fallback as written.
- (c) stock MPC_*_VEL_I_ACC: most upstream-friendly (no new parameter, familiar tuning), but absent in
  acceleration-only groups (standing acceleration error, A10/A15) and conflicts with A2 (A16 freeze rule then applies).
  Acceptable upstream only as the stock path when INDI is off. D-GAP must state that with (d) on, the velocity
  integrators stay 0 (A2): (c) + (d) is two integrators on one error (less margin, overshoot), not allowed.

## Q5. What fails if the remedy is broken (lesson 20): missing from the text, MINOR
- Unit test (`src/lib/indi_accel_control/IndiAccelControlTest.cpp`, new case): closed loop on a point mass with
  u_m = 0.85 T (mean_u_valid), a_ref from Kp/Kv on z; assert |e_z| < 1 mm after 5 tb with the blend, and assert
  e_z = 0.15 g/(Kp Kv) +- 2 % with tb = 0 (negative control proves the test can fail). Edge cases in the same file:
  reset() keeps b; 50 invalid mean_u cycles then valid -> |delta T| < 1e-3 at recovery and no tb-long sag;
  T at thr_max -> b unchanged.
- Flight check: rerun `s5_gap085` with `gap_htoff.params` (HTE frozen, isolates the mechanism) and `s5_loss08`, scored
  by `bench/s5_gap_check.py`: last-10 s mean dz < 0.06 m (stock + integrator reference, row iv) versus 0.372 m today,
  hover pretest gate still PASS, and a land/re-takeoff showing no tb-long sag (freeze check). Mind the -0.8..-0.96 s
  event offset (README orchestrator note) if a transient is scored.

## Not verified
- Motor/filter/delay values for omega_r (tb lower bound is order-of-magnitude only). Whether `_f_b` is bias-corrected.
  The stage-1 0.1 s failure cause (LESSONS.md:38: unexplained). A2/A3/A8 text not read beyond A16.

VERDICT: BLOCKING

Changes required in the D-GAP text before implementation:
1. Specify b edge semantics instead of "one mechanism ... setActuatorBlendTimeConstant": freeze (not snap) on ground,
   at A3/A8 bypass and e7 edges (A16), reset() leaves b untouched; freeze while mean_u is invalid with
   coll_f = coll_model; freeze when T is clamped or the allocator reports collective saturation; bound b in u units.
2. State that coll_model = previous clamped collective command (no actuator model) and that a second delay/LPF path
   parallel to the measured one is added in `indi_accel_control`; b kept in u units and logged.
3. Replace the overturn criterion: the crossover phase cost is bounded by asin((1-k)/(1+k)), independent of tb; overturn
   on the measured acceleration-loop response at tb and tb/3 (HF mode from the missing motor model) plus G2 velocity PM
   >= 45 deg; state the tb window (~0.3 to ~2.5 s, upper bound from 10 s convergence).
4. State that MPC_*_VEL_I_ACC stay 0 with (d) and that (d) runs in acceleration-only groups.
5. Name the unit test (with tb = 0 negative control) and the flight check (gap_htoff + loss08, < 0.06 m, re-takeoff).
