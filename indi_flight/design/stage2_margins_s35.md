# Stage 2 design: stability margins (gate G2), S35

Status: DESIGN ONLY (no code, build or flight). Items marked (UNVERIFIED) were not read in this session and must be
checked before implementation. Line refs are to the working tree at S35.

## 0. Summary and constraints
- Zero diff (O-11) on mc_rate_control, mc_att_control, mc_pos_control, control_allocator, allocation lib, commander. So no
  injection inside the PID stack. PID loops are probed from OUTSIDE it: gz_bridge (gyro, motor path), gz force, setpoints.
- One physical rule drives the design: a loop gain needs BOTH signals around a break point. Setpoint injection gives
  T = y/r (closed loop), not L. It gives L only when the logged error e = r - y is exactly what the loop closes on
  (single feedback path through e). Neither rate controller qualifies: PX4 PID rate (D on measured accel) and INDI
  (feedback through K*e AND the angular-accel term a_f) are two-degree-of-freedom. See 1.1.
- Method: injection d(t) known and independent of the loop; L = -S_yd / S_xd (instrument method, section 3), or the
  sensitivity method L = 1/S - 1 where only an output disturbance is possible (outer loops).
- Controller-rate note: `indi_flight/bench/run_scenario.py:37` has `RATES_HZ = (800, 400, 267)`: 800/round(800/RATEMAX).
  250 Hz is not selectable; "250 reported" is really 267 Hz (VERIFIED in source). Decide in session A.

## 1. Loop-break points and injection mechanisms
### 1.1 Mechanism evaluation
- M1 gz_bridge gyro path: add n(t) to `gyro_b` before `_px4_gyro[i].update(...)` (`GZBridge.cpp:675-686`; rotor vibration
  is already added there, `addRotorVibration` l.623). x = sensor_gyro (post-injection, logged, 800 Hz), y = pre-injection
  gyro (needs a new sim-only topic, e.g. `sim_inject`, same callback, same sim timestamp). Works UNCHANGED for PID and INDI;
  it is a true single-point break of the whole rate controller incl. IMU filters, derivative, delays (INDI uses the gyro
  twice: K*e and a_f; both are behind the break). Caveat: EKF2 integrates the injected gyro, so the attitude loop stays
  closed through the estimator: the measured L_rate is "rate loop with attitude loop closed" (negligible above ~5 rad/s,
  crossover is K = 20 rad/s for INDI). Band must start >= 0.5 Hz; gyro-bias estimator ignores it above that (UNVERIFIED).
- M2 gz_bridge actuator path: add d(t) to the rotor command in `GZMixingInterfaceESC::updateOutputs` before
  `_actuators_pub.Publish` (`GZMixingInterfaceESC.cpp:75-113`, motor scale l.108), along B^+ e_axis (pure roll/pitch/yaw
  torque, no thrust). u_pre = actuator_motors (logged), u_post = applied (new sim topic). Plant-input break in torque
  space, both stacks. Needs the allocation matrix B (CA_ROTOR*_PX/PY/KM params, UNVERIFIED) to project. Acts as the
  cross-check of M1 (SISO loop gain must agree at any break point); also exposes cross-axis terms (3 axes with disjoint
  frequencies give the 3x3 loop matrix).
- M3 injection inside INDI modules behind a bench-only param (INDI stack only; PID cannot have it): (a) torque level,
  add d to `torque_setpoint` before publish (`McIndiRateControl.cpp:195` update, :314-329 publish): u_pre/u_post exact, no
  allocator; (b) acceleration level, add d to `t_c` at `indi_accel_control.cpp:273` (`t_c = t_f + (a_c - a_f)`), log t_c
  pre/post in `indi_pos_status` (already logged); (c) attitude level, add d to the rate setpoint where
  `McIndiPosControl.cpp:571` builds `rates = attitude_control.update(q) + omega_ff` (`_rates_setpoint_pub` :381). These are
  the only breaks that expose the INDI incremental loop (t_f path) separately. New msg fields live in INDI-owned or
  sim-only topics; any new .msg file is outside the zero-diff list but needs msg versioning care (UNVERIFIED).
