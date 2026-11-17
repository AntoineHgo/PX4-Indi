# D-YAW-INV option (c) implementation (S56)

Files changed (not committed):
- src/lib/indi_rate_control/indi_rate_control.cpp: step 8 yaw law Delta_k = (nu - (1+c)a_f + (G2/dt) Delta_k-1)/(G1 + G2/dt); `_yaw_inc_prev` stored after step 9 and the isAllFinite check as t_cmd(2)-t_fb(2), forced 0 when landed; resetStates() zeroes it; rejected cycles leave it alone; `_t_f_prev` removed.
- src/lib/indi_rate_control/indi_rate_control.hpp: law comment, `float _yaw_inc_prev` replaces `_t_f_prev`.
- src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml: G2_Y description rewritten (G1 x spin-up time constant, low pass G2/G1, under-estimate benign). Default 0 unchanged. MAX raised 1 -> 1000, because the old max of 1 made the intended value (~27) impossible to set. Say if you want it reverted.
- src/lib/indi_rate_control/indi_rate_control_test.cpp: 4 new tests (suite IndiRateControlYawInvTest). No existing yaw test needed a change: the one reading getTorqueIncrement()(2) (noise std test, G2 = 0) is unaffected, since for G2 = 0 the law is identical.

| Test | Break it catches |
|---|---|
| DcGainAndTimeConstantIndependentOfDt | dropping the (G2/dt) Delta_k-1 term (fails) ; wrong DC gain, dt dependence |
| LandedStateIsZeroAndTakeoffHasNoDoubleCount | no landed zeroing of the state (fails) |
| FaultHoldThenRecoveryHasNoStep | resetStates not zeroing the state (fails); step > max_increment |
| ClosedLoopYawStepSettlesWithoutOscillation (plant G2 x1, x0.5, x2) | dropping the Delta_k-1 term (fails); instability/oscillation |

Counts: indi_rate_control_test 57 total, 57 pass, 0 fail (53 before + 4 new... suites: 56 pass + new one earlier fixed; final run 100% pass).
Break-check: (1) Delta_k-1 term zeroed -> DcGain and ClosedLoop fail; (2) no landed zeroing -> Landed fails; (3) resetStates zeroing removed -> FaultHold fails. Each restored, final rerun green. Old t_f difference term reintroduction was not run separately (it is the same class as break 1; not run).
Build: `make px4_sitl_default` OK (712/712). `make format`: passed, no extra files changed.

UNVERIFIED:
- Closed-loop peak with plant G2 x0.5 is 1.33 (test bound 1.5); only tail settling (<2 % after 3.2 s) and boundedness are asserted.
- No SITL flight run, no log script audit for the new torque_increment(2) meaning (finding 9).
- Break-check of the literal old t_f difference term not executed.
- Plant model sign convention accel = G1 m + G2 dm/dt is assumed from the (G1 + G2/dt) denominator.
