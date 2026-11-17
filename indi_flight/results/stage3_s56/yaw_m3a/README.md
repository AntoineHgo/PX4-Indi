# S56: yaw M3a after D-YAW-INV option (c)

Binary built at 23e9d30cc0 (option (c), before the landed-gate fix 296766019a, which only changes the first landed
cycle and is outside the injection window). quad5in, 800 Hz, model-only path, hover_long, speed 4, AMP 0.008,
bins 0.1-20 Hz, TP 10, NP 4, DLY 15, G1_Y 205, G2_Y 27, ACT_TC 0.05, LEAD 1 (`yaw_lf.params`, `run_all.sh`).

| seed | pre-inj gate | bins | f_c [Hz] | PM [deg] | DM [ms] | GM | Ms [dB] |
|---|---|---|---|---|---|---|---|
| 1 | PASS | 21/21 | 1.25 | 88.1 | 196 | no -180 crossing below 20 Hz (arg -170 at 20 Hz, |L| -17 dB) | 1.59 |
| 2 | PASS | 21/21 | 1.24 | 88.0 | 197 | same | 1.59 |

Before (S54, coded law, same set): |L| -0.4 dB at 0.1 Hz, L -> -1 at DC, no crossover, Ms 25 dB.
Model prediction (`bench/yaw_break_model_s54.py`, matched G2): K A/s, crossover 1.4 Hz, Ms 1.3 dB. Flight agrees
within 0.15 Hz and 0.3 dB. Seeds change sensor noise only (lesson 5): one sample of the plant.
GM is unread: the band ends at 20 Hz with |L| -17 dB at arg -170 deg; a G2 margin claim on yaw needs bins to ~40 Hz.
Files: `yaw_s{1,2}_margins.txt`, `yaw_s{1,2}_gate_preinj.md`; raw logs untracked.
