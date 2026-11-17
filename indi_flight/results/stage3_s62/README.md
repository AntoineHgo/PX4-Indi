# S62: INDI attitude + torque steps after D-S3-ATT-STEP (setpoint lead), seeds 1-3

Provenance: SITL rebuilt at da64bc26b3 (`build.log`, rc 0, clean tree for firmware). Command: `fly_steps.sh` (quad5in,
sim v2, 800 Hz, speed 4, `indi.params` = stage3_s61/indi.params, seeds 1-3), 12 flights all rc 0 (`done.txt`).
b8866cd4b1 (yaw-filter toggle restart, T126 finding) came after the build; it only acts when the yaw cutoff changes in
flight, which these flights do not do. PID reference: symlinks to the unchanged S61 / indi_vs_pid PID flights.
Metrics: `python3 results/indi_vs_pid/plot_compare.py results/stage3_s62/steps_seedN` -> `steps_seedN/metrics.md`
(script still single-key; its header says "seed 1" for every folder, cosmetic).

| axis | overshoot % s1/s2/s3 | settle 2 % ms s1/s2/s3 | rise ms s1/s2/s3 | S61 (before) OS / settle |
|---|---|---|---|---|
| roll | 0.9 / 0.8 / 0.8 | 358 / 394 / 370 | 205 / 209 / 210 | 12.8-14.2 / 659-870 |
| pitch | 0.6 / 0.6 / 1.0 | 387 / 373 / 371 | 209 / 209 / 211 | 12.6-13.2 / 655-664 |
| yaw | 0.2 / 0.6 / 0.5 | 926 / 920 / 936 | 550 / 540 / 551 | 2.9-3.4 / 1273-1316 |
Model prediction (D-S3-ATT-STEP): 0.6 % / 388 ms (T124 key: 1.2 % / 294 ms). Flight agrees within 1 point: the decision's
overturn test is not triggered. G2-STEP limits (roll/pitch OS <= 5 %, settle <= 450 ms; yaw OS <= 5 %, settle <= 1350 ms)
are met on all 9 steps; this is a pre-test, not the gate's first test (metric second key pending, G1).
Rise 10-90 % is ~25 ms slower than before (205-211 vs 179-184 ms; PID 172-188).

Torque-step rejection kept and slightly better (peak angle roll 11.7-11.9 deg vs 12.9 in S61 seed 2, pitch 10.6-10.8 vs
12.4, yaw 4.3-4.4 vs 4.6; PID 14.5-15.6).
Open: r_dot_f noise in acro (stick) and hover effort (G4), attitude-break margin with the new setpoint path (G2).
