# Second key S39: M3a injection vs D-G2-BREAK/D-G2-INJ

Scope: commit f44674b399 (HEAD~3, "bench loop-break excitation"); src/modules/mc_indi_rate_control/IndiInjection.cpp and .hpp as they are now; the McIndiRateControl.cpp call sites at HEAD; indi_flight/bench/margins_est.py log_bins() and multisine(); DECISIONS.md entries D-G2-BREAK (line 191) and D-G2-INJ (line 204). Line numbers for McIndiRateControl.cpp are HEAD line numbers.

## 1. u = c + d goes to the publish and to the stored previous setpoint
VERIFIED. u is formed at McIndiRateControl.cpp:213 (`torque_setpoint = torque_setpoint_pre_inject + inject`). It is published at :342-344 (non-finite components replaced by 0) and stored at :354 (`_prev_torque_setpoint = Vector3f(vehicle_torque_setpoint.xyz)`), so the stored value equals u whenever u is finite.
Doc nit: D-G2-BREAK cites `McIndiRateControl.cpp:329` and `:331`. At HEAD these lines are :342-344 and :354 (the references predate the commit).

## 2. AX = 0 gives u bit-identical to c
DEVIATION (trivial, sign of zero only). With AX = 0, `_injection.axis()` returns -1 (IndiInjection.hpp:65), the update call is skipped (McIndiRateControl.cpp:206-210), and d is never computed (`inject` stays zero). setParameters leaves `_num = 0` (IndiInjection.cpp:61-62). u = c + (+0.0f) equals c for every c except c = -0.0f, which becomes +0.0f. The value is identical; only the sign bit of a zero differs.

## 3. d = 0 gating
VERIFIED.
- Disarmed: IndiInjection.cpp:113-116 (also clears the origin, :114).
- Landed: the caller passes `_maybe_landed || _landed` (McIndiRateControl.cpp:334); checked at IndiInjection.cpp:118-120.
- Before origin + MC_INDI_INJ_DLY: the origin is `first cycle timestamp + delay` (:122-125); zero for timestamp < origin (:127-129).
- After NP*Tp: zero for t >= NP*Tp (:131-135).
Caveat: the clock does not pause while landed (see 6b).

## 4. Frequency bins and phases
VERIFIED, bins:
- Same count: margins_est.py:32 `ceil(log10(fmax/fmin)*10)+1` equals IndiInjection.cpp:68.
- Same grid: f_i = fmin * 10^(i/10) (margins_est.py:33; IndiInjection.cpp:72).
- Same uniqueness: np.unique (margins_est.py:34) equals the `k == last_k` skip (cpp:76), valid because k is non-decreasing in i.
- Same bounds: k >= 1 and k*df <= fmax*(1+0.5*df/fmax) (margins_est.py:35) equals `k*df > fmax + 0.5*df` (cpp:76). The two are algebraically identical.
- Cap: `_num < MAX_COMPONENTS` (cpp:71) is not reached at the defaults or pre-test values (see 6d).

Rounding tie check (python, run for this review): over every grid point, min |frac(f/df) - 0.5| = 0.0107 for both (Tp 20, fmin 0.5, fmax 60) and (Tp 10, fmin 1, fmax 60). No bin lands on .5, so numpy round-half-even versus C round-half-away does not matter. Emulating both rounding modes gives identical bin lists: defaults give 21 bins [10, 13, 16, 20, 25, 32, 40, 50, 63, 79, 100, 126, 158, 200, 251, 316, 398, 501, 631, 794, 1000]; pre-test gives 18 bins [10 ... 501].

VERIFIED, phases: with equal amplitudes, p_l = 1/K, margins_est.py:47-49 gives phi_k = -2*pi*sum_{l<k}(k-l)/K. IndiInjection.cpp:84-93 computes the same with 0-based k, and both use ascending frequency order.
Doc nit: margins_est.py:48 says "= -pi k(k-1)/K", which is the 1-based form. With 0-based k the formula gives -pi k(k+1)/K, which is the correct Schroeder phase for 0-based indices. The code is right; the comment is off by one index base.

## 5. Time origin and logged fields
VERIFIED. The clock is `angular_velocity.timestamp_sample`, passed at McIndiRateControl.cpp:335, into runIndiRateControl (:183) and then `_injection.update(timestamp_sample, ...)` (:209). indi_rate_status gets timestamp_sample (:216), c (:217), d (:218) and u (:219) on every cycle that reaches runIndiRateControl (the flag_control_rates_enabled branch). Not re-read here: the publish call of indi_rate_status after :224, and the logger interval 0 claim in D-G2-INJ.

## 6. Other issues that could make a margin measurement wrong
a. Rejected cycles open the loop at c. On invalid inputs IndiRateControl returns the held `_t_cmd_last` (src/lib/indi_rate_control/indi_rate_control.hpp:314; documented at :203) and sets fault (:324, logged at McIndiRateControl.cpp:224). On those cycles c does not depend on u, so the u-break is open. This contradicts D-G2-BREAK's "every feedback path closes through u". Fault cycles must be excluded from the estimate.
b. Landed gating does not pause the schedule. `_maybe_landed || _landed` (McIndiRateControl.cpp:334) zeros d while the clock keeps running (IndiInjection.cpp:118-120; `_started` is not cleared). A maybe_landed flicker in flight leaves zero holes inside the NP*Tp window, so the logged record is not the periodic multisine the estimator assumes. The estimator should reject windows that contain zero-d gaps.
c. A mid-flight parameter change restarts the origin. setParameters clears `_started` (IndiInjection.cpp:58) when any of the seven values changes bitwise (:44-49). parameters_updated runs on each parameter update (McIndiRateControl.cpp:244-250), but the early return keeps unrelated parameter changes harmless. Changing AMP, TP, FMIN, FMAX, NP or DLY in flight starts a second schedule at the next airborne cycle plus DLY, and nothing in indi_rate_status marks it. Disarm and re-arm also restart it (:113-116). lag_check (margins_est.py:78-90) catches this only against a regenerated reference. Recommend logging the origin or forbidding in-flight changes.
d. MAX_COMPONENTS is not triggered. The count is at most ceil(10*log10(fmax/fmin))+1, which is at most 64 unless fmax/fmin exceeds about 1e6. Defaults give 21 bins and pre-test gives 18. If it were triggered, the loop (cpp:71) keeps the lowest 64 and drops the highest, as the header says (IndiInjection.hpp:49). Python log_bins has no cap, so lag_check would fail rather than fail silently.
e. Precision. t = double(uint64 microsecond difference) * 1e-6 (cpp:131) is exact for any flight length. The cosine argument stays below about 2.3e5 rad at 600 s and 60 Hz, so its double error is around 1e-11 rad. Negligible. However, `_period` and `_f_min` are float32, and df = 1/(double)period uses the float value. Tp = 10 and 20 are exact. A non-exact Tp such as 12.3 shifts the grid by about 6e-8 relative to python's float64, which at 60 Hz over 600 s is about 0.01 rad of phase drift, enough to break the reference comparison. The delay conversion `(uint64_t)(_delay*1e6f)` is accurate to about 1 us below 16 s.
f. Not verified: the sign and mapping of the estimator's signals. margins_est needs y = c (torque_sp_pre_inject, cpp:217) and x = u (torque_sp, cpp:219). The CSV producer was not in the read set, so this mapping is unconfirmed.
g. Doc only: the D-G2-BREAK line references are stale (see 1).

## Verdict
AGREE-WITH-ISSUES
