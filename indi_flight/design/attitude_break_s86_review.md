# Review T185: attitude_break_s86.md vs firmware code

Reviewer read: note (all), McIndiRateControl.cpp 205-432, indi_rate_control.cpp 375-420, mc_att_control_main.cpp 360-392,
IndiRateStatus.msg, logged_topics.cpp, run_scenario.py LOG_TOPICS. Budget-limited (about 15 calls); nothing edited.

## 1. Injection point and signals

- OK: the rate setpoint enters only at McIndiRateControl.cpp:353-358 (topic) or 339 (ACRO), is zeroed at 381, and is consumed
  at one place, `_indi.update(rates, _rates_setpoint, ...)` at :231. No second subscription or feedforward of it in the module
  (grep of `_rates_setpoint` shows only 231, 339-358, 381). A local `rates_sp_applied` at :231 breaks the loop without touching
  mc_att_control / mc_rate_control. Reachable under O-11.
- MINOR: the lead path inside the lib (indi_rate_control.cpp:387-404) differentiates the ZOH staircase of y (steps at the att
  rate, 1 ms-class LPF Tc 0.01 s, clamp 1000). The note covers this as "inside the cut", but the staircase makes the lead
  term spiky at the att update instants; this is a model item for section 5 (sp_lead), not a break defect.
- MINOR: the note's x is "y + d" built in the module, while y is `_rates_setpoint` AFTER the watchdog (:381) and AFTER the
  non-finite substitution with `rates(i)` (:354-356). The substitution case makes y differ from the topic; the 1e-6 check
  against `vehicle_rates_setpoint` (note section 2) would flag it, fine, but say so.
- MINOR: ACRO branch (:339) is also a rate-setpoint source; the note gates only on stale. The break is meaningless there;
  add `flag_control_attitude_enabled` to the gate.

## 2. L_att identity

- Note section 5: L_att = A/(1+L_rate), 1+L_M3a = (1+L_rate)(1+L_att). Algebraically consistent (L_M3a = L_rate + A), and
  L = -y/x gives the right sign for x = y + d.
- MINOR (wording): the "expected" form A*T_rate with T = L_rate/(1+L_rate) is NOT what the note uses and would be wrong
  here: the setpoint path gain is (K + lead) Pn, not the feedback gain, so setpoint->rate is (K+lead)Pn/(1+L_rate), not T_rate.
  The note's A carries (K+lead) Pn so it is right, but it calls the factor "closed rate loop from rate setpoint to rate";
  state explicitly that it is not L/(1+L). Pn scaling left UNVERIFIED by the note: must be closed before the model is a gate.

## 3. PID reference

- Not possible without editing mc_rate_control: confirmed (no injector there). The note proposes the stock autotune hook at
  mc_att_control_main.cpp:371-379 (verified: adds `_pid_autotune.rate_sp` to rates_sp before publishing, if status is
  ROLL/PITCH/YAW/TEST and < 1 s old). It is honest: state-machine signal, not a periodic multisine, y not logged, so the
  frf_periodic estimator cannot use it; recommends model-only cell. Accurate.
- MINOR (missed option): the same hook works for the INDI stack with zero module change, so it gives an independent check of the
  new INDI-side injector; and a bench-only publisher of `autotune_attitude_control_status` with our multisine would give a
  measured PID break with no stock diff (note leaves it as open question 4, which is right). Note that with this hook d is
  inside `vehicle_rates_setpoint` so x is logged but y = x - d needs d from the publisher: log it.

## 4. Logging

- OK: new fields in indi_rate_status (published once per rate cycle, :245-263) at logger interval 0 in the bench
  (run_scenario.py:86) and no interval in the profile (logged_topics.cpp:90). `timestamp_sample` is the gyro sample time
  (:246), same base as the existing torque inject fields. Rate is the controller rate.
- MINOR: logged_topics.cpp:159 logs vehicle_rates_setpoint at 20 ms and :329 without interval (other profile); the second-source
  check in note section 2 must state which profile/interval, otherwise the 1e-6 join fails by sampling, not by a bug.
- MINOR: msg growth (3 x float32[3]) at 800 Hz: note flags UNVERIFIED (open question 6); needs a size/drop check in
  the first flight.

## 5. Tests (section 6)

- MAJOR: the pure-function tests (OnlyTheSelectedAxis, SignAndPoint, Gating, Waveform) test the helper, not the call site. The
  real failure modes are in `runIndiRateControl`: passing `_rates_setpoint` instead of `rates_sp_applied` to `_indi.update`
  (:231), or applying d after the update. None of the listed unit tests fails for that. The "lib-level" test (update(sp+d)
  equals update(sp+d)) is a tautology about the library and cannot fail when the injector is broken.
- MAJOR: the runtime check `max |x - y - d| <= 1e-6` is computed from the same logged variables the module fills, so it cannot
  detect that the INDI law received something other than x. Add a check that uses an independent logged quantity that depends
  on what `_indi.update` really got: `rate_sp_dot` (already logged, :255) must equal the filtered derivative of the logged x
  (reproduce with Tc 0.01 s), and the logged `torque_sp_pre_inject` must respond to x. That fails if the injection is not
  fed to the law or is applied after it.
- MINOR: Python self-test with swapped x/y fails on sign: good. AX = 0 bit-identical check: good (needs a real log diff, not
  only "fields zero").
- MINOR: pre-test window DLY 20 + NP 5 x Tp 10 = 70 s vs hover_long 60 s: the note flags it UNVERIFIED; resolve before flying.

## 6. Other

- MINOR: new param MC_INDI_INJ_RAMP separate from AMP (max 0.2 normalised torque, yaml ~:239-241) is the right call; also make
  AMP ignored (or logged) when PT = 1 so a stale file cannot be misread.
- MINOR: outer position loop stays closed (note admits, below ~0.3 Hz); compare with PINJ, which opens the outer loop. Gate
  wording decision is open question 2.

Counts: BLOCKING 0, MAJOR 2, MINOR 10.

VERDICT: no blocking defect; the break point is reachable inside mc_indi_rate_control and the identity is correct, but fix the two test gaps (call-site wiring test, independent rate_sp_dot check) before the second key.
