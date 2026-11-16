# T79 second key: continuous-time models (S38), independent re-implementation

Script: `indi_flight/bench/second_key_models_s38.py` (numpy, continuous time). Written from the S35 note (sections 4, 7) and the task gains; `models_T78.md` and `margins_models.py` were read only after the numbers were computed.

Equations as implemented (T = 1/800 s, K = 20, g = 1, G1 = 320):
- INDI model-only: L = (K/s) F_w A_r + H (A_r - A_m), A_r = e^{-sT/2}/(1+0.033 s), A_m = e^{-sT}/(1+0.02 s), F_w = 2nd-order Butterworth 40 Hz, H = F_w / (1+s/(2 pi 20)).
- PID roll: L = G1 (Kp/s + Ki/s^2) A_r F_w + Kd G1 A_r F_w / (1+s/(2 pi 20)), Kp 0.03, Ki 0.06, Kd 0.0006 (task values, not re-checked against the airframe).
- H reading: the note's "derivative" in H would give a factor s and a non-dimensionless L. I read the derivative and the 1/s of the rate chain as cancelling, so H(0) = 1, matching note 4.1 ("H ~ 1") and T78 ("H = F alpha").

Numbers (dense log grid 0.1-400 Hz, PM = 180 + phase at |L| = 1, DM = PM(rad)/w_c):
- INDI model-only: fc 3.18 Hz, PM 43.55 deg, DM 38.0 ms, GM 6.53 dB at 6.19 Hz (second -180 crossing at 79.4 Hz, GM 53.4 dB, not the worst).
- PID roll: fc 1.48 Hz, PM 67.91 deg, DM 127.35 ms, GM 25.99 dB at 18.6 Hz.

Comparison with T78 at 800 Hz (sampled; T78 continuous model-only GM quoted as 6.3):

| Quantity | Mine (continuous) | T78 (800 Hz) | Difference | Allowance |
|---|---|---|---|---|
| INDI GM (dB) | 6.53 | 6.1 (6.3 cont.) | 0.23 | 1 dB |
| INDI PM (deg) | 43.55 | 42.7 | 0.85 | 3 deg |
| INDI DM (ms) | 38.0 | 36.5 | 1.5 | not in criterion |
| PID GM (dB) | 25.99 | 25.8 | 0.19 | 1 dB |
| PID PM (deg) | 67.91 | 67.9 | 0.01 | 3 deg |
| PID DM (ms) | 127.35 | 127.4 | 0.05 | not in criterion |

Verdict: AGREE. All GM and PM values fall within 1 dB and 3 deg. The INDI DM differs by 1.5 ms, more than the 0.7 ms T78 quotes for continuous vs sampled; DM is not in the criterion, so this is noted only.

Reduction check: with A_m = eta A_r and g = eta, L equals eta (K/s) F_w A_r with max relative error 0 for eta = 1, 0.5, 0.25. This is an algebraic identity (the mismatch term vanishes), so it checks the code path only.

Unsure:
- The model delay follows the task spec (one sample, e^{-sT}). The note's default d_m = 0 would change the result; T78 also uses the previous-setpoint sample.
- F_w and the 20 Hz filter are analog Butterworth/first-order forms, not PX4's bilinear biquads, so this is a continuous-time check only.
- PID gains and the sign of the D term (+Kd, per note 7.2) come from the task, not from the airframe; the note marks them UNVERIFIED.
- Single axis, no yaw spin-up term, no cross-coupling.
