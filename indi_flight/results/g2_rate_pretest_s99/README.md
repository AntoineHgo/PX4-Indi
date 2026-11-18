# S99 G2 rate-loop margin pre-test (2 flights, HEAD firmware)

Recipe: S57 `roll_m3a_meas800` (meas800.params, sim v2, CA_R_W_MAX 2700, hover_long, indi_m3a, speed 4, seed 1, ACT_TC 0.05, lead 1, G2_Y 27, TP 10, bins 1-60 Hz, AMP 0.001).
Changed only: injection axis (MC_INDI_INJ_AX 2 = Pitch for P1, 3 = Yaw for P2; roll was 1) and controller rate (`--rate-hz` 800 for P1, 400 for P2).
Serial run: `bash indi_flight/results/g2_rate_pretest_s99/fly.sh`. Params: `P1.params`, `P2.params` (same dir).

| flight | axis | rate | gate | f_c [Hz] | PM [deg] | GM [dB] | DM [ms] | bins |
|---|---|---|---|---|---|---|---|---|
| P1 | pitch | 800 | PASS | 4.15 | 69.0 | 15.7 | 46.2 | 18/18 |
| P2 | yaw | 400 | PASS | 1.48 | 87.0 | 15.5 | 163.6 | 18/18 |

Checks:
- Flew: armed by external command, took off and flew hover_long, no crash or failsafe in px4.log, exit=ok.
- Injection on named axis only: m3a_csv.py per axis (0,1,2). P1 injects on axis 1 (pitch) only. P2 injects on axis 2 (yaw) only.
- Logged rates (check_rates.py): P1 actuator_motors/sensor_gyro 800 Hz, dt 1.25 ms; P2 400 Hz, dt 2.5 ms. esc_status median at the controller rate, mean 764 / 381 Hz. No logger dropouts.
- Margin script: no warnings emitted, all 18 bins accepted.
- Note: the script's crossover is the first crossing; P2 has low crossover (1.5 Hz) and large DM. Only one seed, so no repeatability estimate.

Commands:
- `bash indi_flight/results/g2_rate_pretest_s99/fly.sh` (driver; per flight: `run_scenario.py --scenario hover_long --controller indi_m3a --seed 1 --speed 4 --model quad5in --rate-hz {800|400} --sim v2 --params {P1|P2}.params --out <dir>/s1`, then `check_rates.py`, `pretest_gate.py --delay 4 --length 15`, `m3a_csv.py <ulg> {1|2} <csv>`, `m3a_margins_pretest.py <csv> 1 60 10 {800|400}`).
