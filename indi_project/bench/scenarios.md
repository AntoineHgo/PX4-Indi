# Benchmark specification: scenarios, metrics, acceptance criteria

Status: **frozen v1, 2026-11-13 (session 3), written before any INDI code
exists.** Changes after INDI's first flight are allowed only to fix a defect in
the harness. Each change is logged at the bottom of this file with its reason,
and it applies to both controllers and to every result already recorded (those
results are re-run).

## 1. What the benchmark has to probe

With a fixed control effectiveness, rate-loop INDI is algebraically an
incremental PI(D) (acquatella2017, eq. 29-30, see `research/notes/acquatella2017.md`).
So on a nominal plant with small inputs, a well-tuned PID should roughly match
INDI, and a difference there would mostly reflect tuning. Any real INDI
advantage has to come from one of these mechanisms, and the scenarios are
chosen to exercise each one:

| Mechanism | Scenarios that exercise it |
|-----------|----------------------------|
| Disturbance rejection through angular-acceleration feedback (no integrator wind-up delay) | gusts, payload drop/add, CoM shift |
| Robustness to plant change without retuning (inertia, mass, motor effectiveness) | payload, degraded actuator, plant mismatch |
| Actuator-state feedback and actuator-dynamics handling | rate steps, aggressive trajectory, slow-motor mismatch |
| Saturation handling | aggressive trajectory, degraded actuator, large rate steps |

The weak points are tested too: noise sensitivity (hover, control effort) and
dependence on the effectiveness estimate (plant mismatch).

## 2. Controllers under test

| Label | Description |
|-------|-------------|
| `pid_default` | PX4 defaults for gz_x500 as shipped (airframe file), untouched. |
| `pid_tuned` | PX4 PID retuned for gz_x500 on the **tuning set only**. |
| `indi` | INDI rate loop (+ existing attitude P loop unless the design says otherwise), tuned on the **tuning set only**. |

**Fairness rule:** `pid_tuned` and `indi` get the same tuning procedure and the
same budget: the same optimiser or sweep design, the same number of simulation
evaluations, the same tuning cost function (section 5) and the same scenarios.
The tuning logs of both are kept in `results/tuning/`. Parameters outside the
rate/attitude loops (position control, estimator, allocator, failsafes) are
identical for all three controllers.

## 3. Scenarios

All scenarios start from a 5 m hover in offboard mode after takeoff. Times are
sim time. "Sim extension" marks scenarios that need simulator changes. Those
changes are committed separately and applied identically to every controller.

### 3.1 Tuning set (T): used for tuning and development

| id | Scenario | Excitation | Primary metric |
|----|----------|------------|----------------|
| T1 `hover` | position hold 30 s, sensor noise only | none | rate RMS error, position RMS |
| T2 `step_roll`, `step_pitch` | attitude steps 0, +15, 0, -15, 0 deg, 3 s each | setpoint | attitude IAE over the step windows |
| T3 `step_yaw` | yaw steps 0, +45, 0, -45, 0 deg, 4 s each | setpoint | yaw IAE |
| T4 `rate_step_roll` | roll-rate pulses +-120 deg/s, 0.25 s, x3 | setpoint | rate RMS error during pulses |
| T5 `traj_lemniscate` | lemniscate 8 m x 4 m, peak speed 5 m/s, position+velocity+acceleration feedforward | trajectory | position RMS error |
| T6 `gust_x` (sim extension) | steady 3 m/s wind along +x, then 1-cosine gust +6 m/s along x, 1 s duration | disturbance | peak attitude and position deviation, recovery time |
| T7 `payload_add` (sim extension) | +25 % mass added at the CoM during hover | disturbance | peak altitude deviation, recovery time |
| T8 `motor_loss_0` (sim extension) | motor 0 thrust constant x0.7 during hover and then a yaw step | plant change | attitude RMS after the event, peak deviation, saturation time |
| T9 `mismatch_inertia` | Ixx, Iyy x1.3 in the sim, controller unchanged, run T2 | plant change | attitude IAE ratio vs nominal |

### 3.2 Held-out set (H): never used for tuning or development

Held-out runs are executed only for the final validation (phase 6) and for at
most one intermediate check per design iteration, whose result is recorded
but must not drive gain changes. Each H scenario is a variant of a T mechanism
with different parameters, so that tuning on T cannot simply memorise it.

| id | Scenario | Variant of |
|----|----------|------------|
| H1 `traj_circle_fast` | circle radius 4 m, 7 m/s, plus a 2 m vertical sine | T5 |
| H2 `gust_diag` | steady 4 m/s wind at 45 deg in the xy plane, gust +8 m/s, 0.6 s, from 120 deg | T6 |
| H3 `com_shift` | payload of +15 % mass offset by 5 cm along +y | T7 |
| H4 `motor_loss_2` | motor 2 x0.6 during the lemniscate of T5 | T8 |
| H5 `mismatch_combined` | inertia x0.8, mass x1.15, motor time constant x2, run T2 + T4 | T9 |
| H6 `step_diag` | simultaneous roll+pitch step 20 deg | T2 |

