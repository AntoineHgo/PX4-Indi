# S124 first offline roll G1 identification (quad5in, M3a hover logs pos0 / pos1)

Serves D-IDENT condition (ii) (instrument strength, CI per axis) and is the pretest for (i). Not a start-independence result.

## Commands
```
cd indi_flight
python3 bench/ident_fit.py results/ident_m3a_s123/pos0/flight.ulg --axis roll --t0 22.6 --t1 76.4
python3 bench/ident_fit.py results/ident_m3a_s123/pos1/flight.ulg --axis roll --t0 22.6 --t1 76.4
python3 -c "import test_ident_fit as T; ..."   # in bench/tests (pytest not installed on the host), see Self-test
```
Window = injection 20.6..78.4 s log time, 2 s trimmed at each end. Grid 800 Hz, 15-tap moving average on regressand,
regressor and instrument (same filter), 17 instrument lags (0..32 samples, step 2), Newey-West 400 lags (0.5 s).

## Model and units
alpha_roll [rad/s^2] = G1 * u_meas + c. alpha = d(sensor_gyro.x)/dt; u_meas = actuator_torque_measured.torque[0]
(normalised torque from esc rpm, (omega/MC_INDI_W_MAX 2700)^2 space, the units of MC_INDI_G1_R, IndiRateControl::setG1:
"angular acceleration per unit normalised torque"). Level u regressed with an intercept (equivalent to the increment).
Instrument = indi_rate_status.inject[0] (d). Timestamps: timestamp_sample for gyro, torque and inject;
control_allocator_status has no timestamp_sample (timestamp used, saturation mask torque_setpoint_achieved).

## Results (roll)
| log | G1 IV | 95 % CI | first-stage F | G1 OLS | n | excl. | xcorr lag | Hansen J (df 7) |
|---|---|---|---|---|---|---|---|---|
| pos0 (POS_EN 0) | 1748.9 | +-1.7 (0.1 %) | 4549 | 1748.9 | 42994 | 0 | 0.78 sample (0.97 ms) | 45 |
| pos1 (POS_EN 1) | 1747.3 | +-1.5 (0.1 %) | 4676 | 1748.3 | 42994 | 0 | 0.77 sample (0.96 ms) | 64 |

Latency compensation: the regressor time base is shifted by the lag that minimises the Hansen J (0.80 / 0.83 sample).
Without it (pass 1): pos0 IV 1759.3 / OLS 1746.9 / J 106; pos1 IV 1758.0 / OLS 1746.4 / J 106 (both within 0.1 % of 1757).

## References
- Derived (D-G1-DERIVE, `results/stage2_s46/derive_g1.md`, `bench/params/quad5in_indi_g1.params`): 1757 = torque per unit
  normalised command 2.4598 N m / Ixx 1.400e-3 kg m^2 (total inertia about CoG, base_link + 4 rotor links). Re-check by hand:
  4 rotors x arm 0.0795 m x (1.5e-6 x 2700^2 = 10.94 N) x 0.7071 (normalised roll row) = 2.459 N m. Same number, so it is
  the flown value, not an independent model value: the "model" and 1757 are one reference. Independent part: the identified
  value uses simulated rpm and gyro, not Ixx.
- Deviation of IV: pos0 -0.46 %, pos1 -0.55 % vs 1757 (pass 1: +0.13 %, +0.06 %).

## SNR verdict at INJ_AMP 0.003
F = 4500 (>> 10) and CI half-width 0.1 % (<< 5 %). Condition (ii) is met for the roll axis in this SITL, by a wide margin.
AMP could be cut by roughly 30x before F reaches 10, if a smaller excitation is wanted (unverified, noise scales are
those of the simulator).

## Self-test
bench/tests/test_ident_fit.py: synthetic closed loop (rate feedback at G1_set = 0.5/1/2 x true, coloured disturbance, 2-sample
telemetry delay, multisine injection), recovers G1 = 1700 to about -3 % (1653..1668), OLS is far lower (780..1270). Saturation
exclusion test included. All 3 tests PASS (run by calling the test functions directly, about 100 s, pytest absent on the host).

## Flags, unverified
- The residual difference IV vs 1757 (0.5 %) is far larger than the HAC CI (0.1 %): there is a systematic error of order 0.5-1 %
  (filter and latency handling, 15-tap smoothing, the Hansen J rejects at df 7). The CI is therefore not the whole error budget.
- OLS equals IV here because the simulated hover has almost no disturbance (gyro noise-free, peak corr 1.000); the closed-loop
  bias that IV protects against is demonstrated only in the synthetic test, not in these logs.
- Regressor is measured torque built with MC_INDI_W_MAX 2700 and CA_*: an error in W_MAX would scale G1 identically (G1 is
  identified in the controller's own normalisation, not in physical units).
- The xcorr lag is biased by feedback if disturbance dominates; the driver compensates with the J-minimising lag instead.
- Yaw / pitch not fitted. Start-independence (condition i) not tested (both logs flew G1 = 1757).
