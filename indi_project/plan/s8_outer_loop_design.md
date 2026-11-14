# Stage 8: outer-loop (linear-acceleration) INDI with flatness feedforward, design draft

Status: DRAFT, session 41 (2026-11-14), written while the v2 inner-loop validation flies (D-s8-early). Nothing here
is coded. Items marked [verify] are assumptions read from code headers only, to check before implementation.
Sources: `research/notes/tal2021.md` (Tal & Karaman 2021, sec. III-B/C, IV, V), O-9, O-10, O-11.

## 1. What is replaced, what stays

| layer | stock baseline (O-9) | stage-8 INDI path |
|---|---|---|
| position/velocity | `mc_pos_control`: P pos, PID vel, acc ff | new module: P pos, P vel, acc ff, **no integral** (INDI supplies it) |
| acceleration -> thrust vector | hover-thrust scaling (`PositionControl::_accelerationControl`) | **INDI**: thrust increment from filtered measured acceleration and measured thrust |
| thrust vector + yaw -> attitude | `ControlMath::bodyzToAttitude` | same function (reused library) |
| attitude -> rate | `mc_att_control` (`AttitudeControl`, MC_*_P) | same `AttitudeControl` library and gains, **plus body-rate feedforward Omega_ref from jerk** |
| rate -> torque | PID `mc_rate_control` (v2 tuned, r1f c05) | `mc_indi_rate_control` (v2 tuned, r2 c01), unchanged |

Tal's attitude law (eq. 28) is dOmega_c = K_xi xi_e + K_Omega (Omega_ref - Omega_f) + dOmega_ref. With our inner
loop nu = K (Omega_sp - Omega), choosing Omega_sp = (K_xi / K) xi_e + Omega_ref reproduces it except for dOmega_ref,
so a P attitude loop plus a rate feedforward is the PX4-shaped equivalent. The angular-acceleration feedforward
dOmega_ref (snap) is NOT carried in v1 of stage 8 (D-s8-snap): `vehicle_rates_setpoint` has no field for it and O-11
asks for unchanged messages. Tal's Table V ablates jerk/snap feedforward together [verify the split in the PDF].

## 2. Control law (NED, specific force units, per cycle of the module)

Inputs: x, v (vehicle_local_position), q (vehicle_attitude), trajectory_setpoint (p_ref, v_ref, a_ref, jerk_ref,
yaw_ref), body specific force f_b (accelerometer, bias-corrected), measured motor u_i = (omega_i/omega_max)^2 from
eRPM (as in the inner loop, model fallback on eRPM loss).

1. a_c = K_p (p_ref - x) + K_v (v_ref - v) + a_ref, with K_p = MPC_XY_P/MPC_Z_P and K_v = MPC_XY_VEL_P_ACC /
   MPC_Z_VEL_P_ACC: the stock P gains, so position/velocity gains are not a difference between the arms.
   Velocity and acceleration limits as stock (MPC_*), tilt limit via `ControlMath::limitTilt`.
2. Measured acceleration a_f = R(q) LPF(f_b) + g e_z (gravity added back; accelerometers measure specific force).
3. Measured thrust specific force t_f = -G_T LPF(mean_i u_i) R(q) e_z, G_T [m/s^2 per unit mean u] identified
   from hover logs as G1 was (G_T ~ g / mean u at hover; identify, do not tune).
4. INDI increment (Tal eq. 20): t_c = t_f + (a_c - a_f). This is where drag, payload, CoM-induced thrust error and
   motor loss are absorbed: no velocity integrator is needed (Tal sec. III-B claim, to be checked in flight).
5. Collective thrust command T_c = ||t_c|| / G_T in normalised units, clamped to [MPC_THR_MIN, MPC_THR_MAX] with
   vertical priority as stock; thrust direction -t_c / ||t_c||; `bodyzToAttitude(-t_c, yaw_ref)` -> q_d.
6. Omega_sp = AttitudeControl(q, q_d) + Omega_ref, with Omega_ref from jerk (Tal eq. 14): for unit thrust axis
   z_b and collective specific thrust c, h = (jerk_ref - (z_b . jerk_ref) z_b) / c, Omega_ref = (-h . y_b, h . x_b,
   yawspeed_ref * (e_z . z_b)) in body axes (PX4 FRD signs to be derived in the implementation spec, gtest).
7. Publish vehicle_rates_setpoint (roll, pitch, yaw, thrust_body = (0, 0, -T_c)).