- M4 setpoint injection through the player: `sched` rows today are arm, disarm, mode_offboard, sp, sp_hold, sp_back, att,
  pva, takeoff, land, anchor (`SimScenarioPlayer.cpp:133-212`, applied l.418-530; `sched_scenario_rows`
  `run_scenario.py:497-523`). Excitation is applied in sim time and logged (`sim_schedule_applied`, `run_scenario.py:70`).
  Gives T, and L = y/e only where valid: attitude loop (P on e, roll/pitch), position loop (p enters only via e_p, the
  velocity loop is inside), INDI velocity loop (v only via e_v). NOT valid for either rate loop or PID velocity loop
  (D-on-measurement). New rows needed: `vel` (position NaN, velocity loop alone, UNVERIFIED that offboard accepts it),
  and one multisine row kind (or many `att`/`pva` rows at 50 Hz, as traj rows already are, no player change).
- M5 external force in sim time (sensitivity method, both stacks): ApplyLinkWrench on base_link. `bench/disturbance.py`
  already does it from a Python process; for G2 the wrench must be published from the gz_bridge physics callback
  (sim time, logged in the same callback) not from Python (wall/clock-message timing, UNVERIFIED). F enters at the
  acceleration node, so v/F = S/(m s), p/F = S/(m s^2): L = 1/S - 1 with m = SDF mass (read from model, UNVERIFIED).
  It returns the TOTAL return difference at the acceleration node (velocity, position and inner loops together).

### 1.2 Per-loop table (primary = P, cross-check = X)
| Loop | PID stack | INDI stack | Signals (topic, controller rate?) |
|---|---|---|---|
| rate roll/pitch/yaw | P: M1; X: M2 | P: M1; X: M2, M3a | x=sensor_gyro (800 Hz, logged), y=sim_inject.gyro_pre; motors: actuator_motors, vehicle_torque_setpoint (logged, interval 0) |
| attitude | P: M4 `att` rows, L=y/e, e from vehicle_attitude_setpoint, vehicle_attitude (logged) | P: M3c (rate sp break); X: M4 via module-internal e | vehicle_rates_setpoint (logged), indi_pos_status; quaternion error small-angle |
| velocity | P: M4 `vel` + M5 (velocity-only mode, pos loop open) | P: M4 `vel` (L=v/e_v exact); X: M5, M3b | vehicle_local_position, trajectory_setpoint (logged interval 0, but EKF output rate, UNVERIFIED ~50-100 Hz) |
| position | P: M4 L=p/e_p (position mode) | same as PID; X: M5 | vehicle_local_position(_setpoint) |
| INDI accel (linear) | n/a (no PID equivalent; PID shown by M5 total) | P: M3b at t_c | indi_pos_status (extend with t_c_pre/d), vehicle_acceleration (logged) |
| INDI ang. accel (t_f path) | n/a | P: M3a plus the model (4.1) | needs `indi_rate_status` and `actuator_torque_measured`, NOT in `LOG_TOPICS` (`run_scenario.py:55-72`): add, interval 0 |
Outer loops are bandwidth-limited by the estimator rate; their band stays far under 20 Hz, so non-controller-rate topics are acceptable there.

## 2. Excitation
- Multisine, not chirp: period-exact FFT (no leakage, no window), phases Schroeder (crest factor ~1.7), frequencies on the
  1/T_p grid, log-spaced (about 10 per decade), per-axis disjoint subsets so 3 axes are excited in ONE flight and
  cross-axis terms are separable. Chirp kept as fallback/cross-check for one case. The multisine is generated INSIDE the sim
  callback from (freq list, amplitudes, phases) params and sim time (never wall time); d(t) logged each sample.
- Bands (design values, to be confirmed in the pre-test): rate 0.5-60 Hz (crossover ~3 Hz at K=20, HF mismatch term
  needs up to ~0.3 fs: 80 Hz at 267/400 Hz); attitude 0.2-8 Hz; velocity and INDI accel 0.1-4 Hz; position 0.05-2 Hz.