### 3.3 Seeds and repetitions

- Seed controls: sensor noise seed (if the simulator lets us set one, see
  `RUNNER_NOTES.md`), gust onset time (uniform +-0.5 s), wind direction jitter
  (+-10 deg), and trajectory start phase. The seed is recorded in `run.json`.
- Tuning: 3 seeds per evaluation. Final validation: 10 seeds per scenario and
  controller, the same seed list for every controller (paired design).

## 4. Metrics (computed by `bench/metrics.py` from the ULog only)

Evaluated inside the scenario window only, which starts when offboard is
engaged and ends when it is left.

- **Tracking:** RMS and IAE of the rate error (`vehicle_rates_setpoint` vs
  `vehicle_angular_velocity`), the attitude error (rotation angle of
  q_sp^-1 q), and the position error for trajectories.
- **Steps:** 10-90 % rise time, overshoot %, 5 % settling time, per step.
- **Disturbance:** peak deviation from the pre-event state, and recovery time
  until the error stays within 10 % of the peak (attitude) or within 0.2 m
  (position).
- **Control effort:** RMS of d/dt of the `actuator_motors` outputs (noise
  transmission) and RMS of the motor outputs about their mean (differential
  effort).
- **Saturation:** fraction of the window during which any motor output is
  >= 0.99 or <= 0.01, plus `control_allocator_status` unallocated torque when
  available.
- **Safety:** crash (attitude error > 60 deg, ground contact, or divergence)
  makes the run a failure. Failed runs are reported, never dropped.

## 5. Tuning cost function (identical for `pid_tuned` and `indi`)

J = mean over T scenarios and seeds of (primary metric / primary metric of
`pid_default` on the same scenario and seed), plus a penalty of 0.2 x (effort
ratio - 1) when the effort ratio is above 1.25, plus 10 for any failed run.

## 6. Acceptance criteria (decided before INDI flies)

Comparisons are paired by seed: per scenario, a Wilcoxon signed-rank test on the
10 per-seed differences of the primary metric, two-sided, alpha = 0.05.

INDI **outperforms PID** if, against `pid_tuned` on the held-out set H:

1. no INDI run fails in any H or T scenario;
2. INDI is significantly better (median improvement >= 10 % and p < 0.05)
   on at least 4 of the 6 H scenarios;
3. INDI is not significantly worse by more than 10 % on any H scenario;
4. INDI's control-effort metric is at most 1.5x that of `pid_tuned` in hover
   (T1), so that a gain in tracking is not bought with motor noise a real
   vehicle could not tolerate.

If 1 and 3 hold but not 2, the result is "INDI matches PID". In any other case
it is "INDI does not outperform PID". All three outcomes are written up with
the same rigour. Results against `pid_default` are reported too, but they do
not decide the outcome.

## 7. Simulation fidelity prerequisites

INDI's claimed advantages depend on realistic actuator dynamics, sensor noise,
delay and disturbances. Before T6-T9 and H are run, the following must be
checked in the gz_x500 model and documented in `bench/sim_fidelity.md`: motor
time constant (and whether it differs between spin-up and spin-down), IMU
noise and bias model, gyro rate and latency, whether wind and drag act on the
body, and whether mass, inertia and motor constants can be changed at runtime
or per run. Missing pieces are added as simulator extensions in separate
commits.

## 8. Stage-2 held-out set V (frozen v2, 2026-11-14, session 36, before the v2 INDI flies any of it)

Owner decision O-7; choices in DECISIONS.md D-heldout-v2; draft `plan/s2_heldout_v2.md`. Every run uses the v2
configuration: `--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05` and `v2_fac.params` for both
families (D-omega2), seeds 1-10, speed 4 for attitude/rate patterns and speed 1 for position scenarios (D-speed).
Scenario-level plant settings override the CLI ones. None of these entries is ever used for tuning.

| entry | id | plant change (identical for both controllers) | primary metric (as in v1 for the same pattern) |
|---|---|---|---|
| v2_tau2_att, v2_tau2_rate | V1 | motor time constants x2 | H5 att: roll attitude RMS; H5 rate: roll-rate RMS |
| v2_asym_att, v2_asym_rate | V2 | spin-down constant x3 (synthetic, not sourced) | same |
| v2_lat_att, v2_lat_rate | V3 | eRPM latency +2 frames (placeholder magnitude) | same |
| v2_drop_att, v2_drop_rate | V4 | 20 % eRPM frame drops + total loss of motor 0 over one segment | same |
| v2_vib3_hover, v2_vib3_att | V5 | vibration x3 | T1 hover: as T1; att: as H5 att |
| v2_sag_att | V6 | available thrust 100 % -> 85 % over the window | as H5 att |
| gust_diag | V7 | H2 profile | as H2 |
| com_shift | V8 | H3 profile | as H3 |
| motor_loss_0 | V9 | T8 profile | as T8 |

