# S57: roll M3a at 800/3 Hz controller rate, re-fly with MC_INDI_INJ_TP 7.5 (replaces the invalid S56 set)

`run_all.sh`, `roll267b.params` = S56 `roll267.params` with TP 10 -> 7.5 (2000 samples at 266.667 Hz; TP 15 would overrun the
60 s hover_long hold with DLY 20 + 3 periods). Firmware 296766019a (unchanged since the SITL build), hover_long, speed 4,
AMP 0.001, bins 1-60 Hz, model-only path, defaults ACT_TC 0.05, lead 1. Margins `m3a_margins_pretest.py csv 1 60 7.5 266.6667`.
Logged rates (`*_rates.txt`): vehicle_angular_velocity, actuator_motors, vehicle_torque_setpoint 266.7 Hz, dt p1/p99 3.75 ms.

| seed | pre-inj gate (--delay 4 --length 15) | FRF path | bins | f_c [Hz] | PM [deg] | GM [dB] | DM [ms] | Ms [dB] |
|---|---|---|---|---|---|---|---|---|
| 1 | PASS (RMS 0.0022/0.0032/0.0003) | least squares on actual t (time base dev 0.33 sample) | 18/18 | 4.03 | 83.2 | 10.2 | 57 | 4.0 |
| 2 | PASS (RMS 0.0048/0.0032/0.0004) | period-exact FFT (dev 0.0007 sample) | 18/18 | 4.11 | 83.6 | 10.0 | 57 | 4.1 |

Why S56 seed 1 "passed the integer check": it did not reach it. Its logged times deviate 0.33 sample from a uniform grid
(dt 2.5-5 ms jitter in a few samples), so `frf_periodic` took the least-squares phasor path on actual times, which does not
need fs*Tp integer. Not a rounding hole. The same happens here on seed 1, and both paths agree within 0.4 deg PM and
0.2 dB GM (seed 2 FFT vs seed 1 LS), which is a cross-check of the two FRF paths on flight data. S56 seed 1 (TP 10, LS path)
PM 84.0 / GM 10.0 also agrees.

Rate trend, roll M3a, model-only path, ACT_TC 0.05, lead 1 (G2 thresholds GM 6 dB, PM 45 deg):
| controller rate | PM [deg] | GM [dB] | DM [ms] | Ms [dB] | source |
|---|---|---|---|---|---|
| 800 Hz | 86 | 11.3 | - | - | S53 act_tc_sweep x1.5 |
| 400 Hz | 84.4 | 10.5 | 58 | 3.9 | `results/stage3_s57_pre/roll_m3a_400/` |
| 267 Hz | 83.4 | 10.1 | 57 | 4.1 | this set |
DM 57 ms against 2 periods (7.5 ms) + telemetry latency: met. Single key: FRF script S40-keyed, only fs/Tp arguments new.
