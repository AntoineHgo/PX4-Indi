# T5, H1, H4 trajectory scenarios: 10 seeds per controller (session 15)

Frozen candidates (D-freeze): PID = PX4 defaults, INDI = `results/tuning/indi/r4f/c00/params`. Speed 1, seeds 1-10,
paired by seed, 60/60 runs completed (log `results/traj_s15.log`, untracked). Trajectory error is measured against the
logged `trajectory_setpoint` (`metrics.json` block `trajectory`); att = attitude rotation-angle RMS (deg) over the
window (dominated by the commanded tilt, not a tracking error of the rate loop only); minalt = lowest altitude above
home in the window (m); p = exact two-sided Wilcoxon signed-rank. Note: in the minalt row "INDI lower" means worse.
Table computed by an inline script in session 15 from `metrics.json` and the ULog (`vehicle_local_position`);
TODO: move it into `bench/` before the report so the figures stay reproducible.

## T5 traj_lemniscate (tuning-set mechanism, never used for tuning in practice)

| metric | PID | INDI | ratio | INDI lower | p |
|---|---|---|---|---|---|
| position RMS 3d (m) | 0.46 ± 0.0045 | 0.437 ± 0.0047 | 0.95 | 10/10 | 0.002 |
| max deviation 3d (m) | 1.2 ± 0.026 | 1.3 ± 0.026 | 1.08 | 0/10 | 0.002 |
| att RMS (deg) | 10.8 ± 0.017 | 7.89 ± 0.017 | 0.73 | 10/10 | 0.002 |
| minalt (m) | 5.03 ± 0.13 | 4.94 ± 0.029 | 0.98 | - | 0.23 |

Small INDI gain in RMS (5 %), slightly larger peak deviation (8 %). The position loop (PX4 MPC, shared) dominates.

## H1 traj_circle_fast (held-out)

| metric | PID | INDI | ratio | INDI lower | p |
|---|---|---|---|---|---|
| position RMS 3d (m) | 3.43 ± 0.042 | 2.51 ± 0.022 | 0.73 | 10/10 | 0.002 |
| max deviation 3d (m) | 8.07 ± 0.083 | 6.67 ± 0.078 | 0.83 | 10/10 | 0.002 |
| att RMS (deg) | 16.9 ± 0.059 | 15.3 ± 0.036 | 0.90 | 10/10 | 0.002 |
| minalt (m) | 4.0 ± 0.16 | 3.84 ± 0.031 | 0.96 | - | 0.006 |

The path needs ~52 deg tilt, above MPC_TILTMAX_AIR 45 deg (D-h5): neither controller can track it, errors are metres.
INDI deviates 27 % less, presumably because its faster attitude response uses the tilt limit sooner; not analysed.

## H4 motor_loss_2 (held-out): both controllers crash on every seed; equivalent up to impact

Motor 2 at 60 % thrust under the lemniscate's 6.6 m/s^2 path acceleration exceeds what the x500 can deliver with
either controller (as specified and frozen, D-h5). Ground contact (altitude < 0.3 m): PID 10/10, INDI 10/10.

Up to first ground contact (fault onset to contact; inline script, session 15, from `vehicle_local_position` and
`vehicle_attitude`):

| | PID | INDI |
|---|---|---|
| time from fault to ground contact (s), seeds 1-10 | 7.1-7.2 (all 7.2 but one) | 7.3-7.6 (mean 7.45) |
| max tilt before contact (deg) | 17 on every seed | 18-23 (18 on 6 seeds) |

Whole-window metrics (include the post-impact samples, so they describe the crash, not the control):

| metric | PID | INDI | ratio | INDI lower | p |
|---|---|---|---|---|---|
| position RMS 3d (m) | 4.35 ± 0.24 | 5.01 ± 1.0 | 1.15 | 3/10 | 0.11 |
| att RMS (deg) | 38.6 ± 25 | 69.3 ± 22 | 1.80 | 1/10 | 0.010 |
| peak tilt error (deg) | 32.1 ± 7.9 | 111 ± 56 | 3.46 | 1/10 | 0.004 |
| saturation time (s) | 8.86 ± 2.7 | 8.97 ± 1.6 | 1.01 | 4/10 | 0.85 |

Reading: the whole-window numbers make INDI look worse, but its large tilt errors (up to >90 deg) all occur after
impact, on the ground. In flight both controllers fail the same way; INDI stays airborne ~0.3 s longer. H4 is a
draw: neither controller can fly it. The metrics window should end at ground contact for scenarios that can crash
(metrics.py change, to do before the report).
