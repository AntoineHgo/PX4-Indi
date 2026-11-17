# D-YAW-INV option (c) review r1 (note vs code, before implementation)

Verdict: NOT BLOCKING. The law is correct and safe to code provided the MAJOR items below are written into the spec and the unit tests.

Scope read: DECISIONS.md D-YAW-INV (299-322), indi_rate_control.cpp 100-422, indi_rate_control.hpp, bench/yaw_break_model_s54.py
loops(), results/stage3_s55/yaw_model/README.md, mc_indi_rate_control_params.yaml defaults. No code run.

## A. Math
Backward Euler s -> (1 - z^-1)/dt on (G1 + G2 s) Delta = nu - (1+c) a_f gives (G1 + G2/dt) Delta_k - (G2/dt) Delta_k-1
= nu - (1+c) a_f, i.e. exactly the proposed recursion. Pole p = (G2/dt)/(G1 + G2/dt) lies in [0, 1) for G1 >= kMinG1, G2 >= 0
and any dt in [kMinDt, kMaxDt]: always stable, DC gain 1/G1, time constant G2/G1 (27/205 = 0.13 s in the model), all
independent of dt. The model "lpf" branch (yaw_break_model_s54.py:27-29) is the same law: D = G1 + G2(1 - z^-1)/dt, numerator
nu - (1+c) H alpha with c = lead K tau_m (same as cpp:384), own = H Am (no t_f difference term). The model is linear: no
clamps, no landed, constant dt, no source switch; items 1-4 below are outside what it checked.
Wording: DECISIONS.md:301 "G1 + G2/dt (21600 + 205)" lists G2/dt first (G1 = 205, G2/dt = 21600); swap for clarity.

## Findings
1. MAJOR - define Delta_k-1 as the applied yaw increment, not the raw one and not a reconstruction from t_cmd and t_f.
   Evidence: cpp:404-405 clamps dt_cmd to +-_max_increment and t_cmd to [-1, 1]; the Smeur derivation's previous term is
   u_k-1 - u_f,k-1. Fix: new state `float _yaw_inc_prev` (hpp, replaces `_t_f_prev` at hpp:327), set after step 9 to
   t_cmd(2) - t_fb(2) (the increment that actually reached the output, = back-calculation anti-windup). Storing the raw
   value lets the state sit beyond the clamp and adds up to G2/G1 (0.13 s) of lag after an output clamp. Do NOT store
   t_cmd and recompute t_cmd_k-1 - t_f,k: a model/measurement switch (cpp:339-341, no blend) would then enter the state.
   Write the state only after the isAllFinite check (cpp:395) so a fault cycle never stores NaN.
2. MAJOR - landed/maybe_landed (module passes `_maybe_landed || _landed`, McIndiRateControl.cpp:336). With the state running
   on ground, t_fb = 0 (cpp:374) and the yaw output converges to K_Y e/G1_Y (G1_Y default 30: 0.33 per rad/s of yaw error)
   instead of today's ~nu/(G1 + G2/dt) ~ 0; at takeoff t_fb jumps to t_f (~ that landed output) while the state still holds
   it, so t_cmd(2) ~ 2x the landed output (same double count roll already has, but yaw G1 is small). Fix: while landed,
   force `_yaw_inc_prev = 0` after the step (ground yaw = (nu - a_f)/(G1 + G2/dt), as today minus the t_f term), so flight
   starts from Delta_k-1 = 0. Unit test: ground yaw stick output and first in-flight cycle, G2 = 27, G1 = 205.
3. MAJOR - parameter documentation now contradicts the law. Evidence: mc_indi_rate_control_params.yaml:62 says G2_Y should
   be ~G1_Y x loop period (0.02) and larger values "remove yaw rate feedback" (coded-law statement). Under option (c) G2_Y is
   G1_Y x the spin-up time constant (model 27 with G1 205) and large values only slow the increment. Fix: rewrite the
   description, state that under-estimating G2 is benign and over-estimating is the weak side (S55 finding 3); update
   hpp:54-55 law comment and hpp:327.
4. MAJOR - reset paths: resetStates() (cpp:~175, replaces `_t_f_prev.zero()`) must zero `_yaw_inc_prev`; it is reached by
   reset(), faultOutput(true) and the hold expiry (cpp:192-207). Rejected cycles (cpp:222-227) must leave it untouched, as
   today for _t_f_prev. A filter redesign (cpp:240-247) needs no action (state is in torque units). Add a test: fault hold
   then recovery with G2 > 0 gives no output step beyond max_increment.
5. MINOR - dt jitter: use the same dt for both G2/dt terms in one cycle (as cpp:388 does); the variable-step BE form is
   then exact and stable. Invalid dt is already rejected before step 8 (cpp:218-226). No further action.
6. MINOR - G2_Y / G1_Y change in flight: state is a torque, so no bump; G2 -> 0 steps the output from the low-passed
   increment to e/G1, bounded by max_increment (default 1.0, yaml:169, i.e. effectively unbounded). Acceptable; test once.
7. MINOR - telemetry loss / source switch: option (c) is better than the coded law. Coded: a t_f jump J from a model <->
   measurement switch enters (G2/dt)(t_f - t_f_prev)/(G1 + G2/dt) ~ 0.99 J, so t_cmd jumps ~2J. Option (c): J only, as
   roll/pitch. Holds only with finding 1's definition.
8. MINOR - allocator saturation: t_f follows torque_allocated_prev (cpp:255), so the INDI integration is anti-windup as
   today; the Delta state is a bounded low pass (|Delta| <= |nu - (1+c) a_f|/G1 + clamp), no integrator windup.
9. MINOR - logging semantics: torque_increment(2) (cpp:419, module:225) becomes a persistent offset t_cmd - t_f (as roll),
   no longer a per-cycle step. Update the yaw spin-up unit test reading getTorqueIncrement()(2) (indi_rate_control_test.cpp:453)
   and any log scripts that assume the old meaning.

## C. Lead and _t_f_prev
_t_f_prev is used only at cpp:389 (term), cpp:393 (store), cpp:175 (reset), hpp:55/327 (comments); test names t_f_prev at
test.cpp:363/1216 are local variables. Nothing else depends on it: remove it. The lead (cpp:381-385) stays in the numerator
with (1+c), as in the model (c = lead K tau_m). Note: under the coded law the yaw lead was weighted ~G1/(G1 + G2/dt) ~ 1/105;
under option (c) it becomes fully effective on yaw (c_Y = 1 x 10 x 0.05 = 0.5 at defaults), so yaw now depends on ACT_TC and
LEAD like roll. The model includes this (lead = 1.0). Default ACT_TC 0.05 (yaml:110) >= plant 0.033: inside the tolerance.

## D. Defaults and modes
Default G2_Y = 0 (yaml:64): option (c) then reduces to Delta = (nu - (1+c) a_f)/G1, identical to the coded law; the change
only acts when G2_Y is set. All modes go through the same update(); landed/maybe_landed is the only mode-dependent branch
(finding 2). Unverified: Ms at ACT_TC between x0.5 and x1 of plant tau (S55 grid has x0.5 and x1 only); G2 x0.5..2 with
tau_m x0.5 reaches GM 0.6 dB (S55 finding 3), so the overturn rule depends on the tau tolerance being respected.