V7-V9 were flown in v1 (never tuned on): held out, but their v1 outcome is known. The seen set (H1-H6, T1-T8 on
the v2 configuration) is reported separately and labelled as seen.

Acceptance for v2 (section 6 rules, same test and thresholds, scaled to 14 entries, against the v2 `pid_tuned`):
1. no INDI run fails in any V, seen or T entry;
2. INDI significantly better (median improvement >= 10 %, p < 0.05) on at least 10 of the 14 V entries (2/3, as 4/6
   in v1);
3. INDI not significantly worse by more than 10 % on any V entry;
4. INDI hover control effort (T1, v2 configuration) at most 1.5x `pid_tuned`.
Outcome words as in section 6.

## Change log

- v1 (2026-11-13): initial frozen version.
- v1.1 (2026-11-14, before any tuning run of either controller): the T2/T3
  primary metric is the RMS attitude error of the stepped axis over the
  scenario window (`attitude_tracking.<axis>_rms_deg`) instead of IAE,
  because `metrics.py` computes RMS, not IAE. Both penalise the same
  tracking error over the same window; RMS weights large errors more. The
  same metric applies to `pid_tuned` and `indi`. T1 uses position RMS 3D,
  T4 roll-rate RMS. The effort ratio uses `effort.motor_rate_rms_per_s`.
  Stage-1 tuning uses T1-T4 only: T5-T9 need simulator extensions that do
  not exist yet; when they do, both controllers are re-tuned on the full T
  set with the same budget.
- 2026-11-14 (session 12): H6 `step_diag` implemented as the T2 pattern
  (settle 2 s, then 0, +20, 0, -20, 0 deg, 3 s each) on roll and pitch at
  once; step metrics are reported per axis (`<segment>_roll`,
  `<segment>_pitch`), primary metric `rotation_angle_rms_deg`. One PID
  default harness check (seed 1, x4): 6.5 deg, no saturation. Not used for
  tuning.
- 2026-11-14 (session 12): H2 `gust_diag` and H3 `com_shift` implemented
  in `bench/disturbance.py` with the T6/T7 models. Directions are where the
  air moves to, angle from gz world +x towards +y (T6 is +x); the gust is a
  0.6 s 1-cosine of 8 m/s at 120 deg on top of a 4 m/s base wind at 45 deg
  (ramp 2 s, hold 10 s, gust, hold 15 s). H3: weight of +15 % mass applied
  as a force with a 5 cm +y lever arm kept fixed in the world frame
  (level-hover approximation; mass and inertia of the plant unchanged, as
  in T7). Metric kinds: gust_diag horizontal, com_shift vertical. PID
  default harness check (seed 1, speed 1): gust_diag 0.44 m / 11.2 deg /
  recovery 15.1 s; com_shift 0.21 m / 2.6 deg / recovery 3.9 s.
- 2026-11-14: T9 `mismatch_inertia` implemented via per-run gz model variants
  (`model_variant` scenario key, `bench/model_variant.py`; Ixx, Iyy x1.3,
  verified in gz). Same mechanism supports ixx/iyy/izz/mass/tau scales for
  H5. PID default (seed 1, speed 4): roll RMS 3.27 deg vs 3.35 deg for
  step_roll, no slower rise (details in `plan/t9_model_variant_log.md`).
- 2026-11-14 (session 15): H5 implemented as two runs `mismatch_combined_att`
  (T2 pattern) and `mismatch_combined_rate` (T4 pattern), model variant ixx,
  iyy, izz x0.8, mass x1.15, motor time constants x2 (gz reports mass 2.3 kg).
  Trajectory mode added (`traj` segment, position + velocity + acceleration
  feedforward, smoothstep phase ramps of 3 s so paths start and end at rest at
  the hold position): T5 `traj_lemniscate` (Gerono, 8 x 4 m, 5 m/s, 2 laps),
  H1 `traj_circle_fast` (r 4 m, 7 m/s, vertical sine +-1 m, 3 laps), H4
  `motor_loss_2` (T5 path, motor 2 thrust x0.6 from path start). Metric:
  `trajectory` block, error against the logged `trajectory_setpoint`. Start
  phase is not seeded (deviation from 3.3: seed varies only sim noise). H1
  needs ~52 deg tilt, above the default MPC_TILTMAX_AIR 45 deg: infeasible as
  specified for both controllers, flown unchanged. H4 PID seed 1 touched the
  ground (altitude 0 m in the window): reported as an outcome, not re-specified.
- 2026-11-14 (session 36): section 8 added, stage-2 held-out set V frozen (O-7) before any v2 INDI flight on it.
  The v1 sections are unchanged and v1 results stay valid.