- Amplitude (keep linear): chosen from the pre-test so that peak |torque - hover| <= 0.2, motors stay in [0.2, 0.85]
  (no allocator clip), tilt <= 6 deg, position excursion <= 1.5 m, gyro n RMS <= ~0.3 rad/s. Spectrum shaped ~1/f at low
  frequency (SNR), flat at HF. Scale by 2 in one repeat to check linearity (L must not change > 1 dB).
- Duration: 6 periods, first discarded. Rate/att: T_p = 20 s (0.05 Hz grid), 100 s excitation. Vel/pos: T_p = 60 s, 4
  periods = 4 min. All at hover (hover thrust, zero setpoint), wind off, same `T_ARM_S` determinism as G1.6.
- Flights per controller rate (800, 400, 267): PID rate (M1, M2) 2; attitude 1; velocity 1-2; position 1; PID total ~6.
  INDI rate (M1, M2, M3a) 3; attitude 1-2; velocity 1-2; accel 1; position 1; INDI ~9. About 15 per rate, 45 for G2,
  plus 3 repeats and one linearity run per stack: ~55 flights.

## 3. Estimation and synthetic self-test
- Estimator: per axis/period FFT at the excited bins, average over periods; fall back to Welch (Hann, 50 %, segments of
  4 periods) for chirp/noise data. G_yd = S_yd/S_dd, G_xd = S_xd/S_dd, L = -G_yd/G_xd (M1/M2/M3); L = y/e (M4);
  L = 1/(m s^k v/F) - 1 (M5). Coherence gamma^2_xd and gamma^2_yd >= 0.8 (>= 0.9 within a decade of crossover) else the
  bin is rejected; sample variance across periods gives a per-bin confidence band; margins reported with the band edges.
- Reading margins: PM = angle(L)+180 at each |L|=1 crossing; GM = -20log|L| at each angle = -180; take the worst
  crossing, not the first. Delay margin DM_i = PM_i(rad)/w_ci, DM = min_i. Pass = DM >= 2 T_s + tau_tel
  (T_s = 1.25 ms at 800 Hz, 2.5 ms at 400; tau_tel = MC_INDI_ERPM_DLY samples = 1 default, plus the esc_status age).
  Also report peak |S| (disk margin) as a sanity cross-check on GM/PM. Reject (flag "band-limited") if |L| is not < -10 dB
  at the upper band edge. Empirical DM check: add k samples of gyro delay in the bridge (bench param) and require the
  measured PM drop to equal w_c k T_s within 20 %.
- Self-tests (pure Python, no sim, run before any flight; a failing self-test blocks the analysis):
  1. Open loop, known answer: L(s) = K e^{-s tau}/(s(1+sT)) discretised at 800/400/267 Hz, with GM/PM/DM from an
     independent root solve; estimator on synthetic data must give GM +-1 dB, PM +-3 deg, DM +-0.3 ms.
  2. Closed loop, known answer: simulate the loop in discrete time with plant/measurement noise, same multisine, same
     CSV-reader format as the bench logs. Assert (a) instrument estimator unbiased, (b) the naive -y/x without instrument
     IS biased (proves the test has power), (c) rejected bins are exactly the low-coherence ones.
  3. Timebase: inject d with a 1-sample offset in x vs y: the estimator's lag check (cross-correlation of d against the
     logged copy) must flag it; run at 267 Hz decimation (non-integer 800/267) to catch alias/sample-hold errors.
  4. Model-vs-simulation (feeds section 4): the discrete INDI model simulated in the time domain must reproduce its
     analytic L(z) through the same estimator within 0.5 dB / 2 deg.

