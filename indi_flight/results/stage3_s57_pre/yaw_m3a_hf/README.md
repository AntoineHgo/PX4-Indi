# S56: yaw M3a gain margin read, bins 5-40 Hz (option (c), firmware 296766019a)

Same set as `../../stage3_s56/yaw_m3a/` except FMIN 5, FMAX 40 (`yaw_hf.params`, `run_all.sh`). Binary rebuilt at
the firmware of 296766019a (run.json records the HEAD at run time, docs/results commits only after it).

| seed | gate | bins | phase crossing [Hz] | GM [dB] | |L| at 5 Hz [dB] | Ms [dB] |
|---|---|---|---|---|---|---|
| 1 | PASS | 10/10 | 22.2 | 18.5 | -5.3 | 1.60 |
| 2 | PASS | 10/10 | 21.9 | 18.3 | -5.2 | 1.62 |

Overlap with the 0.1-20 Hz run (S56): |L| and arg agree within 0.1 dB / 0.5 deg at 5-20 Hz.
Yaw M3a at 800 Hz, matched plant: PM 88 deg (f_c 1.24 Hz), DM 197 ms, GM 18.4 dB (22 Hz), Ms 1.6 dB.
