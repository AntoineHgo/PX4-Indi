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

## S124 start independence (D-IDENT condition (i), roll only)

Flights: same command as fly.sh with `--params inj_g1x0p5.params` / `inj_g1x2.params` (G1_R/P/Y all scaled x0.5 / x2,
gains not halved, POS_EN 0), `--out g1x0p5` / `g1x2`, containers s124x0p5 / s124x2 (run in parallel).
Fit: `python3 indi_flight/bench/ident_fit.py <ulg> --axis roll --t0 <inj start+2> --t1 <inj end-2>`.

| start G1_R | flown | inj window (s) | max roll (deg) | IV G1_R | 95 % CI | F | J (df 7) | vs 1757 |
|---|---|---|---|---|---|---|---|---|
| x0.5 | 878 | 20.7-78.5 | 3.4 | 1742.3 | +-1.9 | 27091 | 89.1 | -0.8 % |
| x1 (pos0) | 1757 | 20.6-78.4 | 7.3 | 1748.9 | +-1.7 | 4549 | 45 | -0.5 % |
| x1 (pos1) | 1757 | 20.6-78.5 | 7.2 | 1747.3 | +-1.5 | 4676 | 64 | -0.6 % |
| x2 | 3514 | 18.7-76.7 | 18.7 | 1756.1 | +-1.3 | 902 | 14.0 | -0.05 % |

Spread across starts (max-min)/mean = 0.8 % (limit 10 %); each within 0.8 % of 1757 (limit 10 %). The estimate
does NOT follow the start (start x4 range -> 0.8 % change), but a small monotonic trend with the start exists
(1742 -> 1756), larger than the CI: CI is not the whole error budget (J significant). Roll axis only; pitch and yaw
not flown. x2 start = lower loop gain, larger roll (18.7 deg) and weaker instrument (F 902, still >> 10).
Status: roll (i) and (ii) met in SITL, UNKEYED until K124 (design/key_k124_ident_fit.md) closes.

## S124 pitch and yaw (G1 x1, INJ_AX 2 / 3, inj_axpitch/axyaw.params, out axpitch / axyaw)

| axis | inj window (s) | IV G1 | 95 % CI | OLS | F | J (df 7) | derived | dev |
|---|---|---|---|---|---|---|---|---|
| pitch | 20.0-78.0 | 1634.1 | +-1.3 (0.1 %) | 1632.4 | 4297 | 88.2 | 1640 | -0.4 % |
| yaw | 20.1-78.0 | 102.8 | +-15.0 (14.6 %) | 111.8 | 11292 | 107.1 | 205 | -50 % |

Pitch: consistent with roll. Yaw: NOT a valid estimate. ident_fit.py regresses alpha = G1 u + c only; in yaw the
rotor spin-up reaction torque (G2_Y du/dt, opposite sign, comparable size at injection frequencies up to 60 Hz) is
omitted and biases G1_Y down, and the CI is 15 %. Yaw needs a two-regressor IV (u, du/dt) with two instrument sets
(decision 5, D-YAW). Yaw ident = open item for S125. Yaw flight first attempt left an empty output dir (container
did not start in the parallel launch, cause not investigated); re-flown alone, ok.

## S125 halved-gain ident config (D-IDENT: ident flies at halved gains)
Params `inj_half_ax1.params` (= inj_pos1 + MC_INDI_K_R/P 10, K_Y 5, MC_ROLL_P/PITCH_P 4, MC_YAW_P 1.5), script
`fly_half.sh`, out `half_ax1` (status ok). Fit (post-K124-fix ident_fit.py, same window 22.6-76.4):
`python3 bench/ident_fit.py results/ident_m3a_s123/half_ax1/flight.ulg --axis roll --t0 22.6 --t1 76.4`
-> G1_R 1757.9 (CI +-0.1 %), OLS 1755.1, robust F 1765, J/df 14.8, shift 0, IDENT PASS. Derived 1757 (+0.05 %);
full-gain x1 gave 1767-1768 (+0.6 %). Halved gains do not degrade the estimate; F lower (1765 vs ~4600) but far
above 10. Yaw half_ax3: first launch left an empty dir (as S124), re-flown alone.