## 4. Linear models for the cross-check
Notation: T = 1/controller rate; A_r = real actuator chain (motor lag tau_r, gz command latency, ZOH T/2); A_m = model
chain e^{-s d_m T}/(1+s tau_m) with tau_m = MC_INDI_ACT_TC (default 0.02 s) and d_m = MC_INDI_DELAY (default 0);
A_meas = A_r e^{-s n T} (n = MC_INDI_ERPM_DLY, default 1); F_w = IMU gyro low pass (IMU_GYRO_CUTOFF 40 Hz, set at
`run_scenario.py:39`); H = LPF2p(40 Hz) x alpha(20 Hz) x derivative, same chain on the gyro derivative and the model path
(by design, McIndiRateControl.cpp:95); g = G1_true/G1_set (default MC_INDI_G1_R = 320 rad/s^2 per unit, MC_INDI_K_R = 20 1/s);
eta = delivered/allocated torque. Tau_r and the gz motor time constants are in the SDF (UNVERIFIED, read in session A).
### 4.1 INDI rate loop (per axis; yaw adds the G2 spin-up term, omitted)
Derived from `indi_rate_control.cpp` (steps 3-9: t_act lag, delay buffer, H, measured path, blend, nu = K e, dt = (nu-a_f)/G1):
- Loop broken at the torque setpoint u (M3a), model-only t_f, plant w' = g G1 A_r u:
  `L = g (K/s) F_w A_r + H (g A_r - A_m)`   (first term: rate loop; second: incremental mismatch loop).
- With measured torque and blend (`hpp:59-62`; t_f = t_meas + LPF_Tb(t_model - t_meas), blend alpha = dt/(Tb+dt), kMaxBlend 2),
  plant w' = G1 eta A_r u, A_meas = eta A_r e^{-snT}:
  `L = eta (K/s) F_w A_r - H (A_m - eta A_r e^{-snT}) / (1 + s Tb)` (+ terms that vanish when n = 0, eta = 1).
- Low-frequency reduction (A ~ 1, H ~ 1): characteristic polynomial `Tb s^2 + eta (1 + K Tb) s + eta K`, i.e. a blend mode at
  w_n = sqrt(eta K / Tb), zeta = eta (1 + K Tb) / (2 sqrt(eta K Tb)). Discretise by z = e^{sT} with the real sample delays;
  the time-domain version (self-test 4) is the 800/400/267 Hz reference. Checks that must hold: eta = 1, Tb any -> L = (K/s) F_w A_r.
### 4.2 PID rate loop
`L = (Kp + Ki/s - Kd s F_d) G1 eta A_r F_w / s`, torque-per-rad/s gains; D on the measured angular acceleration with the
IMU derivative filter (IMU_DGYRO_CUTOFF 20 Hz). Gains, I-term and MC_*RATE_K scaling to be read from mc_rate_control
source and params (UNVERIFIED, not read this session); G1 from the same MC_INDI_G1_* effectiveness for like-for-like.
### 4.3 Anomaly A-1 (`indi_project/results/v3_screen.md` l.22: Tb 0.1 lost altitude after the fault, 1 seed, pruned unexplained)
- What the model says: the blend replaces the integral action by an extra rate-loop mode at w_n = sqrt(eta K/Tb). With
  K = 20: Tb 0.1, eta 0.25-0.5 gives w_n 7-10 rad/s, zeta 0.53-0.75; Tb 0.3: w_n 4-6 rad/s; Tb 1.0: 2-3 rad/s, zeta ~0.75;
  Tb 0.03: zeta ~0.3. So Tb 0.1 puts the mode at the attitude-loop crossover (UNVERIFIED value of the attitude gain; read it)
  where it can cost attitude phase, while Tb 0.3 and 1.0 place it below. For eta near 1 (no fault) nothing differs, which
  matches the nominal entries being indistinguishable (v3_screen.md reading, "within 3 %").
- Hypothesis H-A1a (linear): at Tb 0.1 and reduced eta the attitude-loop PM and peak |S| are worse than at Tb 0.3.
- Hypothesis H-A1b (nonlinear, the linear model cannot show it): the faulted motor saturates, the blend hands the model
  torque (what was allocated, not delivered, with `unallocated_torque` subtracted at `McIndiRateControl.cpp:178-182`) to
  the law at a speed the allocator cannot follow; the allocator trades thrust for torque; altitude is lost. A linear
  model alone cannot explain altitude loss, only a margin dip: it explains A-1 only if it predicts growing tilt.
