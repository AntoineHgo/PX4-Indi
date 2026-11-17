# S50 second key: lead sweep with unmodelled plant delay

Script: `bench/lead_sweep_key2_s50.py` (numpy only; scipy not installed). Own frequency-domain model, G1 = 1.
Plant tau 0.033; lead rows use tau_c = 0.033 (matched), P_att 8, no-lead rows ACT_TC = 0.033, K_R 20.
d = extra pure plant delay the controller does not model.

## Modelling choices
- L = X Pl - Fm, i.e. 1 + L = 0 for the loop closed on the torque setpoint u (model state fed by the same u).
  X = K (P/s + Hg) + (1 + c) D, c = K tau_c (lead) or 0. Pl = ZOH * e^{-sd} / ((tau s + 1) s).
- Attitude loop: rate_sp = -P w/s, continuous integrator, no attitude-estimate lag. Rate error uses LPF2p-filtered gyro.
- Filters: gyro LPF2p 40 Hz (bilinear Butterworth); D-term alpha filter 30 Hz (mid of 20/30/50); a_f = alpha * (1 - z^-1)/T * LPF2p.
- Torque model t_f = alpha * LPF2p * exact discrete lag(tau_c) * z^-1 (one sample delay), same H as a_f.
- Plant has ZOH on the command at the loop rate; no other latency besides d. Sample rate = loop rate (400 or 800 Hz).
- Crossover = first downward |L| = 1 on a 0.2 Hz .. 0.45 fs grid; GM at first -180 deg crossing above f_c; DM = PM / (360 f_c).

## Table
| case | rate Hz | K_R | d ms | PM deg | f_c Hz | GM dB | DM ms |
|---|---|---|---|---|---|---|---|
| no lead | 800 | 20 | 0 | 29.2 | 3.01 | 16.8 | 26.9 |
| no lead | 800 | 20 | 2.5 | 26.7 | 3.10 | 10.6 | 23.9 |
| no lead | 800 | 20 | 5 | 24.0 | 3.19 | 7.8 | 20.9 |
| lead | 400 | 20 | 2.5 | 58.0 | 3.13 | 13.2 | 51.5 |
| lead | 400 | 20 | 5 | 54.7 | 3.27 | 9.6 | 46.5 |
| lead | 400 | 30 | 2.5 | 57.4 | 4.90 | 10.2 | 32.6 |
| lead | 400 | 30 | 5 | 50.0 | 5.16 | 7.0 | 27.0 |
| lead | 400 | 40 | 2.5 | 50.2 | 6.76 | 7.9 | 20.6 |
| lead | 400 | 40 | 5 | 39.7 | 7.08 | 5.1 | 15.6 |
| lead | 800 | 20 | 2.5 | 58.6 | 3.15 | 13.0 | 51.8 |
| lead | 800 | 20 | 5 | 55.4 | 3.29 | 9.4 | 46.7 |
| lead | 800 | 30 | 2.5 | 58.3 | 4.92 | 10.2 | 32.9 |
| lead | 800 | 30 | 5 | 51.0 | 5.19 | 7.0 | 27.3 |
| lead | 800 | 40 | 2.5 | 51.6 | 6.79 | 8.1 | 21.1 |
| lead | 800 | 40 | 5 | 41.1 | 7.13 | 5.2 | 16.0 |

## Comparison with key 1 (S49 `results/stage2_s49/lead_delay_README.md`), written by the orchestrator S50

| case | key 1 PM/GM | key 2 PM/GM |
|---|---|---|
| no lead 800 K20 d0 | 28.6/14.2 | 29.2/16.8 |
| no lead 800 K20 d2.5 | 26.1/9.7 | 26.7/10.6 |
| no lead 800 K20 d5 | 23.5/7.2 | 24.0/7.8 |
| lead 800 K20 d2.5 | 57.8/11.4 | 58.6/13.0 |
| lead 400 K20 d2.5 | 57.0/10.5 | 58.0/13.2 |
| lead 400 K30 d2.5 | 52.8/8.1 | 57.4/10.2 |
| lead 400 K40 d2.5 | 42.7/6.2 | 50.2/7.9 |
| lead 400 K20 d5 | 53.3/7.8 | 54.7/9.6 |

Verdict: AGREE on the decision (K_R 20 with lead passes the stop rule PM >= 50, GM >= 8 dB at 400 Hz with the
calibrated 2.5 ms; PM within 1.4 deg, f_c and DM within 2 %). DISAGREE in GM (key 2 is 0.6-2.7 dB higher, as T101
found for the no-lead loop: flights sided with key 1) and in PM at K30-40 (key 2 4.6-7.5 deg higher; crossover 5-7 Hz,
where key 2's free choice of the 30 Hz D-term filter and its one-sample model delay matter). Both keys trigger the stop
rule at K40 in GM. Key 1 alone triggers it at K20 with 5 ms delay (GM 7.8 vs 9.6). Consequence: lead stays the
candidate with K_R 20; K_R above 20 is not supported by the models; the 400 Hz delay is measured by flight before the
lead flight (unchanged plan).
