# S54: A-27 yaw M3a re-fly at 0.1-20 Hz -- mechanism found, M3a degenerate for yaw

Binary built at 7522625b0f, quad5in, 800 Hz, model-only path, hover_long, seed 1, speed 4, AMP 0.008,
MC_INDI_INJ_FMIN 0.1, FMAX 20, TP 10, NP 4, DLY 15 (`yaw_lf.params`, `run_all.sh`).

- Pre-injection gate PASS (rate RMS 0.0042/0.0056/0.0003 rad/s), 21/21 bins accepted.
- `yaw_s1_checks.txt` [5] shows max|logged d - expected| = 0.118: `stage2_s40/pretest_inj/checks.py` hard-codes
  TP 10, FMIN 1, FMAX 60, so its "expected" signal is the S40 multisine, not this one. Not a firmware fault; the FRF
  uses the logged d, x, y. (S53 with the S40 set: 6.9e-9.)
- |L| -0.4 dB at 0.1 Hz, -0.5 dB at 1 Hz, -19.8 dB at 20 Hz; arg 178 deg at 0.1 Hz, 157 at 1 Hz, -4 at 20 Hz.
  L -> -1 at DC. No gain crossover; Ms 25 dB at 0.1 Hz (`yaw_s1_margins.txt`).

## Mechanism (from `indi_rate_control.cpp` step 8, l.386-390)

dt_cmd = [nu - (1+c) a_f + (G2/dt)(t_f - t_f,prev)] / (G1 + G2/dt). For yaw at 800 Hz, G2/dt = 27 x 800 = 21600
against G1 = 205: the denominator is ~105 G1. So per sample t_cmd ~ t_f + (t_f - t_f,prev) (one-step extrapolation of
the filtered actuator state) and the nu and a_f terms enter with gain ~1/105 of the G1-only law. At the M3a break
(d fed to plant AND model) y ~ H A_m x, so L ~ -H A_m: -1 at DC, phase 180 minus the model+filter lag. The a_f term
that cancels t_f on roll (y = t_f - a_f/G1 + ...) is ~100x too small on yaw to do so.

Model (`bench/yaw_break_model_s54.py`, UNKEYED, crude margin read-out, `../yaw_model/model_out.txt`): yaw G2 27 at
M3a |L| -0.6 dB / arg 160 at 1 Hz (flight -0.5 / 157), -10.5 / 72 at 10 Hz (flight -11.6 / 53), -16.7 / 24 at 20 Hz
(flight -19.8 / -4). With G2 0 the same model gives a roll-like integrator loop (crossover 1.4 Hz).

## Consequences

1. No yaw margin can be read at M3a with this law: the break measures the actuator-model positive-feedback loop,
   whose gain is 1 at DC by construction. A-27 is explained (not a sign error, not a measurement fault).
2. The law's yaw inversion assumes the rotor reaches the commanded speed within one sample (dead-beat spin-up torque
   G2 du/dt). With the 33 ms motor lag that does not hold, and the yaw feedback gain is set by G2 rather than K_Y.
   This re-opens D-G2Y-DERIVE's *form* (the value 27 is not in question): see D-YAW-INV (PROPOSED) in DECISIONS.md.
3. The yaw row of the G2 table waits for D-YAW-INV and a yaw break choice (plant-only break, or M3a on the new law).
