# Flatness feed-forward A18, round 2: answers to review r5

Session 15. Input: `flatness_r1.md`, `outer_loop_review_r5.md` (verdict BLOCKING, F1). No new review round until
base A flies in stage 5 (STATE S15). A18 stays out of base A.

## Decision
A18 is kept as an optional stage-5 increment, specified as the review's "Minimal correct A18", with the changes below.
It is built only after base A passes its stage-5 tracking pre-test, and kept only if the acceptance test passes.

## Answers
| finding | answer |
|---|---|
| F1 BLOCKING yaw-rate double count | Accepted. Message carries `omega_ff_xy = (j.y_b, -j.x_b)/c - psi_dot (e3.x_b, e3.y_b)` in the q_d body, psi_dot = `yaw_sp_move_rate` of the same setpoint; Omega_z = 0. The same double count exists today in `McIndiPosControl.cpp:564-571` (`yawspeed_ff` + `omega_ff`): anomaly A-9, fixed in the base-A rewrite of stage 5 by the same subtraction (or by dropping `omega_ff` from that path until A18). |
| F2 MAJOR freshness unverifiable | Accepted. Message carries `attitude_setpoint_timestamp`; rate module subscribes to `vehicle_attitude_setpoint` and gates on equality. The one-attitude-cycle race is accepted and written in the design. |
| F3 MAJOR accumulation trap | Accepted. Local `rates_sp_used = constrain(_rates_setpoint + g R(q^-1 q_d) omega_ff, -rate_max, rate_max)` each gyro cycle; `_rates_setpoint` never modified; Acro never adds it (gate on attitude AND velocity/position flags). |
| F4 MAJOR frame | Accepted: rotate by `q^-1 q_d` in the rate module (needs `vehicle_attitude`, already available at gyro rate through the estimator topic). Small-error approximation rejected: it fails in the transients where A18 matters. |
| F5 MC_REF_FF overlap | Gate g on `MC_REF_FF == 0`. Baseline of the acceptance test = base A with `MC_REF_FF` tuned (zero new interface). |
| F6 mapping corrections | Accepted in full; `flatness_r1.md` section 1 is superseded on: acceleration-error term (paper K_a, not in stock, not added), thrust from motor-speed encoders (agrees with O-5 measured omega), psi_dot enters only Omega_z. Paper evidence for the jerk term alone: none (Table V ablates rate and angular-acceleration ff together). A18 must earn its place on our data. |
| F7 jerk from difference | A18 uses only a finite, nonzero message jerk; `jerk_from_difference` forced off for the published ff. The difference path in the LIB is re-examined in stage 5 (r1 F14 class). |
| F8 steps and staleness | First-order filter on omega_ff in the rate module (time constant = one local-position period, ~8 ms at 125 Hz). Staleness bound 25 ms in microseconds of `vehicle_local_position` time. Zero on landed, maybe_landed, disarm. |
| F9 untested transitions | Added to the acceptance set below. |

## Acceptance (all required)
1. Unit: full rate setpoint (mc_att_control output + A18) vs analytic Omega for a constant-speed circle with yaw
   locked to the tangent and to the centre, and with fixed yaw, at tilts 10, 30, 45 deg. Checked by breaking F1 once.
2. Flight, ground truth, same seed: figure-8 and Orbit, A18 on vs base A with `MC_REF_FF` 0 and tuned. Keep A18 only
   if its tracking gain over the better baseline exceeds the G1.6 same-seed spread.
3. Edge set with the applied (post-gate) ff logged in the rate module status: Auto -> Stabilized -> Acro in Orbit,
   RTL landing, injected heading reset, offboard with jerk stream cut, failsafe Descend from Orbit at tilt. Pass:
   applied ff exactly 0 within one attitude cycle of each edge; no rate-setpoint step larger than base A's.

## What overturns this
A failed acceptance item 2 (A18 dropped, F-a with `MC_REF_FF` kept). An edge in item 3 that cannot be gated without
changing a stock module (A18 dropped: O-11 outranks it).
