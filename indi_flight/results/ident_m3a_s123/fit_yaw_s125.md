# S125 yaw G1_Y and G2_Y identification (two-regressor IV), quad5in

## Commands
```
cd indi_flight   # ulimit -v 4000000, host python, no pytest
python3 bench/ident_fit_yaw.py results/ident_m3a_s123/axyaw/flight.ulg --axis yaw --t0 22.1 --t1 76.0
python3 bench/ident_fit_yaw.py results/ident_m3a_s123/half_ax3/flight.ulg --axis yaw --t0 22.1 --t1 76.0
python3 bench/ident_fit_yaw.py results/ident_m3a_s123/axyaw/flight.ulg --axis yaw --t0 22.1 --t1 76.0 --g1-only
python3 bench/ident_fit_yaw.py results/ident_m3a_s123/pos0/flight.ulg --axis roll --t0 22.6 --t1 76.4
python3 bench/tests/test_ident_fit_yaw.py            # BREAK=1|2|3 env var breaks one test each
```
bench/ident_fit.py untouched; new files bench/ident_fit_yaw.py, bench/tests/test_ident_fit_yaw.py (imports _lead,
update_rate, chain_mismatch, load, GATE, SHIFT range from ident_fit; 2SLS and SW F are new because iv_effectiveness
takes one instrument series).

## Model and firmware convention
alpha = G1 u + G2 du/dt + c; u = actuator_torque_measured.torque[axis]; du/dt in 1/s, so G2 is rad/s^2 per (unit
torque / s) = rad/s. Firmware: src/lib/indi_rate_control/indi_rate_control.cpp:456-459 `g2_over_dt = _g2_yaw / dt`,
`dt_cmd = (nu - (1+c) a_f + g2_over_dt * prev_inc) / (G1 + g2_over_dt)`, i.e. backward Euler of (G1 + G2 s) Delta;
header indi_rate_control.hpp:60-63; the clamp to G2 >= 0 at hpp:117. So G2 multiplies the time derivative of the
commanded torque (increment), not a per-sample difference; the plant model in indi_rate_control_test.cpp:1853 is
`accel = g1 m + g2 (m - m_old)/dt`, same sign (G2 > 0 adds with G1). The fit uses the MEASURED u (same quantity in
the quasi-static band; the shift scan aligns it). Note the brief said "opposite sign": the fit gives G2 > 0 in the
firmware convention (same sign as G1 u), no sign flip applied.
Filters: y = F[D w]; x1 = F[C u]; x2 = F[D u] (gain sinc, same as the D in y); instruments z1 = F[C d] lags 0..32 step 2
(17) and z2 = F[D d] lags 0..32 step 4 (9); F = 15-tap MA, 800 Hz grid, rows decimated by the true update period (2),
common integer latency shift of both regressors by min Hansen J over -2..12, Newey-West 400 lags.
First stage: Sanderson-Windmeijer conditional (other regressor's fitted values removed), classical and HAC effective
(Montiel Olea-Pflueger form as ident_fit.robust_first_stage_f). Gates: F_eff >= 10 per regressor, J/df <= 20,
interior shift, CI/G1 <= 0.15, CI/G2 <= 0.5 (new, my choice), chain match, excluded fraction.

## Results (yaw window 22.1-76.0 s log time; derived G1_Y 205, G2_Y 27)
| log | G1_Y | 95 % CI | G2_Y | 95 % CI | F_eff G1 / G2 | J (df 8) | shift | gates |
|---|---|---|---|---|---|---|---|---|
| axyaw (S124 gains) | 163.1 | +-1.2 (0.7 %) | 27.53 | +-0.045 (0.2 %) | 3926 / 91461 | 90.6 (J/df 11.3) | 1 | PASS |
| half_ax3 (K_Y 5, YAW_P 1.5) | 166.0 | +-1.1 (0.7 %) | 27.54 | +-0.045 (0.2 %) | 21371 / 45071 | 96.0 (12.0) | 1 | PASS |
| axyaw, G1-only (S124 model, full instrument set) | 18.3 | +-13.6 (75 %) | - | - | - | 107 | -2 | no G2 |
| roll pos0 (sanity) | 1751.8 | +-2.1 (0.1 %) | -3.59 | +-0.04 | 1413 / 14480 | 13.5 (1.7) | 2 | PASS |

Robustness (axyaw): ntaps 7 / 31: G1 163.8 / 161.4, G2 27.84 / 27.41; first half / second half of window: 163.4 / 163.0,
G2 27.53 / 27.54; shorter lag sets: 162.7, 27.52.
Reading:
- G2_Y = 27.5, +2 % from the derived 27 and stable (CI 0.2 %, too small to be the real error; systematic spread across
  settings about 1 %). D-G2Y-DERIVE is confirmed in the "within 30 %" sense.
- G1_Y = 163-166, NOT 205 (-19 to -20 %), identical at both control gains and across windows/filters, so it is not a
  closed-loop artefact of this method. Either the sim's yaw effectiveness is ~165 (derive_g1.md uses yaw torque
  0.5544 N m / Izz 0.0027 = 205; torque or Izz in Gazebo differs by 20 %), or the normalised u measured for yaw is
  scaled differently. NOT resolved here. If the true G1_Y is 165, the derived G2/G1 = 0.132 s differs from the
  identified 27.5/164 = 0.168 s (+27 %), so D-G2Y-DERIVE's J_r/(2 k_m w_h) ratio is also off, while the G2 absolute is close.
