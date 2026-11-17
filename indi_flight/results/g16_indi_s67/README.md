# G16 determinism batch: same-seed INDI step_roll repeats

Scenario step_roll, seed 1, 400 Hz, indi, quad5in, params `results/g2_step_s64_400/indi.params`.
`fly.sh`: s4_r1..s4_r5 at --speed 4 (5 in parallel), then s1_r1..s1_r3 at --speed 1 (3 in parallel, -t 2400).
done.txt: all 8 runs rc=0, then ALLDONE.
Metrics: `python3 bench/g2_step_metrics.py results/g16_indi_s67/g2_step_primary.json <8 flight dirs>` (run from `indi_flight/`), output `g2_step_primary.json`. All 8 pass.

Times are PX4 time (us, converted to s): arm = `t_arm_us` in run.json, step = `t_on_us` in the metrics JSON.
`gz arm cmd` = `t_arm_sent_s` in run.json (scenario clock, read as gz sim time; not independently verified).
The ULog was not parsed directly because `pyulog` is not installed on the host.
gz.log has no arm line to cross-check against.

| run | speed | rc | rise ms | settle ms | OS % | arm PX4 s | gz arm cmd s | step PX4 s |
|---|---|---|---|---|---|---|---|---|
| s4_r1 | 4 | 0 | 202.70 | 356.25 | 0.65 | 30.370 | 30.01 | 57.391 |
| s4_r2 | 4 | 0 | 205.18 | 363.75 | 0.74 | 30.723 | 30.00 | 57.745 |
| s4_r3 | 4 | 0 | 206.09 | 348.75 | 1.23 | 30.696 | 30.01 | 57.719 |
| s4_r4 | 4 | 0 | 202.33 | 357.50 | 0.53 | 30.075 | 30.00 | 57.088 |
| s4_r5 | 4 | 0 | 202.05 | 358.75 | 0.85 | 30.338 | 30.01 | 57.363 |
| s1_r1 | 1 | 0 | 208.90 | 356.25 | 0.59 | 30.780 | 30.00 | 57.791 |
| s1_r2 | 1 | 0 | 207.63 | 356.25 | 0.72 | 30.792 | 30.00 | 57.804 |
| s1_r3 | 1 | 0 | 205.74 | 343.75 | 0.96 | 30.832 | 30.00 | 57.856 |
| a30 A (ref) | 4 | 0 | 210.0 | 356.25 | 0.54 | - | - | - |
| a30 B (ref) | 4 | 0 | 205.6 | 360.0 | 1.18 | - | - | - |
| a30 C (ref) | 1 | 0 | 208.8 | 356.25 | 0.41 | - | - | - |
| S64 seed 1 (ref) | 4 | - | 188.7 | 312.5 | 1.78 | - | - | - |

Same-seed spread (max - min)

| speed | n | rise ms | settle ms | OS % pts |
|---|---|---|---|---|
| 4 | 5 | 4.04 (202.05 to 206.09) | 15.00 (348.75 to 363.75) | 0.70 (0.53 to 1.23) |
| 1 | 3 | 3.16 (205.74 to 208.90) | 12.50 (343.75 to 356.25) | 0.37 (0.59 to 0.96) |

S64 seed 1 (188.7 / 312.5 / 1.78 %) is outside the new spread on all three metrics, for both speeds.
Rise is 13.4 ms below the speed-4 minimum, settle is 36.3 ms below, and OS is 0.55 pts above the speed-4 maximum.

Arm and step timing
- The arm instant varies by 757 ms across runs (30.075 to 30.832 s PX4 time).
- Step onset minus arm is 27.011 to 27.024 s in every run, so the step follows arming. The step time varies by the same amount.

Notes
- s4_r5 truth settle is 2021.25 ms, while the estimated settle is 358.75 ms. The metric passes, but this truth value looks like an outlier and was not checked further.
- Reference rows A, B, C and S64 are copied from the a30_refly_s67 README. Their arm and step times were not extracted.
