# Stage 8 implementation spec: outer-loop (acceleration) INDI with jerk feedforward

Status: session 49 (2026-11-15). Based on `s8_outer_loop_design.md` (design, alternatives) and `s8_verify.md` (code
facts). Where this file and the design draft differ, this file wins. Three tasks, separate commits, in order:
**A** library + gtests, **B** module + parameters + status message, **C** G_T identification + sync check.
Scenarios (sec. 5) are frozen in `bench/scenarios.md` sec. 10 and pre-checked with pid_tuned (O-13) before INDI flies.

## 1. Conventions

NED world frame, FRD body frame, R = R(q) body->world. Specific thrust vector t (world, m/s^2) = -c z_b, c > 0,
z_b = R e3. g_vec = (0, 0, +9.80665). Acceleration a = t + g_vec + (drag, disturbances): accelerometer measures
specific force f_b = R^T (a - g_vec), so a_f = R f_b + g_vec.

## 2. Task A: library `src/lib/indi_accel_control/` (class `IndiAccelControl`, no uORB, no params)

Pattern: copy the layout of `src/lib/indi_rate_control/` (CMake `px4_add_library`, `target_link_libraries(... PRIVATE
mathlib)`, PUBLIC include dir, `px4_add_unit_gtest(SRC IndiAccelControlTest.cpp LINKLIBS IndiAccelControl)`). Fixed-size
members only, no dynamic allocation, every float input checked with `PX4_ISFINITE`.

Configuration setters:
- `setGains(Vector3f k_pos, Vector3f k_vel)` (per axis x,y,z; z from MPC_Z_*), `setLimits(float vel_xy_max, float vel_z_up_max,
  float vel_z_down_max, float tilt_max_rad, float thr_min, float thr_max)`.
- `setFilter(float sample_freq_hz, float cutoff_hz)`: one `math::LowPassFilter2p<Vector3f>` on f_b and one
  `math::LowPassFilter2p<float>` on mean u, SAME cut-off and sample rate (filter matching; cutoff <= 0 disables both).
- `setThrustModel(float g_t, float k_cmd)`: g_t [m/s^2 per unit mean u] > 0; k_cmd = mean u per unit thrust_body
  command (identified, ~1 with THR_MDL_FAC 0.683 and CA_R_W_MAX 1000; task C).
- `setMeasurementDelay(int samples)`: ring buffer on the mean-u sample only, clamp [0, 4] (same role as MC_INDI_ERPM_DLY:
  eRPM arrives later than the accelerometer).
- `setFeedforward(bool jerk_ff)`.
- `reset(const Vector3f &f_b, float mean_u)`: filters and delay buffer initialised to these values (no increment step).

Per cycle: `bool update(const Input &in, Output &out)` with Input {p, v, q, f_b, mean_u, mean_u_valid, p_ref, v_ref, a_ref,
j_ref, yaw_ref, yawspeed_ref, dt} and Output {q_d (Quatf), yawspeed_ff, thrust (normalised command, >= 0), omega_ff
(Vector3f body, z = 0), a_c, a_f, t_f, t_c (Vector3f, for status)}. Steps:

1. **Reference handling.** NaN p_ref component -> no position term on that axis (as stock: velocity-only). NaN v_ref ->
   0 feedforward on that axis but position term still active. NaN a_ref -> 0. NaN j_ref or not provided -> j_ref from
   backward difference of a_ref over successive *changes* of a_ref (store a_ref and its timestamp; difference only
   when a_ref changed; hold between updates; reset to 0 on `reset()`), clamp each axis to +-50 m/s^3.
2. **Commanded acceleration.** v_sp = k_pos (p_ref - p) + v_ref, clamp xy norm to vel_xy_max and z to
   [-vel_z_up_max, vel_z_down_max]; a_c = k_vel (v_sp - v) + a_ref. No integrator (INDI supplies it).
