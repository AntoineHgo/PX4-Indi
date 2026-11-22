# S199 cause search, step 1: which loop goes unstable first (INDI speed-1 re-fly logs)

Data only, no firmware change proposed. Scripts: `cause_s199/` (common.py, timeline.py, loopcheck.py, env.py, fault264.py). Times are sim s. Fitted
quantities are least-squares sin/cos at the line frequency over 4-8 s windows; "L" is the rate-loop open loop assembled from
the fitted pieces (controller tsp/err x plant accel/tsp x 1/jw), so it is a describing-function estimate on a growing/limit-cycle signal.
`MC_INDI_ACT_TC` = 0.033 s in all runs; drawn plant tau scale 3.0 (245), 2.55 (239), 0.50 (283), 0.60 (264).

## 245 (C1, pitch 2 Hz, LOC)
- Shown: growth is NOT at ~65 s. It starts at lift-off (~30 s) and grows exponentially, x3 per 4 s, with constant ratios between levels,
  from 0.3 deg to a plateau of 29 deg / 360 dps amplitude at ~51 s (pitch peaks 58 deg). Rate setpoint clips at 220 dps (plateau, shown).
  Motors stay 0.11-0.29 (no 0/1 saturation) until 63 s; saturation (min 0, then max 1) appears only in the last ~2 s. Saturation follows.
- Shown (25-33 s, small signal, 2 Hz): rate loop closed w/wsp = 1.48 at -79 deg; |L| = 0.91 at -145 deg (phase margin ~35 deg on the rate loop alone,
  so the rate loop is lightly damped, not unstable). Attitude loop wsp/(attsp-att) = 7.2 at -3 deg, closing it gives |L_att| ~0.84 at about -169 deg (~11 deg margin, estimate);
  attsp/att = 0.30 at +125 deg (position loop feeds the attitude setpoint back in phase with the pitch motion). All levels grow together, so
  no level shows its error first; the margin is lost in the cascade rate -> attitude -> position, with the rate loop already at 1.5x peaking.
- Shown: tsp -> measured torque (eRPM) gain 0.65, lag 56 deg at 2 Hz (equivalent tau ~0.12 s vs the controller's 0.033 s); tsp -> true angular accel 1214 at -62 deg
  (controller model G1_P 2460 at ~-14 deg). True accel/measured torque 1865 (controller 2460, so G1 over-estimated 1.3x, gain not the problem; phase is).
- PID twin, same draw (shown): no growth; 2 Hz line stays below ~2 dps, motors 0.15-0.22.

## 239 (class B, ROLL p, not pitch; no LOC)
- Shown: the detector line is roll rate p at 2-2.5 Hz. Not a steady limit cycle: lightly excited bursts, biggest at 62-64 s (129 dps amplitude, 2.25 Hz), decaying by 66 s; smaller ones at 58 and 82 s.
  Motors 0.10-0.22, never saturated. PID twin: roll 2.25 Hz below ~1 dps.
- Shown (42-47 s, before the burst): rate closed loop w/wsp 1.99 at -69 deg (sharper peak than 245), |L| = 0.88 at -147 deg; attitude P 6.8, attsp/att 0.75 at +32 deg;
  tsp -> measured torque 0.61 at -49 deg (tau up 1.85 / down 2.55 vs 0.033 modelled). True accel/measured torque 2296 vs G1_R 1677: G1 under-estimated 1.37x, so loop gain is above design on top of the lag.
- Inferred: a lightly damped 2 Hz mode of the rate/attitude cascade, rung by gust or the eRPM freeze (motor 1, 2.5 s after traj start); not an unstable loop.

## 283 (class A, pitch q 10.75 Hz)
- Shown: rate loop only. Rate setpoint amplitude at 10.75 Hz ~0.4-0.7 dps, rate response 7-8 dps (31 dps peak second at 62 s), so the line is self-generated in the rate loop.
  Open loop (sim 61-69 s): |L| = 0.92 at -176 deg, i.e. gain ~1 at the -180 deg crossing. Controller tsp/err = 0.058 at +27 deg; plant tsp -> accel 1068 at -114 deg (total delay ~30 ms at 10.75 Hz).
- Shown: motors 0.08-0.19, no saturation; measured torque follows tsp at 0.67, -80 deg. Drawn: tau scale 0.5 (fast plant), delays 5+5 ms, vibration x5, G1 mult pitch 0.88, 20% telemetry dropout. PID twin: 0.2-0.6 dps at that frequency.

## 264 (C3, tilt > 60 deg at 60.9 s)
- Shown: fault step at ~58.3 s (all motors x0.351, motor 3 further x0.709 = 0.249). Hover needs ~0.51-0.52 on motors 0-2 and ~0.73-0.75 on motor 3 in both INDI and PID; no unallocated torque
  until the end, motor 3 reaches 1.0 only at 60.7 s with tilt already 88 deg. Saturation follows the loss.
- Shown: INDI and PID follow the same path to 59.5 s (yaw rate -68/-24 dps at the step, yaw rate setpoint ~100 dps, yaw torque 0.16-0.21, CCW pair 0.63 vs CW pair 0.21). At 59.7-59.9 s both spin up yaw (124-135 dps) with CW rotors collapsing (rpm 8000 -> 7400).
  PID then recovers (q 71, then 31 dps at 60.1 s); INDI does not: q 114 then 175 dps at 60.1 s against a rate setpoint of -127 (wrong direction), rate setpoints on the 220 dps limit on all axes by 60.4 s, tilt 69 deg.
- Inferred: the yaw axis (large yaw torque held against slow, weakened CW rotors) disturbs roll/pitch first; INDI's roll/pitch loop then fails to recover where PID does. Allocation assumes equal motors (weak motor 3 not known to it).

## Per-run conclusions (shown = on the log, inferred = my reading)
- 245: rate/attitude/position cascade at 2 Hz, lightly damped from lift-off, grows exponentially to a rate-limited plateau (shown); plant tau 3x vs 0.033 s modelled giving ~56 deg lag (shown), G1 pitch mult 1.5 (shown, but G1 over-estimated, so not a gain excess); saturation is a consequence (shown); position-loop contribution inferred from attsp/att.
- 239: same cascade mode in roll, only intermittently excited (shown); tau 1.85-2.55x and G1 under-estimated 1.37x make it peaky (shown); trigger inferred.
- 283: rate loop alone at 10.75 Hz, gain ~0.92 at -176 deg (shown, describing-function estimate); drawn contributors delays 5+5 ms and vibration x5 inferred, no saturation (shown).
- 264: yaw spin-up under motor fault first (shown), INDI fails to recover roll/pitch where PID does (shown); mechanism inferred; saturation follows (shown).
Unverified: whether the 2 Hz growth in 245/239 needs the position loop (no loop-open run); actuator_torque_measured is eRPM-derived with 3 frames latency, so its lag mixes plant and telemetry; fits are at 200 Hz resampling.