Filter matching (the inner-loop lesson): the same LPF (2nd-order Butterworth, one cut-off parameter, start 10 Hz
because the v2 accelerometer carries x1 vibration) on f_b and on mean u, sampled in the same cycle; u passes through
the same eRPM delay compensation as in the inner loop (MC_INDI_ERPM_DLY). Outer-loop bandwidth ~1-2 Hz, so the
filter lag is small against it; the cut-off is identified from a sweep of the sync check, not tuned on scores.

Edge cases: ||t_c|| < epsilon -> hold last q_d and minimum thrust; NaN in any input -> hold last output 3 cycles
then fall back (same rule as D-faulthold); filter states reset on mode entry from the current measurement (no
increment step at engagement); landed / maybe_landed -> module does not engage (the stock pipeline lands).

## 3. Integration (O-11 style: separate module, stock untouched)

New module `mc_indi_pos_control`, registered as an **external mode** exactly like `mc_raptor`
(`register_ext_component_request`, `request_offboard_setpoints = true`, optional `replace_internal_mode =
OFFBOARD` behind parameter MC_INDIP_OFFB), with `setpoint_config` TYPE_RATES so that `mc_pos_control` and
`mc_att_control` stand down and the rate controller selected by MC_INDI_EN flies its rate setpoints [verify the
vehicle_control_mode flags commander derives for TYPE_RATES]. The benchmark runner keeps its offboard PVA stream at
50 Hz; takeoff, hold and landing stay with the stock pipeline, so only the trajectory window is flown by INDI.
Reused libraries: `AttitudeControl`, `ControlMath` (`bodyzToAttitude`, `limitTilt`), the inner loop's filter
classes [verify they link from a new module without touching mc_pos_control/mc_att_control CMake].
Parameters: MC_INDIP_* (enable via mode registration, LPF cut-off, G_T, feedforward on/off, OFFB replace).
Status topic `indi_pos_status` (a_c, a_f, t_f, t_c, Omega_ref) for the sync check and the ablation.

Jerk input (D-s8-ff): trajectory_setpoint.jerk is "for logging only" and MAVLink PVA offboard carries no jerk. The
module uses the jerk field when finite and non-zero, else a backward difference of a_ref over successive setpoint
updates (held between updates). At 50 Hz this lags by ~10 ms: 1 deg of phase at the 1.75 rad/s of H1, negligible.

## 4. Alternatives considered

- Modify `PositionControl::_accelerationControl` behind a parameter: least code, but changes a stock module the
  owner asked to keep at `main` (O-11) and mixes the INDI path into the baseline's binary path. Rejected.
- Copy `mc_pos_control` into a new module: takeoff/landing/constraints duplicated, large and unreviewable. Rejected.
- Full Tal cascade with its own attitude PD emitting angular acceleration to the inner INDI: needs a new message
  between modules and bypasses the stock attitude gains, which would mix two changes in one comparison. Rejected
  for now; the snap feedforward is the only thing lost (D-s8-snap).
- Internal analytic trajectory generator (as `mc_raptor/trajectories`) for exact jerk/snap: unequal reference
  path between the arms (offboard stream vs internal). Rejected for the comparison; possible as a later ablation.

## 5. Evaluation plan (to freeze in `bench/scenarios.md` sec. 9 before the first flight)

Arms (O-9): A = stock pipeline + PID rate (pid_tuned v2); B = stock pipeline + INDI rate (the v2 seen-set T5/H1
runs already give it); C = INDI outer loop without feedforward (MC_INDIP_FF 0) + INDI rate; D = C with jerk
feedforward. A vs D is the headline; C vs D isolates the feedforward, B vs C the outer INDI feedback (O-9 ablation).
Draft scenarios (all trajectory-window, position RMS primary, 10 seeds, paired Wilcoxon, sec. 6 thresholds):
lemniscate (T5 profile), fast circle (H1), lemniscate + gust_x, lemniscate + payload_add, lemniscate + com_shift,
fast circle + motor tau x2, vertical sine with mass x1.15 (thrust-model mismatch, INDI's G_T error case). The last
two aim at expected INDI weaknesses, as V1/V5 did for the inner loop. Effort check as criterion 4.

## 6. Open questions to settle in the implementation spec

1. TYPE_RATES control-mode flags and whether `request_offboard_setpoints` delivers trajectory_setpoint [verify].
2. Accelerometer source: `vehicle_acceleration` (filtered by IMU_ACCEL_CUTOFF upstream) or `sensor_combined`
   (raw); the filter chain of f_b must equal that of u, so a raw source plus our own LPF is preferred [verify fields].
3. Thrust model: does the allocation library already give a measured collective thrust from eRPM alongside
   actuator_torque_measured (O-11 module code), or is mean u enough (symmetric x500, equal k_T)?
4. G_T identification script (from v2 hover logs, CPU only) and its spread across seeds.