3. **Measured acceleration.** f_bf = LPF(f_b); a_f = R(q) f_bf + g_vec. (Rotation by the current q, not filtered.)
4. **Measured thrust.** u_f = LPF(delay(mean_u)); t_f = -g_t u_f z_b. If `mean_u_valid` is false: use the previous
   cycle's thrust command times k_cmd in place of mean_u (model fallback, same rule as the inner loop on eRPM loss).
5. **INDI increment.** t_c = t_f + (a_c - a_f).
6. **Saturation, vertical priority.** Require t_c,z <= -epsilon (thrust must point up); if not, t_c,z = -g_t * thr_min.
   Tilt: limit the angle between -t_c and -e3 to tilt_max_rad keeping t_c,z (scale the horizontal part).
   c = ||t_c||; thrust = clamp(c / (g_t * k_cmd), thr_min, thr_max). If saturated at thr_max: shrink the horizontal
   part first so that the vertical component is kept (stock vertical-priority rule).
7. **Attitude.** body_z = -t_c / c; q_d from `ControlMath::bodyzToAttitude(body_z, yaw_ref, att_sp)` (link
   `PositionControl`; if linking it into a lib is a problem, reimplement the 15-line function in the lib with a comment
   naming the original, and gtest equality on 3 vectors). NaN yaw_ref -> keep the current yaw of q.
8. **Rate feedforward (if jerk_ff).** Derivation (body rates p,q,r; z_b' = q x_b - p y_b; t' = -c' z_b - c z_b'):
   j . x_b = -c q, j . y_b = c p. With x_b, y_b the body axes of **q_d** (desired attitude) and c from step 6:
   omega_ff = (j_ref . y_b / c, -(j_ref . x_b) / c, 0); clamp each to +-3 rad/s; zero if c < 1 m/s^2.
   yawspeed_ff = yawspeed_ref (0 if NaN), passed to AttitudeControl by the module (not added to omega_ff).
   gtest: a coordinated-turn case (constant-speed circle, analytic a, j, expected rates) and the sign case "pitch nose up
   -> jerk along -x_b".
9. Return false (outputs untouched) if any required input is non-finite; the module then holds (sec. 3).

gtests (at least): hover equilibrium (t_c = t_f when a_c = a_f, thrust = hover value, q_d level); pure INDI increment
(a_c - a_f = (0,0,-1) -> thrust up by 1/(g_t k_cmd)); tilt limit; thrust saturation keeps vertical; NaN input -> false;
reset gives zero increment on the first cycle; filter matching (same step on f_b and mean u gives identical normalised
responses); delay buffer clamps; jerk feedforward sign and turn cases; jerk backward-difference hold.

## 3. Task B: module `src/modules/mc_indi_pos_control/` (after A is committed)

- External mode like `mc_raptor` (s8_verify Q1): name "INDI POS", register_mode true, arming check true (reply: allow
  arming, no failures), request_offboard_setpoints true, `enable_replace_internal_mode = MC_INDIP_OFFB` (default 1),
  replace NAVIGATION_STATE_OFFBOARD so the runner's existing offboard switch selects it. On the inactive->active edge,
  publish `setpoint_config` TYPE_RATES (s8_verify Q2) and `reset()` the library from the current measurements; unregister
  on exit.
- Run on `vehicle_local_position` updates (~50-100 Hz in SITL; dt measured, clamp [0.002, 0.05]); filter sample rate =
  measured mean rate (set once after 50 samples, or from param). Inputs: `vehicle_local_position` (x,y,z,vx,vy,vz; valid
  flags required), `vehicle_attitude`, `sensor_combined.accelerometer_m_s2` (latest), `esc_status` (mean u with
  `IndiRateControl::normalisedThrustFromRpm` over the 4 motors, valid only if all 4 online and plausible; omega max from
  CA_R_W_MAX converted to rpm), `trajectory_setpoint`, `vehicle_land_detected`.
