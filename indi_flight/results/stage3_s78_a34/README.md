# S78: A-34 closing test, setpoint-path lead in the linear model

No flight. Model: `indi_flight/bench/margins_models.py` `L_indi` with new options `fb_lead` (c = MC_INDI_LEAD x K x ACT_TC,
feedback lead (1+c) a_f), `att_p` (MC_ROLL_P attitude path closed around the M3a break), `sp_lead` (the da64bc26b3 term
c x r_dot, r_dot = discrete first order LPF, Tc 0.01 s, alpha = T/(Tc+T), of the backward difference of rate_sp, as in
`indi_rate_control.cpp` step 6c; the 1000 rad/s^2 clamp is nonlinear and ignored), `att_lat` (1 sample). Presets
`HEAD_FLIGHT` (sp_lead True) and `PRE_DA64` (sp_lead False). Plain `L_indi` defaults are unchanged (G2 tables, tests).
Flown config (all from the param files): measured-rotor path (CA_R_W_MAX 2700), Tb 0, n 1, K 20, MC_INDI_LEAD 1,
ACT_TC 0.05 -> c = 1 (< kMaxLeadGain 2), 800 Hz, MC_ROLL_P 8 (airframe 4040_gz_quad5in; not in the param files, taken from
the airframe; a21_compare_s41.py uses the same). G1 cancels in L (g = 1).
Measured bins: `results/stage3_s57/roll_m3a_meas800/meas800_s1_margins.txt` (S57), `results/stage3_s77_a34/tb0_margins.txt` (HEAD).
Reproduce: `python3 indi_flight/results/stage3_s78_a34/compare.py`, `table.py`. Self-test: `bench/tests/test_margins_selftest.py` test5.
Choices fixed before looking at the data: att_lat = 1, MC_ROLL_P = 8 (airframe), criterion as given by the task.

## Margins (worst crossing)

| | PM [deg] | f_c [Hz] |
|---|---|---|
| S57 measured | 77.5 | 3.08 |
| model PRE_DA64 | 76.4 | 3.68 |
| HEAD measured (tb0) | 69.1 | 4.07 |
| model HEAD_FLIGHT | 66.7 | 4.60 |
| shift measured | -8.4 | +0.99 |
| shift model | -9.7 | +0.92 |

Shift errors: PM 1.3 deg (<2), f_c 0.07 Hz (<0.3): PASS. Sign right. Without any lead/attitude path the model f_c is 2.74 Hz.

## Bins 1-8 Hz (model minus measured)
### S57 vs PRE_DA64
| f Hz | meas dB | model dB | d dB | meas deg | model deg | d deg |
|---|---|---|---|---|---|---|
| 1.0 | 11.4 | 12.9 | +1.5 | -163.6 | -146.5 | +17.1 |
| 1.3 | 7.5 | 9.1 | +1.6 | -148.2 | -136.4 | +11.8 |
| 1.6 | 4.7 | 6.4 | +1.7 | -135.4 | -127.4 | +8.0 |
| 2.0 | 2.5 | 4.1 | +1.6 | -121.1 | -117.7 | +3.4 |
| 2.5 | 1.1 | 2.3 | +1.2 | -108.9 | -109.8 | -0.9 |
| 3.2 | -0.2 | 0.8 | +1.0 | -101.8 | -104.6 | -2.8 |
| 4.0 | -1.1 | -0.5 | +0.6 | -100.2 | -103.7 | -3.5 |
| 5.0 | -2.3 | -1.7 | +0.6 | -102.7 | -106.1 | -3.4 |
| 6.3 | -3.6 | -3.2 | +0.4 | -106.8 | -111.7 | -4.9 |
| 7.9 | -5.1 | -4.9 | +0.2 | -114.0 | -119.8 | -5.8 |
### S77 tb0 vs HEAD_FLIGHT
| f Hz | meas dB | model dB | d dB | meas deg | model deg | d deg |
|---|---|---|---|---|---|---|
| 1.0 | 13.7 | 14.7 | +1.0 | -154.5 | -138.0 | +16.5 |
| 1.3 | 10.6 | 11.4 | +0.8 | -142.3 | -130.2 | +12.1 |
| 1.6 | 8.2 | 9.1 | +0.9 | -133.2 | -124.4 | +8.8 |
| 2.0 | 5.8 | 6.8 | +1.0 | -126.2 | -118.9 | +7.3 |
| 2.5 | 3.8 | 4.8 | +1.0 | -118.8 | -114.7 | +4.1 |
| 3.2 | 1.8 | 2.8 | +1.0 | -113.5 | -112.2 | +1.3 |
| 4.0 | 0.1 | 1.1 | +1.0 | -110.9 | -112.1 | -1.2 |
| 5.0 | -1.4 | -0.6 | +0.8 | -112.7 | -114.4 | -1.7 |
| 6.3 | -3.1 | -2.5 | +0.6 | -115.1 | -119.1 | -4.0 |
| 7.9 | -4.8 | -4.4 | +0.4 | -120.9 | -126.1 | -5.2 |

Absolute criterion (1 dB and 5 deg per bin): FAIL in both sets. Magnitude: max 1.7 dB (S57), 1.0 dB (HEAD, borderline, all bins
0.4-1.0 dB, model high). Phase: +17 deg at 1 Hz falling to 0 at ~3 Hz and -5 to -6 deg at 8 Hz, in both sets.
Shift between the sets (model shift minus measured shift, HEAD-S57): dB diff max 0.9 (1 Hz: 1.8 vs 2.3, ...), phase diff
max 5.0 deg (2.5 Hz: -4.9 vs -9.9), 4.4 at 3.2 Hz, <= 2.2 elsewhere; the common offset cancels. This is a supplementary view, not the criterion.

## Verdict: NOT CLOSED by the fixed criterion; the lead explains the shift

- The predicted PM shift (-9.7 vs -8.4 deg) and f_c shift (+0.92 vs +0.99 Hz) reproduce within the limits, and removing only
  `sp_lead` moves PM/f_c as the S77 trace said. da64bc26b3 is therefore the sufficient explanation of the change S57 -> HEAD
  in margins; no other firmware change is needed.
- What remains: the model does not match absolute bins. A phase offset of +17 deg at 1 Hz (model has less lag at low
  frequency) is the same in S57 and HEAD, so it predates the lead and is not part of A-34. Sensitivity (diagnostic only, not tuned):
  att_p 10 lowers it to 9-10 deg but raises dB error to 2.3-2.9; tau_r 0.04, lat 1, att_lat 4, gyro_fc 30 change it by <3 deg.
  Likely missing low-frequency dynamics of the attitude path (estimator lag, setpoint pipeline); unidentified.

## Unverified
- MC_ROLL_P 8 comes from the airframe file, not from a logged param of the flights (flight .ulg not opened here).
- att_lat 1 is an assumption (0 and 2 give the same margins within 0.2 deg).
- Clamp (1000 rad/s^2) and any other nonlinearity ignored; the attitude estimate is taken as the ideal integral of the roll rate.
- Not flown: the worktree at da64bc26b3^ (the direct test) is still pending.