- Hypothesis H-A1c (null): single-seed outlier.
- Test (in this order, cheapest first): (1) 5 seeds of motor_loss_0 at Tb 0.1 vs 0.3, same gates as v3_screen, count how
  many lose altitude (decides H-A1c at no model cost); (2) log fraction of cycles with |t_cmd| = 1 and allocator
  unallocated thrust and `indi_rate_status` blend state (`getActuatorBlend()` exists at `hpp:229`, is NOT in the
  message: add a field) -> H-A1b; (3) measured L(Tb) at eta in {1, .75, .5} using collective motor scale `SIM_GZ_THR_SC`
  (`run_scenario.py:806`, UNVERIFIED that it scales all motors) as the eta proxy, M1/M3a injection at hover -> compare
  measured attitude PM and w_n, zeta with 4.1 -> H-A1a. A-1 is closed if (1) fails to reproduce; else attribute by (2)/(3).

## 5. Work breakdown (3 sessions, ~20-30 tool calls each)
- S36 Analysis + models (no sim): `indi_flight/bench/margins_est.py` (estimator, margins, DM), `margins_models.py` (4.1 analytic
  and discrete time-domain, 4.2), `tests/test_margins_selftest.py` (self-tests 1-4). Second keys: self-tests pass; model L equals
  time-domain-simulated L; eta=1 reduces to the pure-K case; predicted w_n/zeta table for Tb x eta (A-1 prediction written down BEFORE flying).
- S37 Injection infrastructure: gz_bridge M1/M2 (+ force M5, delay knob), params in `gz_bridge/parameters.yaml`, `sim_inject`
  topic (sim time, one sample per step), INDI bench params M3a/b/c, extra fields (`indi_rate_status`, `indi_pos_status`),
  `LOG_TOPICS` additions, `run_scenario.py` flags (`--inject`, rate), player rows `vel`/multisine if needed. Second keys: zero
  injection amplitude gives bit-identical log vs baseline; logged x - y equals the logged d to float precision; `git diff main
  -- mc_rate_control mc_att_control mc_pos_control control_allocator lib/control_allocation commander` is empty; 800/400/267
  timestamp alignment (timebase_check.py style).
- S38 Flights + gate: pre-test (amplitude, linearity), the ~55-flight matrix, result tables (GM, PM, DM per loop, rate, stack),
  model cross-check (|L| within 2 dB and 10 deg at crossover), A-1 tests 1-3, G2 verdict, PID shown as reference only.
  Second keys: repeat-run spread of GM/PM < 2 dB / 5 deg; M1 vs M2 agreement; 2x amplitude linearity.

## 6. Open questions and risks
- 250 Hz is not selectable (267 Hz is): owner call; or extend `RATES_HZ`.
- Does the player/offboard accept velocity-only (NaN position) rows? Is `sim_scenario_player` in scope of "simulator code"
  (it is under `src/modules/simulation/`, not named in the brief)? Confirm with owner before editing it.
- Outer-loop L from M4 is exact only for single-feedback structures; for the PID velocity loop M5 gives the total return
  difference at the acceleration node, which is the conservative quantity but not the loop in isolation.
- Estimator-rate outer loops: `vehicle_local_position` is not controller-rate; delay of the estimate is part of the loop (good,
  real) but must be logged to interpret DM there. Delay-margin pass criterion "2 control periods + telemetry latency" is
  trivial for the rate loop (~tens of ms) but may bind on the INDI mismatch term; confirm tau_tel definition.
- MIMO: single-axis margins ignore cross-coupling (yaw/roll through the allocator); report the 3x3 and the worst sigma_min of
  I + L at the plant input from M2 for the gate, or state the gate is per-axis.
- Hover linearisation: injections near saturation (low thrust margin, vibration `SIM_GZ_VIB_*`) bias L; keep G1 vibration setting.
- New msg files and parameters: any change outside INDI and gz_bridge trees breaks O-11; keep every new field in INDI or sim-only topics.