- Roll: G1_R 1751.8 (-0.3 % vs 1757), G2_R = -3.6 = 0.2 % of G1_R, not zero in CI terms. Interpretation (unverified):
  G2 = G1 * residual delay; -3.6/1751.8 = -2 ms is the sub-sample latency (the shift is integer 1.25 ms steps and the
  scan optimum is jagged). The same artefact would move G2_Y by about G1_Y x 2 ms = 0.3 (1 %), the order of the
  robustness spread. G2_R has no physical meaning.
- Hansen J/df 11-12 on yaw (gate 20) is significant: CI is not the whole error budget; the jagged J curve (min only at
  one shift, 263 vs ~490) indicates alignment sensitivity at the 400 Hz update grid.

## Self-test (bench/tests/test_ident_fit_yaw.py, plain python, all 4 pass)
Synthetic 800 Hz closed loop, G1 200, G2 27, rate feedback with g1_set 100/200/400, first-order actuator lag 20 ms,
2-sample telemetry delay, coloured disturbance, multisine 1-60 Hz amplitude 0.03.
1. test_recovers: G1 within max(5 %, 1.5 CI), CI < 10 %, G2 within 8 %, all gates pass (the g1_set 100 case lands at
   -6 % of G1, inside its 11 CI; stat. fluctuation, seed 4 gives +2 %).
2. test_omitting_du_dt_biases_g1: G1-only fit deviates > 10 % (seed 5).
3. test_no_spinup_gives_g2_zero: G2 true 0 gives |G2| < 2.2.
4. test_mismatched_filter_is_caught: regressors re-filtered with 7 taps instead of 15: G1 1961, J/df 13, verdict fails
   (chain gain match and G2 CI gates).
Break-once evidence: BREAK=1 (fit without du/dt in test 1) fails with G1 2074; BREAK=2 (full fit in the omission
test) fails with G1 197.8; BREAK=3 (no mismatch) fails the "must fail a gate" assertion. BREAK=0 restores all passing.

## Flags / unverified
- The G1_Y 163-166 vs 205 discrepancy (-20 %) is unexplained; check Gazebo yaw torque / Izz, the CA KM sign/scale.
- Measured u used, not the commanded Delta the firmware acts on; roll G2 -3.6 shows residual delay leaks into G2 (~1 %).
- SW F is classical + HAC-effective; no weak-instrument-robust CI (Anderson-Rubin) computed.
- Self-test plant has G2 acting on actual u with the measurement delayed; real-plant rotor dynamics beyond one lag untested.
