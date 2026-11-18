# t181: x-axis G2 outer loop gain, diagnosis

## Cause: misread of the JSON, not an x-loop fault (a, b, c rejected)
`top_db` in `*_margins.json` is |L| at the LAST bin of the band (`bench/margins_est.py:254`,
`20*log10(|L[-1]|)`), i.e. 6.3 Hz: -37.2 dB (PT 0), -38.9 dB (PT 1). It is not the maximum of |L|.
The x loop is closed and has the expected gain. FRF recomputed from the *_pinj.csv with
`bench/margins_est.frf_periodic` (script `t181/frf.py`, numpy only, no flight):

| f Hz | 0.2 | 0.3 | 0.4 | 0.5 | 0.8 | 1.0 | 2.0 | 3.2 | 6.3 |
|---|---|---|---|---|---|---|---|---|---|
| PT0 abs L | 1.26 | 1.19 | 0.74 | 0.69 | 0.36 | 0.27 | 0.16 | 0.075 | 0.014 |
| PT0 arg L deg | -112 | -123 | -126 | -130 | -127 | -131 | -165 | 148 | 62 |
| PT0 accepted | no | no | no | yes | yes | yes | yes | yes | yes |
| PT1 abs L | 1.24 | 0.96 | 0.82 | 0.44 | 0.31 | 0.26 | 0.16 | 0.076 | 0.011 |

- Raw gain crossover is at about 0.3-0.4 Hz with arg L about -125 deg (PM about 55 deg), same on PT 0 and PT 1.
- The crossover is missing from the report only because the bins below 0.5 Hz (PT0) are rejected by the coherence
  gate (`_finish`, `margins_est.py:102-109`: min(g2x,g2y) < 0.8, 0.9 within one decade of a raw crossover). The
  report then says "max |L| = -3.2 dB at 0.50 Hz" (`gain_crossover.max_L_db`), which is the best accepted bin.
  Closed-loop coherence there is 0.75-0.78 at 0.2-0.3 Hz (JSON coh_x), 0.84-0.89 for y at 0.2-0.4 Hz.
- (d) Expected from stock gains (MPC_XY_P 0.95, MPC_XY_VEL_P_ACC 1.8, defaults in
  `src/modules/mc_pos_control/multicopter_position_control_gain_params.yaml`; the .params files do not override
  them): L = Kv (Kp + jw) / (jw)^2 (acceleration break, INDI makes a ~ c).
  0.5 Hz: 0.60 (measured 0.69); 1 Hz: 0.29 (0.27); 2 Hz: 0.14 (0.16). Matches within 15 percent; the
  xy/tilt conversion is already inside the INDI stage (a_ref in m/s2), so no extra scaling. The ideal crossing is
  Kv/w = 1 -> w about 1.9 rad/s, 0.3 Hz, i.e. below the 0.5 Hz where acceptance starts. z is higher
  (Kv 4.0, Kp 1.0: 0.62 Hz), so its crossing sits inside the accepted bins.
- (a) hover_long is mode "position" (`bench/scenarios.py:66`, hold 60 s); xy is closed by the stock position loop
  (y rms 0.064 vs d rms 0.113 m/s2, x rms 0.126: x responds to d, coherence >0.99 above 0.5 Hz). Rejected.
- (b) Plant response is visible: x (u = c + d, `McIndiPosControl.cpp:197`) follows d; not checked against
  vehicle_local_position acceleration directly (no pyulog/docker run). Unverified, but L consistent with the model
  makes a plant failure very unlikely.
- (c) Axis mapping consistent: param 1 -> `IndiPosInjection::axis()` returns 0 (`IndiPosInjection.hpp:66`),
  `inject(inject_axis)` (`McIndiPosControl.cpp:183`), pinj_csv axis 0 reads `inject[0]`, `a_c[0]`,
  `a_c_pre_inject[0]` (`pinj_csv.py:26-36`). Sign `L = -Gyd/Gxd` is the same as z. Rejected.

## Holes
The runs have sim_ground_truth 30 holes (0.10 percent missing, max 15 ms), sensor_gyro 21, controller
vehicle_angular_velocity 9 (`pt0_ax1_r400_s1_holes.txt`). These add broadband noise and likely contribute to the
coherence shortfall at 0.2-0.4 Hz (few cycles: Tp 10 s, 5 periods, 1 discarded, only about 4 averaged). Not proven.

## Smallest fix
No firmware change. (1) Scenario: raise the low-frequency excitation SNR on x: MC_INDI_PINJ_AMP 0.04 -> about 0.08
and/or NP 5 -> 8, TP 10 -> 20 so 0.2-0.4 Hz bins have more averages and a finer grid; rerun on a quiet host.
(2) Reporting: pinj_csv/margins should print the raw (unaccepted) gain crossover and label `top_db` as
"|L| at top of band", and warn when the raw crossover is in rejected bins (use `fc_raw` already in the FRF dict).
Raw crossover now: about 0.35 Hz (PT0 interpolating 0.3/0.4: 1.19 -> 0.74).
