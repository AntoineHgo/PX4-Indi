# S53: pitch M3a margins at the new defaults (ACT_TC 0.05, lead 1)

Set-up of `../act_tc_sweep/` with MC_INDI_INJ_AX 2 (pitch) and the pitch axis extracted (`m3a_csv.py ... 1`).
Binary 6e82b66300 (flights ran before the rebuild in `run_all.sh`), model-only path, quad5in, 800 Hz, MC_PITCH_P
default, AMP 0.001, plant tau 0.033 (ACT_TC x1.5).

| seed | PM deg | f_c Hz | GM dB | DM ms | Ms dB | pre-injection gate |
|---|---|---|---|---|---|---|
| 1 | 86.9 | 3.93 | 11.9 | 61.4 | 3.4 | PASS (RMS 0.0053/0.0028/0.0003, pin 0) |
| 2 | 86.8 | 3.91 | 12.0 | 61.6 | 3.4 | PASS (RMS 0.0031/0.0035/0.0005, pin 0) |

- Same as roll at x1.5 (PM 85.6, GM 11.3): the reference airframe is near-symmetric, as expected. 18/18 bins accepted
  on the pitch axis, so the injection was on pitch.
- Not a gate result (binary not at HEAD, not --gate, 800 Hz only, model-only path).
