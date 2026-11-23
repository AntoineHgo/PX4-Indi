# Q31: draw 264 (C212 idx 24) cause search and simulator injector fix (S214, 2026-11-23, owner interactive session)

## 1. Injector defect (shown)
`GZBridge` read `parameter_update` through a 1 s `SubscriptionInterval` (src/modules/simulation/gz_bridge/GZBridge.hpp:149).
The runner writes SIM_GZ_EC_MAX1..4 one after the other (~35 ms apart at speed 1): the first write was applied at once,
the rest one full interval later. Rotor speed follows sqrt(u) x EC_MAX, so the applied limit per motor is read from
truth esc_status (instance 1) and actuator_motors (`scripts/drop.py`). Time each motor took EC_MAX < 2150:

| log | m0 | m1 | m2 | m3 | max tilt |
|---|---|---|---|---|---|
| C212 idx 24 INDI s1 (speed1_s213) | 59.04 | 59.09 | 60.04 | 60.04 | 106 (LOC) |
| C212 idx 24 PID s1 | 58.99 | 59.04 | 59.99 | 59.99 | 40 |
| C212 run_024 INDI s4 | 58.44 | 58.59 | 59.44 | 59.44 | 79 (LOC) |
| freeze-10 run_264 INDI s4 | 58.20 | 58.32 | 59.20 | 59.20 | 73 (LOC) |
| **fixed binary** INDI s1 (indi_024) | 58.97 | 59.02 | 59.05 | 59.09 | 75 (LOC) |
| **fixed binary** PID s1 (pid_024) | 59.05 | 59.10 | 59.13 | 59.17 | 37 |

Every C3 flight before the fix was a CCW-only limit for 1 s (yaw spin-up, CCW 0.6 / CW 0.2, yaw torque sp ~0.2 in
both stacks) then a sudden CW limit: not the drawn "all motors step". run.json logged the fault as applied at once.
Affected: every draw with saturation on (C3 corners); weak motor alone was up to 1 s late (single step); the sag
staircase moved in 1 s steps instead of 0.5 s. GATES 2 run validity ("injectors applied within 1 physics step") fails
on all of them. Residual after the fix: 0.12 s spread across the 4 motors (the runner's own write spacing).

## 2. Fix and binary (shown)
Commit f110361a33: plain `uORB::Subscription` (sim-only module). Binary built from the FREEZE-10 sources
(c0b733e677 versions of the 32 firmware files changed since, restored to HEAD after the build) plus the fix, in
px4-indi-sim: sha256 903eae63ceb1bf019215076650cf02fb38cac8534618530410506f6a505f6d62. Against the FREEZE-10 binary
d220e193 (kept as build/px4_sitl_default/bin/px4.freeze10_d220e193): of 14017 function symbols only GZBridge ones change
size; the 200 other frozen build files (parameters.xml, etc/, plugins) match results/g3_refly_actc_s212/chain_freeze.sha256.

## 3. Draw 264 on the fixed binary, speed 1 (shown)
- INDI: `g3_chain.sh start .../indi_024 24 24 --samples g3_refly_actc_s212/samples --speed 1 --allow-binary 903eae63...`:
  aborted, flight watchdog tilt > 60 deg at 60.59 s (truth tilt 60 at 59.88). Still a LOC with the fault applied correctly.
- PID: `fly_pid_run.py 24` (copy of the S213 script, output here): OK, max tilt 37 deg.

## 4. Mechanism on the fixed-binary logs (indi_fix.txt, pid_fix.txt, scripts/outer.py)
- Shown: yaw is not the driver any more: INDI yaw torque sp 0.02-0.06 (0.2 before the fix). No allocator saturation flag
  in either stack until motor 3 nears 1 (INDI 0.97 at 60.0 s). Roll/pitch-over-yaw priority does not separate the stacks.
- Shown: outer loop mild in both: INDI pitch attitude sp -13 -> +4 deg, PID -13 -> -17 -> +7 deg. The fault knocks pitch to
  -30 (INDI) / -23 deg (PID).
- Shown: INDI pitch rate overshoots: rate sp +96..+127 dps at 59.10-59.20, q reaches +194 dps at 59.40 (sp +81 and falling),
  pitch passes its setpoint at 59.40 and keeps rising to 60 deg. Torque sp turns negative at 59.25 and reaches -0.09, but the
  measured torque (torque_filtered) stays -0.02..-0.04 and the filtered pitch accel only -3..-9 rad/s^2.
  PID: q peaks +102 dps at 59.35 and is back to -30 dps at 59.60 with a similar torque sp (-0.07).
- Inferred, not tested: the saturation hook lowers the maximum rotor speed (EC_MAX 2700 -> 1600, motor 3 1347) while the
  INDI measured torque is normalised with the nominal MC_INDI_W_MAX 2700, so after the fault measured torque reads about
  0.35 of the commanded change (0.25 on motor 3). With tau_sp = tau_meas + increment, the measured-torque feedback then
  no longer integrates the missing torque (fixed point tau_real ~ 0.54 x increment): the inner loop loses gain and phase
  exactly when the attitude has been knocked off. Whether this, the weak motor, the drawn G1 error (roll 0.80) or the
  10 ms delay is the cause (and why PID, whose torque path loses the same 0.35, recovers) is what the GATES factor restoration (Q31 B) decides; it is now possible on a valid fault.
