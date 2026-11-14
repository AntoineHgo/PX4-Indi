# Session 42 tilt diagnosis (held-out V motor_loss_0, indi_v2)

Script: `indi_project/bench/tilt_diag.py` (`python3 -I tilt_diag.py show|sweep|fixed ...`; pyulog sits in the user
site dir that `-I` hides, so the script appends it to sys.path). Time base: ULog absolute timestamps (s), the same
base as `run.json` `t_us` (checked: loss event 41.152 s in seed 2 = onset of the tilt in the log).

## Step 1: what happens at t = 20-30 s
- `runner.log` is empty (0 lines). `px4.log` has no param set or mode change after boot (only the startup
  `MC_INDI_EN`, `SIM_GZ_*` sets). `run.json` seed 2: arm 18.15 s, offboard 33.15 s, settle 36.15, loss 41.15,
  up 51.15, zero 55.15; `params_applied` is the tuned set, all applied before arm. No event around 25-30 s.
- ULog, seed 2, 1 s bins: roll/pitch error vs `vehicle_attitude_setpoint` < 0.3 deg for every bin 18-40 s. The tilt
  does NOT start at 27 s. It starts exactly at the motor-loss event (4.5/-5.3 deg in the 41 s bin, 10.3/-10.2 at 42 s).

## Step 2: signals, seed 2 (t = 41-46 s, indi_v2)
- Tilt held: roll +10.2, pitch -10.1 deg, rate 0, `vehicle_rates_setpoint` (-31, +54, +16 deg/s) = MC_PITCH_P x error
  (5.19 x 0.176 rad = 0.91 rad/s). So the rate loop sees a constant 54 deg/s rate error and never removes it.
- `indi_rate_status`: nu = (-15, +15, 0.7) rad/s^2 constant, angular_accel_filtered ~ 0 (1e-4), torque_filtered
  (measured torque, `measured_torque_in_use` = 1) = (+0.027, -0.018, 0.003), torque_increment (-0.086, +0.086, 0.061).
- `vehicle_torque_setpoint` (-0.059, +0.068, 0.064) = torque_filtered + increment to 1e-7 (script `fixed`), and
  increment = nu/174 (G1) = -0.0859 / +0.0856. No saturation: `control_allocator_status` unallocated torque 0,
  motors (0.85, 0.63, 0.61, 0.60), torque increment cap `_max_increment` default 1 is not reached. No `fault`.
- eRPM: motor 0 rpm 7360 at command 0.85 vs motor 1 7616 at 0.64 (thrust ~ rpm^2: ratio 0.93 for a command ratio 1.33),
  i.e. motor 0 realises ~0.7 of its command, as injected.
- pid_tuned seed 2 (same window): same fault, torque setpoint (-0.088, +0.089, 0.064), motors (0.85, 0.60, 0.60,
  0.60), attitude error < 0.15 deg from 44 s. PID reaches the level state with the same ~0.09 torque offset
  because its integrator accumulates it.

## Step 3: other seeds and entries (mean attitude error, deg; script `sweep`)
motor_loss_0, err 44-50 s: indi_v2 seeds 1,2,4-10 = 13.8 13.7 13.5 12.9 13.3 13.2 13.7 13.5 13.5 (all seeds);
pid_tuned <= 0.24, pid_default <= 0.26. Err 30-40 s for indi_v2 is 0.07-0.12 except seeds 5,6,7 (6.1, 4.3, 2.1) which
only differ because the loss event is earlier in those runs (35.4, 36.7, 38.2 s; the 30-40 window then includes the
fault). In every indi_v2 seed the >2 deg onset equals the loss time within 0.2 s. No pre-fault tilt anywhere.
s2_seen_v2 indi_v2 seed1: motor_loss_2 21.7 deg, mismatch_combined_rate 36.7, traj_circle_fast 24.1, others
hover/gust_x/payload_add < 0.25 over the window (note: a plain 44-50 s window is not event-aligned for those entries).

## Step 4: code
`src/lib/indi_rate_control/indi_rate_control.cpp` step 8-9: t_cmd = t_f (measured torque from eRPM through the
NOMINAL effectiveness, `IndiMeasuredTorque::compute`) + (nu - a_f)/G1. The header states "There is no integrator".

## Cause (strong evidence, mechanism partly inferred)
Structural property of the INDI law under an actuator effectiveness loss, not a runner/scenario artefact, not a
guard or parameter problem. The law is incremental on the torque the actuators produce: t_cmd = t_f + nu/G1 with
alpha ~ 0. The allocator maps t_cmd to motor commands absolutely (memoryless, nominal effectiveness) while motor 0
realises only ~0.7 of its command, so the realised torque differs from the command by a roughly constant shortfall
d ~ 0.086 (= t_cmd - t_f, observed). The fixed point is then nu/G1 = d, i.e. nu = 15 rad/s^2 held by a constant rate
error (0.91 rad/s) = a constant attitude error (10 deg). With an intact actuator the loop is t_f(k+1) = t_cmd(k), which
integrates the rate error through the actuator state; with a lost motor that integration is leaky (realised torque is
not the commanded torque + previous), so the loop behaves as P only on this disturbance. No integral term exists
anywhere (rate or attitude) to remove it, hence the steady tilt, the ~160 m drift, and landing as the only way out.
The same shortfall exists for PID, but its integrator absorbs it.

## Unverified
- Leaky-integration explanation is derived from the code and the observed identities (t_cmd - t_f = nu/G1, alpha = 0,
  d = 0.086), not reproduced numerically with the effectiveness matrix; the size of d vs the 30 % loss was not
  recomputed from B.
- The brief's "tilt from ~27 s, before the fault" was not reproduced for seeds 1 or 2 (onset 42.2 and 41.3 s = loss
  event); the brief's times may use a different time base. If a pre-fault tilt is seen in a plot, check that base.
- Other disturbances that do not alter actuator effectiveness (com_shift, gust) are not predicted to show this;
  not checked beyond the brief's statement.
- Whether a remedy (e.g. slow integral on the rate error / on t_f - t_cmd, or effectiveness estimation) fixes it
  was not tested (no simulation allowed).
