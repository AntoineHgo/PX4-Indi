# S61: INDI vs PID attitude steps, seeds 2 and 3 (owner note N1 item B.1), and the overshoot mechanism

Provenance: clean tree, SITL rebuilt at d7c637cb20 (`build.log`, rc 0; firmware unchanged since), flights at 1462fb8aed.
Command: `results/stage3_s61/fly_steps.sh` (same as `results/indi_vs_pid/fly.sh`: quad5in, sim v2, 800 Hz, speed 4,
`indi.params` / `pid.params` copied from there; seeds 2, 3). 16 flights, all rc 0.
Metrics: `python3 results/indi_vs_pid/plot_compare.py results/stage3_s61/steps_seedN` -> `steps_seedN/metrics.md`
(script not second-keyed yet: needed before the G2-STEP gate's first test).

| axis | ctrl | overshoot % s1/s2/s3 | settle 2 % ms s1/s2/s3 | rise ms s1/s2/s3 |
|---|---|---|---|---|
| roll | INDI | 13.8 / 14.2 / 12.8 | 659 / 870 / 682 | 179 / 181 / 184 |
| roll | PID | 0.0 / 0.0 / 0.0 | 380 / 408 / 405 | 183 / 186 / 188 |
| pitch | INDI | 12.6 / 13.1 / 13.2 | 664 / 655 / 664 | 184 / 183 / 188 |
| pitch | PID | 0.0 / 0.0 / 0.0 | 389 / 408 / 412 | 172 / 180 / 188 |
| yaw | INDI | 3.4 / 3.2 / 2.9 | 1303 / 1316 / 1273 | 476 / 476 / 481 |
| yaw | PID | 0.2 / 0.3 / 0.3 | 1233 / 1203 / 1240 | 660 / 656 / 669 |
Seed 1 = `results/indi_vs_pid` (dirty tree). The gap holds on all three seeds. Torque-step rejection (INDI better,
yaw 4.6-4.8 deg vs 14.4-14.5) also holds (`steps_seed2/metrics.md`, `steps_seed3/metrics.md`).

## Mechanism (found, model-checked)
1. Closed rate loop, flight: first order + delay fitted on rate_sp -> rate (`bench/rate_fit.py`, run in docker, scipy):
   INDI roll 79 ms + 23 ms, pitch 81 + 21, yaw 132 + 30 (fit RMS 2 % of signal); PID 12-15 ms + 30 ms.
2. Achieved angular accel vs nu (indi_rate_status, 800 Hz, step window): a_f = 0.48 nu, 24 ms later (residual 1-2 %),
   seeds 1 and 2.
3. Cause: the D-RATE-LEAD law nu - (1 + c) a_f, c = K tau_c = 1, is feedback-only. Closed rate loop
   tau s^2 + (1 + K tau_c) s + K: dominant pole 12.6 rad/s (79 ms) at K 20, tau 33 ms, tau_c 50 ms. With MC_ROLL_P 8 on it
   the attitude loop has zeta ~0.6 plus delay -> 13-14 % overshoot, slow settle. Not a G1 error.
4. Linear model (`bench/att_step_model.py lead`, plant tau 33 ms, tau_c 50 ms, delay 10 ms): reproduces the flight
   (rate loop 76 + 22 ms, overshoot 15.4 %, settle 808 ms). Predictions: setpoint lead (nu += K tau_c r_dot_sp)
   overshoot 0.6 %, settle 388 ms; full r_dot feedforward (kff 1 + K tau_c) 0 %, 705 ms. Same at 20 ms delay.
   The model script is single-key (second key pending, lesson 17).
5. Second key T124 (haiku, independent derivation, `design/t124_second_key_att_model_s61.md`, script
   `bench/t124_att_step_key.py`): rate-loop poles -12.63 / -47.97 (tau 79 ms) AGREE; overshoot kff 0: 16.1 % (vs 15.4),
   kff = K tau_c: 1.2 % (vs 0.6), kff 1 + K tau_c: 0 % AGREE. Settle 2 % kff = K tau_c: 294 ms vs 388 ms here, kff 2:
   532 vs 705 (kff 0: 820 vs 808): the slow tail sits at the 2 % band edge, so settle is sensitive to integration
   detail; both keys predict a pass of G2-STEP (<= 450 ms). The flight decides; difference not chased further.
