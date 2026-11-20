# A18 jerk -> omega_ff side channel (S141, design note, one page)

Gate item: G5.5 rows o1-o4/o7 (horiz RMS 0.78-0.93 m vs limit 0.5; truth lags setpoint 160 ms, D-A18-REOPEN).
Base: `design/flatness_r1.md` F-c. Stock modules stay at zero diff (O-11). One new message.

## What exists
`IndiAccelControl` already computes `out.omega_ff = (j.y_b, -j.x_b, 0)/c` (R_d frame, clamp 3 rad/s, zero when
z_only or c < 1 m/s^2) from `in.j_ref` when finite, else from a filtered backward difference of `in.a_ref`.
The module disables it (`setFeedforward(false)`, McIndiPosControl.cpp:57) and nothing consumes `omega_ff`.

## Two defects in the existing difference path (fixed by this change)
1. It differentiates `in.a_ref` = feed-forward + P/D feedback: the derivative of the feedback is noise and
   double-counts the loop. Fix: difference **only the feed-forward acceleration** (`trajectory_setpoint.acceleration`,
   new input `in.a_ff`); NaN axis -> no jerk on that axis, history forgotten (as today for a_ref).
2. It holds the last difference forever once a_ff stops changing (a single step in a_ff leaves a constant jerk).
   Fix: a hold timeout `kJerkHold = 0.1 s` (5 periods of a 50 Hz offboard stream): no change for longer -> 0.

## Jerk source rule (module)
`j_ref(i) = trajectory_setpoint.jerk(i)` if the jerk vector is finite and not all zero; otherwise NaN, which selects
the a_ff difference. Reason: MAVLink SET_POSITION_TARGET has no jerk, so offboard arrives as finite 0. Treating an
all-zero jerk as missing is safe in every mode: a source that truly has zero jerk has constant a_ff, whose difference
is 0 after the hold timeout. Auto/Orbit keep their PositionSmoothing jerk.

## Edges (flatness_r1 F14: a spurious a_ff step is a jerk pulse)
- The integral of omega_ff over a real a_ff step is the tilt change that step needs (Δa/c), so a genuine step is a
  correct pulse, bounded by the 3 rad/s clamp and the 50 m/s^3 jerk clamp.
- Spurious steps (mode change, setpoint re-init, EKF reset re-expression, landed/ramp, idle -> flight) occur where the
  module already calls `_indi.reset()` (or the bypass branch resets every cycle): reset forgets the jerk history, so
  no pulse. The implementation must confirm every such edge reaches reset(); a test covers one.

## Side channel: new message `IndiRateFeedforward.msg`
`timestamp`, `float32[3] omega_ff` (rad/s, FRD body, z = 0), `bool valid`. Published by `mc_indi_pos_control` every
cycle in which it publishes an attitude setpoint; `valid` = INDI stage active (not bypass/landed/ramp/z_only) and
omega_ff finite. Published invalid otherwise.

## Consumer: `mc_indi_rate_control`
Adds omega_ff (roll, pitch) to `_rates_setpoint` taken from `vehicle_rates_setpoint` only when: message `valid`, age
< 50 ms (5 outer cycles at 100 Hz; the outer loop period is 10 ms), not landed, rate setpoint not from the manual/acro
branch, and the setpoint watchdog is not tripped. Otherwise adds zero. The gate is a small header with a unit test
(same pattern as `RateSetpointWatchdog`). flatness_r1 also asked for an attitude-setpoint stamp match: dropped, the
rate module never sees `vehicle_attitude_setpoint` (it would need a second subscription for a check that freshness
already bounds to one outer cycle of mismatch).

## Frame
omega_ff is in the desired body frame R_d and is added in the actual body frame. The error is second order in the
tilt error (same approximation as the stock yaw-rate feed-forward); the attitude P loop corrects the residual.

## Margins
Feed-forward adds no loop gain: G2 cells are unchanged. The jerk difference is open loop in a_ff, not in feedback.

## Tests (each checked by breaking it)
Library: (a) constant-speed circle with analytic jerk -> analytic body rates (sign and frame); (b) a_ff step then hold
-> jerk 0 after 0.1 s; (c) feedback-only a_ref change with a_ff constant -> omega_ff 0; (d) reset() mid-ramp -> no
pulse. Gate header: valid/stale/landed/manual cases.

## Pass / overturn
Fly G5.5 o1 and o2 s1 with matched GNSS. Overturn (D-A18-REOPEN): gain < 0.1 m RMS on o1, or a G5 edge broken
(re-fly G5.7 x1 and one G5.2 row as the edge check).
