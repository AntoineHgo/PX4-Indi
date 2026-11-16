# S41 A-21 closing test 1, seed repeat

Model-only roll injection, `hover_long`, quad5in, seed 2, speed 4, `stage2_s40/pretest_inj/inj_model_long.params`
(AMP 0.005, DLY 20, NP 3, TP 10). Raw log untracked (`model_long_s2/`).

- Checks (`checks_model_long_s2.txt`, S40 checker): window 52.02-82.02 s, fault 0, landed 0, u = c + d 7.5e-9,
  generator 2.95e-9 at t0, height 4.94-4.91 m, max roll 3.96 deg.
- Margins (`margins_model_long_s2.txt`): PM 24.0 deg at 4.75 Hz, GM 6.0 dB at 7.66 Hz, DM 14 ms, 14/18 bins.
- With S40 (seed 1: AMP 0.005 PM 25.3 / GM 4.3 dB; AMP 0.01 PM 26.3 / GM 5.0 dB): PM within 2.3 deg -> test (1)
  PASS. GM spreads 1.7 dB because the phase lies within ~10 deg of -180 from 6.3 to 7.9 Hz (plateau, see S38 T80).
