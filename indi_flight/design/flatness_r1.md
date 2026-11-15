# Differential flatness in the INDI outer loop (session 13, 2026-11-15)

Owner answer to Q1: "Option A seems correct. I'm wondering using differential flatness as done in
https://arxiv.org/pdf/1809.04048. Consider seriously this." This note takes that seriously: what the paper does, what
A already has of it, what is missing, and how to add it without breaking O-11. The paper summary is from my
knowledge of it (Tal & Karaman, INDI + differential flatness). The PDF was not re-read this session, so a source
check is the first item of review r5.

## 1. The paper's structure, mapped to A
| paper block | A today | gap |
|---|---|---|
| a_ref = a_traj + PD(pos, vel) | stock PositionControl (A9), acc ff from `trajectory_setpoint.acceleration` | none |
| thrust-vector INDI: tau_c = tau_f + (a_ref - a_f), filtered specific force and filtered thrust, same filter | LIB:273 `t_c = t_f + (a_c - a_f)`, A5 filter matching | none: A already *is* this law |
| attitude from thrust direction + yaw | `ControlMath::bodyzToAttitude` (same construction: z_b from tau, x/y from yaw) | none |
| body-rate ref from jerk (flatness, needs tau, jerk, yaw rate) | LIB computes `omega_ff` from jerk (hpp:65-68) but A6 turns it off: `vehicle_attitude_setpoint` cannot carry it (r1 F14) | **interface** |
| angular-acceleration ref from snap, into the inner INDI | none | snap not available in PX4 (see 3) |
| inner INDI on angular acceleration | `mc_indi_rate_control` | needs a feed-forward input |

So the incremental acceleration law of the paper is A's law. What flatness adds is the **feed-forward path from
jerk (and snap) to body rate (and angular acceleration)**. In the paper this path is what makes aggressive
tracking work: the attitude loop no longer lags a fast-rotating thrust vector.

## 2. Where the feed-forward can go (O-11: mc_att_control at zero diff)
- **F-a. None (A as is).** The attitude P loop of mc_att_control tracks a moving q_sp with lag about 1/MC_ROLL_P. That
  is acceptable at mission speeds, and the tracking error grows with jerk.
- **F-b. The INDI position module also runs the attitude loop** (stock AttitudeControl library) and publishes
  `vehicle_rates_setpoint` with omega_ff, with mc_att_control not started. Rejected: in Stabilized, Acro and manual
  attitude modes mc_att_control builds the attitude setpoint itself. F-b would then need either a second copy of
  that code or two publishers of rate setpoints that switch by mode, which is a new edge class.
- **F-c (proposed, A18). Side channel to the INDI rate module.** `mc_indi_pos_control` publishes a new topic
  `indi_rate_feedforward` with omega_ff in FRD, an optional alpha_ff, the timestamp of the `vehicle_attitude_setpoint`
  it belongs to, and a valid flag. `mc_indi_rate_control` adds omega_ff to the rate setpoint from mc_att_control, and
  alpha_ff to its angular-acceleration command, only when all of these hold:
  - the message is fresh (less than 2 outer cycles old);
  - its attitude-setpoint stamp matches the setpoint currently used;
  - the INDI stage is active and not in bypass or on an open group (A10).

  Otherwise it adds zero. Stock modules stay at zero diff; one new message. This is the standard
  feed-forward-around-a-P-loop structure: mc_att_control corrects the residual and the ff carries the derivative of
  q_sp.

## 3. Inputs available in PX4
- Jerk: `trajectory_setpoint.jerk` is filled by FlightTaskAuto (`FlightTaskAuto.cpp:230`, PositionSmoothing) and
  Orbit (`FlightTaskOrbit.cpp:333`); the message calls it "for logging only". Manual modes and most offboard users
  give none. omega_ff therefore exists in Auto, Orbit and offboard with jerk, and is zero elsewhere, which is the
  same as A.
- Never differentiate a_ref to get jerk: r1 F14 showed every setpoint step (failsafe, idle -> flight, re-expression
  after reset) becomes a jerk pulse. Use the jerk field only when it is finite. Clamp it, and zero it at all A3 and
  e7 edges.
- Snap: absent. PositionSmoothing is jerk-limited with piecewise-constant jerk, so snap is impulsive. alpha_ff is
  left at zero unless a filtered derivative of omega_ff proves useful in the tracking test.
- Flatness needs the actual thrust magnitude: use the INDI tau_c (filtered), not ht/k, so a thrust-scale gap does
  not scale omega_ff.

## 4. Value against the gates, and the plan
- No gate threshold is on aggressive tracking. The value is in G5 (missions and Orbit on a fast 5-inch quad), in the
  trajectory metric, and in G2: feed-forward adds no loop gain, so it does not change the margins. The risk is a
  wrong-sign or wrong-frame omega_ff, which unit tests on a known circle trajectory catch (analytic omega for a
  constant-speed circle).
- Plan:
  - A18 = F-c, implemented after A's base works (stage 5, second step).
  - Accept or remove it on a measured test: figure-8 and Orbit at 3 speeds, trajectory error against ground truth
    with omega_ff on and off, PID as reference.
  - The interface (`indi_rate_feedforward` message) is reserved now.
- Because A18 adds an interface between the two modules, it gets one narrow review round (r5, opus, this note
  against the paper and the rate module) before stage 5.
- Overturn: the measured tracking gain is below the same-seed spread (G1.6 d), or the side channel produces a
  transient at any A3/e7 edge in the G5 set.