- Gains/limits read from the stock parameters (MPC_XY_P, MPC_Z_P, MPC_XY_VEL_P_ACC, MPC_Z_VEL_P_ACC, MPC_XY_VEL_MAX,
  MPC_Z_VEL_MAX_UP, MPC_Z_VEL_MAX_DN, MPC_TILTMAX_AIR, MPC_THR_MIN, MPC_THR_MAX) so the two arms share them. Attitude:
  a module-owned `AttitudeControl` configured from the MC_*_P / MC_*RATE_MAX / reference-model parameters exactly as
  `mc_att_control` configures its own (read and mirror its `parameters_updated()`); omega_sp = update(q) + omega_ff.
- Publish `vehicle_rates_setpoint` {roll, pitch, yaw, thrust_body = (0, 0, -thrust)} and `indi_pos_status` (new
  message: timestamp, a_c[3], a_f[3], t_f[3], t_c[3], omega_ff[3], mean_u, mean_u_valid, thrust, jerk_source (0 field,
  1 difference)); add it to logged topics.
- Hold rule: library returns false or an input is stale (> 0.1 s) -> repeat the last rates setpoint for up to 3 cycles, then
  publish level attitude rates (0,0,0) with the last thrust and report mode failure (the runner's watchdog judges).
- Landed or maybe_landed: do not run the law; publish zero rates and MPC_THR_MIN (the runner never activates the mode on
  the ground).
- Parameters `MC_INDIP_*` (yaml, as mc_indi_rate_control): `_EN` (module start in rc), `_OFFB` 1, `_LPF_CUT` 10 Hz,
  `_G_T` (task C value), `_K_CMD` (task C), `_DLY` 1 (samples), `_FF` 1. Kconfig `depends on MODULES_MC_POS_CONTROL &&
  MODULES_MC_ATT_CONTROL`; enable in `boards/px4/sitl/default.px4board`; start in the posix rc only when `MC_INDIP_EN` = 1.
- Stock modules stay untouched (O-11). Regression: `make px4_sitl_default` + a hover flight with MC_INDIP_EN 0 shows the
  same run.json metrics as the last pid_tuned hover (within seed noise).

## 4. Task C: identification and sync check (CPU, before tuning anything)

- G_T and k_cmd from existing v2/v3 hover logs (`results/s2_heldout_v2/runs/*/indi_v2/*/flight.ulg`, hover windows):
  G_T = slope of the regression of the measured specific thrust magnitude ||R f_b|| (accelerometer, hover, low pass)
  on mean u through the origin; k_cmd = regression slope of mean u on thrust_body (vehicle_thrust_setpoint). Report spread across 5 seeds;
  script `bench/ident_gt.py`, result `results/s8_ident_gt.md`. These are identified, never tuned (owner lesson on ACT_TC).
- Sync check after the first INDI-pos flight: cross-correlate a_f,z and t_f,z increments (lag 0-1 cycle expected), as
  `results/sync_check_v0.md` did for the inner loop.

## 5. Scenarios and arms (to freeze in `bench/scenarios.md` sec. 10 before any INDI-pos flight)

Arms (O-9): A = stock pipeline + pid_tuned; D = INDI-pos with jerk ff + indi_v3 rate; C = D with MC_INDIP_FF 0
(feedforward ablation); B = stock pipeline + indi_v3 rate (context only, few seeds, O-13). Verdict pair: A vs D, 10 seeds.
Entries (all new paths/parameters, never used for tuning): O1 lemniscate 10 x 5 m 6 m/s; O2 fast circle r 5 m 8 m/s +
vertical sine 1.5 m; O3 O1 + gust; O4 O1 + payload_add; O5 O2 + com_shift; O6 vertical sine with mass x1.15 (G_T error
case); O7 O1 + motor tau x2 (expected INDI weakness). Each entry is flown once with pid_tuned before freezing (O-13);
any entry pid_tuned cannot fly is replaced, not kept. Tuning (if any) only on T5/H1 (seen paths) with the O-12 watchdog.
