# S53: ACT_TC error sweep with the rate lead (MC_INDI_LEAD 1)

Same set-up as `results/stage3_s52/m3a_lead/` (binary 6e82b66300 + logging-only reset fix not rebuilt; model-only
path, quad5in, hover_long, speed 4, roll M3a torque-setpoint break, AMP 0.001, 18 bins 1-50 Hz, MC_ROLL_P 8, 800 Hz).
Plant motor tau 0.033 s. Params = S52 `lead1_tc20.params` with MC_INDI_ACT_TC changed (`tc*.params`). Flown by
`run_all.sh` (two parallel streams of `fly.sh TC SEED`), scored by `post.sh` (S48 instrument, second-keyed S40,
JOURNAL l.277). Pre-injection gate window: first airborne + 4 s, 15 s.

| ACT_TC | x plant | seed | PM deg | f_c Hz | GM dB | DM ms | Ms dB | pre-injection gate |
|---|---|---|---|---|---|---|---|---|
| 0.0165 | 0.5 | 1 | 36.2 | 3.65 | 5.1 | 27.5 | 8.4 | PASS (RMS 0.0028/0.0031/0.0006, pin 0) |
| 0.020 (S52) | 0.6 | 1, 2 | 42.0, 42.0 | 3.33 | 7.9, 7.8 | 35 | 6.1 | PASS |
| 0.033 (S52) | 1.0 | 1, 2 | 59.1, 59.1 | 2.88 | 13.9, 14.3 | 57 | 2.8 | PASS |
| 0.050 | 1.5 | 1 | 85.6 | 3.99 | 11.3 | 59.6 | 3.6 | PASS (RMS 0.0030/0.0032/0.0003, pin 0) |
| 0.066 | 2.0 | 1 | 75.0 | 7.03 | 10.0 | 29.6 | 4.3 | PASS (RMS 0.0038/0.0035/0.0003, pin 0) |
| 0.066 | 2.0 | 2 | 75.2 | 7.02 | 10.0 | 29.7 | 4.3 | PASS (RMS 0.0035/0.0037/0.0004, pin 0) |

- Asymmetric tolerance, as the unit test predicted (S52): over-estimating tau_c by up to x2 keeps PM >= 75 deg and
  GM >= 10 dB; under-estimating fails G2 already at x0.6 (PM 42) and at x0.5 also GM (5.1 dB < 6).
- Over-estimation over-compensates the actuator pole: |L| stays at +2 dB from 2 to 5 Hz at x2 and the crossover moves
  from 2.9 to 7.0 Hz, so the delay margin falls back to 30 ms (still >> 2 periods + telemetry latency, ~5 ms).
  Beyond x2 the crossover would keep rising towards the filter/delay phase drop: not measured, do not extrapolate.
- Limits: roll only, 800 Hz only, model-only path, one airframe; not --gate (binary not at HEAD).
