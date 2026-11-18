# G2 yaw cross-check (S107, offline, host python3)

Tasks: 1 second key of L_indi_yaw (term by term) | 2 model GM/PM/DM for 8 cells | 3 table | 4 conclusion.
Status: all four tasks done (Task 1 section below). No model fix applied (no BLOCKING term-by-term discrepancy found); self-test untouched, still `python3 indi_flight/bench/tests/test_margins_selftest.py`.

## Task 2. Model margins (command)
```
cd indi_flight/bench && python3 -c "
import margins_models as M
for fs in (800.,400.):
  for p in ('meas','model'):
    m=M.margins_of(M.L_indi_yaw,fs,path=p); print(fs,p,m['gm_db'],m['pm_deg'],m['dm_s']*1e3,[x['f_c'] for x in m['crossings']])"
```
Config = YAW_FLIGHT defaults (K 10, G1 205, G2/G1 0.1317, tau_r .033, tau_m .05, gyro 40, dgyro 20, n 1, d_m 0, lat 0, Tb 0, c 0.5, att_p 3, att_lat 1, sp_lead).

| fs | path | GM dB | PM deg | DM ms | f_c Hz |
|---|---|---|---|---|---|
| 800 | meas | 24.47 | 79.2 | 119.9 | 1.84 |
| 800 | model | 18.68 | 83.6 | 139.1 | 1.67 |
| 400 | meas | 25.23 | 78.8 | 121.6 | 1.80 |
| 400 | model | 18.75 | 83.0 | 138.9 | 1.66 |

Sensitivities (GM/PM/DM, meas | model), 800 Hz: Tb 1.0 (flown MC_INDI_ACT_BLD default) 24.46/79.9/119.6 | unchanged (Tb only enters meas path; negligible);
Tb1 n2 25.19/79.9/121.4; lat 1 22.45/79.0/118.3 | 16.24/82.8/136.3; att_p 0 24.69/94.0/149.5 | 18.84/100.8/171.5.
Note: configs with ts_true=0 make margins_of hang (not investigated).

Extra sensitivities, 400 Hz meas: n2 22.08/78.9; n3 18.83/79.1; lat1 21.76/77.2; lat2 19.41/75.6; lat3 17.63/73.9; lat1 n2 19.50/77.4; tau_r .05 28.28/69.2;
ts_true x0.5 9.00/40.6 (model-only 32.88/44.3); ts_true x1.5 16.92/100.7 (model-only 13.51/95.4) -> yaw margins are very sensitive to J_r vs G2_Y match.
800 Hz meas: lat2 20.88/77.6, lat3 19.58/76.8. GM phase crossing of the meas model at 400 Hz: 30.6 Hz.

## Task 1. Second key, term by term (firmware src/lib/indi_rate_control/indi_rate_control.cpp, yaw/G2 part)
Re-derivation: t_cmd = t_fb + Delta; (G1 + G2/T (1 - z^-1)) Delta = nu - (1+c) a_f + c r_dot (line 458-459: numerator + g2_over_dt*prev_inc, divided by G1 + g2/dt;
prev_inc = t_cmd - t_fb of the previous cycle, line 477). Breaking at t_cmd with w = G1 Pn u, a = G1 Va u gives L = (K F Pn + (1+c) aF Va)/Dz - Tf, Dz = 1 + (G2/G1)(1-z^-1)/T.
This is exactly the code of L_indi_yaw (margins_models.py:164). Setpoint path K att_p and c r_dot lead: identical to L_indi (line 169).

| term | model value | status | evidence |
|---|---|---|---|
| law, backward Euler, G2/dt, Delta_{k-1} | Dz above | VERIFIED | indi_rate_control.cpp:442-459, 477 |
| c = min(lead K tau_c, kMaxLeadGain) | 0.5 (1 x 10 x 0.05) | VERIFIED | cpp:452, kMaxLeadGain 2 (hpp:301); params MC_INDI_LEAD 1, ACT_TC 0.05 (results/g2_rate_batch_s99/params_yaw.params:17-19), K_Y default 10 (mc_indi_rate_control_params.yaml:91-96) |
| K 10 | 10 | VERIFIED | yaml:96 default, not overridden in params_yaw.params |
| G1_Y 205, G2_Y 27 | ts_fw 0.1317 | VERIFIED | params_yaw.params (MC_INDI_G1_Y 205, G2_Y 27) |
| ts_true = J_r/(2 k_m w_h) | 0.1317 | PARTLY: k_m 1.9005e-8 VERIFIED (sim/models/quad5in/model.sdf:15-16, 1.5e-6 x 0.01267), formula/J_r 5e-6 from DECISIONS.md:54,241-245 (rotor izz 5e-5 = 10 x J_r) but the sdf rotor inertia itself was NOT found by grep in sim/models/quad5in (UNVERIFIED in-file); w_h 999 from DECISIONS only. Model-only cells agree with ts=0.1317 within 0.3 dB, which is an indirect check. MINOR |
| tau_r 0.033 | 0.033 | VERIFIED | model.sdf:12-13 timeConstantUp/Down 0.033 (modelled as 1st order on w^2 normalised torque: approximation, same as roll) |
| tau_m (ACT_TC) 0.05 | 0.05 | VERIFIED | params_yaw.params:17; model path uses t_alloc_prev (cpp:262-275) = zi factor in Tmod, d_m 0 = MC_INDI_DELAY default 0 |
| gyro 40 / dgyro 20 Hz | 40 / 20 | VERIFIED | results/g2_rate_pretest_s99/P2/s1/run.json:59-60 (imu_filter_hz) |
| YAW_CUT 0 (yaw LPF bypassed) | no filter | VERIFIED | yaml:209-214 default 0, cpp:121 bypass |
| meas delay n 1 | 1 | VERIFIED | MC_INDI_ERPM_DLY default 1 (yaml:134-139), McIndiRateControl.cpp:105 |
| blend Tb | 0 | UNVERIFIED -> now checked: flown MC_INDI_ACT_BLD default is 1.0 s (yaml:153-158); model with Tb 1.0 changes margins < 0.7 deg / 0.01 dB (800 Hz meas 24.46/79.9 vs 24.47/79.2). MINOR, YAW_FLIGHT left at Tb 0 (could be set to 1.0, not applied) |
| MC_YAW_P 3, yaw weight cancels | att_p 3 | VERIFIED | airframe 4040_gz_quad5in:81; AttitudeControl.cpp:54-55 (gain /= yaw_w) and :179 (error scaled by yaw_w) |
| att_lat 1, sp lead tc 0.01 | | VERIFIED as roll/pitch (same code path) | cpp:279, 399 |
| G1_true/G1_set (g = 1, eta = 1) | 1 | UNVERIFIED (assumed; G1_Y 205 derived in S47, no yaw identification in this note) | |
| 400 Hz: filters designed at fs vs IMU 800 | model uses fs | UNVERIFIED: run.json shows imu_rate 800 with rate_hz 400; model assumes the gyro filters run at the controller rate | MINOR |

