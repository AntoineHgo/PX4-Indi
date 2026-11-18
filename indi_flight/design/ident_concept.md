# Identification concept (decision 3) and default set (decision 4), S119 draft

Status: PROPOSED, owner question Q6. Serves G6 (defaults + procedure, start from physical parameters wrong by x2 / x0.5,
no manual tuning) and lesson 8 (identified, never tuned). Archive identification scripts are not reused (review 11.1).

## 1. What INDI needs, and where each value comes from

| quantity | param | source in the procedure | note |
|---|---|---|---|
| control effectiveness roll/pitch/yaw | MC_INDI_G1_R/P/Y | in-flight regression (sec 2, M1) | initial guess: D-G1-DERIVE closed form |
| yaw spin-up term | MC_INDI_G2_Y | same regression, second regressor d(u)/dt on yaw | initial guess: D-G2Y-DERIVE |
| actuator time constant (up/down) | MC_INDI_ACT_TC | command -> measured omega^2 fit, first order + dead time (M2) | upper bound reported (S53) |
| telemetry latency | MC_INDI_ERPM_DLY | lag of max cross-correlation, gyro alpha vs G1 du_meas (M3) | needs telemetry at >= loop rate/2 |
| rotor speed at full command | MC_INDI_W_MAX | steady command -> omega map over the hover excitation, quadratic thrust-curve fit, extrapolated to 1 (M2) | G1 absorbs a W_MAX error in u-space; bench burst in the bring-up checklist cross-checks it |
| loop and filter delay | MC_INDI_DELAY | computed from the filter configuration (decision 6), not identified | |
| specific thrust (outer loop) | thrust model of mc_indi_pos_control | hover fraction from the stock hover-thrust estimator, then vertical excitation regression a_z on sum u_meas (M1 on z) | |

Mass and inertia are never needed by the user: G1 is identified directly in normalised-torque units.

## 2. Methods (one estimator family, closed-loop aware)

- M1, effectiveness: per axis, inject a band-limited multisine/PRBS on the torque (or thrust) command with the
  existing M3a injector (MC_INDI_INJ_*), small amplitude (rotor-speed ripple below the G4 limit). Regress the angular
  (linear) acceleration, derived from the gyro (accel) through the same filter as the regressor, on the measured
  actuator increment du_meas from eRPM, with an intercept. Estimator = instrumental variables with the injected signal
  as instrument: consistent in closed loop, where ordinary least squares on closed-loop data is biased (the S42/S43
  failure). Data in saturation (any motor pinned, `torque_setpoint_achieved` false) is excluded.
- M2, actuator: from the same excitation, per motor, fit omega^2 response to the motor command (first order with
  separate up/down time constants plus dead time), and the static map command -> omega (W_MAX, thrust-curve factor).
- M3, telemetry latency: lag maximising the correlation between gyro-derived alpha and G1 du_meas, in loop periods.
- Each estimator has a synthetic self-test with a known answer including a closed-loop case (lesson 4) and a second,
  independently written key (lesson 17) before any value is used.

## 3. Procedure and what INDI does before identification

Proposed (option B): INDI arms before identification only in a conservative ident configuration: rate gains
MC_INDI_K_* halved and outer-loop gains reduced, so that a G1 wrong by x0.5 (loop gain x2, -6 dB) still leaves the
measured margins >= 6 dB / 45 deg (to be shown by G2 cells at G1 x0.5 and x2). The user takes off in altitude or
position mode, starts identification by parameter (autotune-style start, sequence roll, pitch, yaw, z, about 60 s
total), the module writes the parameters and sets an identification status parameter; full gains apply only when the
status is set and the identified values pass plausibility checks (identified vs derived within x3, fit residuals).
Without rotor-speed telemetry INDI refuses to arm (F-3 requirement).
Alternatives: (A) identification flown under the default PID stack, INDI selected afterwards (simple, the estimator
is controller-agnostic, but it requires a flyable PID tune first, which defeats "any quadcopter"); (C) refuse to arm
until an offline log-based identification has written the parameters (same estimator, run on a PID or bench log;
safest firmware, worst user flow); (D) online adaptive estimation in flight (adaptive INDI; needs saturation and
excitation guards, adds a flight-time fault path; kept as outlook). Derivation from CA_* and airframe data
(D-G1-DERIVE) stays as the initial guess and the plausibility reference, not the final value (inertia is rarely
known to 30 %).

## 4. Defaults (decision 4)

Gains that transfer are bandwidths: K_R/K_P/K_Y in rad/s (rate-error to angular-acceleration), outer-loop gains in
1/s, ACT_TC-relative lead (MC_INDI_LEAD, dimensionless). Physical parameters (G1, G2, W_MAX, ACT_TC, ERPM_DLY) have no
airframe-independent default: their firmware defaults are the conservative ident values of sec 3, and the
ident status parameter gates the full gains. The default set is written as `bench/params/indi_defaults.params` and
copied into the firmware defaults once G6 validates it (lesson 12).

## 5. Overturn

- M1 on the reference airframe differs from D-G1-DERIVE by > 15 % without an explained cause (D-G1-DERIVE overturn).
- The conservative ident configuration does not hold the 6 dB / 45 deg margins at G1 x0.5 (then the ident flight
  needs a different safe mode, re-open option A or C).
- The identification from x2 / x0.5 starts does not converge to within 10 % of the true quad5in values in SITL.