No BLOCKING discrepancy in the law or parameters. Open observation: the attitude-path contribution in the model (att_p 3) costs 14.8 deg (meas) / 17.2 deg (model-only) of PM; measured PM sits 6-8 deg above the model, i.e. the flown loop behaves as if about half of that attitude term were present (cause not identified; stays within tolerance).

## Task 3. Cross-check table (measured: g2_rate_batch_s99/README.md, g2_rate_pretest_s99/README.md (P2), g2_crosscheck_s105.md Task 4; DM measured only where in READMEs)
Tolerance (GATES.md:128-131): |dPM| <= 10 deg and |dGM| <= 3 dB. delta = measured - model.

| cell (path Hz seed) | meas GM/PM/DM | model GM/PM/DM | dGM / dPM | within |
|---|---|---|---|---|
| meas 800 s1 | 21.53 / 87.1 / 154.6 | 24.47 / 79.2 / 119.9 | -2.94 / +7.9 | y |
| meas 800 s2 | 21.27 / 87.0 / 153.4 | 24.47 / 79.2 / 119.9 | -3.20 / +7.8 | n (0.2 dB over) |
| meas 400 s1 (P2) | 15.5 / 87.0 / 163.6 | 25.23 / 78.8 / 121.6 | -9.73 / +8.2 | n |
| meas 400 s2 | 16.17 / 86.5 / 161.2 | 25.23 / 78.8 / 121.6 | -9.06 / +7.7 | n |
| model 800 s1 | 18.43 / 91.0 / 137.6 | 18.68 / 83.6 / 139.1 | -0.25 / +7.4 | y |
| model 800 s2 | 18.40 / 90.0 / n.a. | 18.68 / 83.6 / 139.1 | -0.28 / +6.4 | y |
| model 400 s1 | 17.84 / 89.6 / n.a. | 18.75 / 83.0 / 138.9 | -0.91 / +6.6 | y |
| model 400 s2 | 17.79 / 90.2 / n.a. | 18.75 / 83.0 / 138.9 | -0.96 / +7.2 | y |

Explanations:
- PM: all 8 within 10 deg but systematically +6.4..+8.2 deg above the model (attitude term, see Task 1; OPEN cause, bounded: without the attitude path the model PM would be 94-101 deg, so measured lies between). DM measured is 15-30 percent above the model (154 vs 120 ms meas, 138 vs 139 model-only s1 OK) for the same reason; no DM tolerance exists.
- meas 800: GM short of the model by 3.0-3.2 dB. Quantified candidate: 2 samples (2.5 ms) of extra measured-path latency (lat 2) gives 20.88 dB, within 0.4-0.65 dB of measured. The roll measured cells show the same sign (roll 800 meas 0.9-1.0 dB, 400 meas 1.7-1.9 dB below model, S105).
- meas 400: GM 9.1-9.7 dB below the model. Extra latency alone does not reproduce it consistently: lat 3 (7.5 ms) gives 17.6 dB, lat2+n2 17.8; a single latency fitting 800 Hz (2.5 ms) gives only 19.4 at 400 Hz. The GM crossing is at 30.6 Hz (model); the model-only path, which shares plant, law and filters, agrees to 0.9 dB, so the discrepancy is confined to the measured-torque path (eRPM telemetry timing/rate at 400 Hz). Cause OPEN.

## Task 4. Conclusion
Can the 8 yaw cells be marked "cross-checked"? NO for all 8; YES for 4 of them.
- The 4 model-only cells (800/400 x 2 seeds): GM within 1 dB, PM within 7.4 deg: cross-checked.
- meas 800 s1: within tolerance (GM 2.94 dB); s2 is 0.2 dB over; defensible with the lat 2 explanation but that is a fitted, not a verified, cause. Mark as "cross-checked with note" at most, owner decision.
- meas 400 s1/s2: GM 9-10 dB below the model, no verified cause: needs an ANOMALIES.md entry (GATES.md:128-131) before the cells are used. The measured margins themselves are well above the 6 dB gate (15.5 dB) so this is a model-fidelity gap of the measured-torque path, not a safety failure.
Next step (not done, needs the sim): FRF of the measured-torque path alone at 400 Hz (eRPM telemetry rate/latency) and a yaw J_r check from the sdf.
