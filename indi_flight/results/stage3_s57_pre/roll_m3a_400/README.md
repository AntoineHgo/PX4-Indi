# S56: roll M3a at 400 Hz controller rate (defaults ACT_TC 0.05, lead 1, firmware 296766019a)

`run_all.sh`, `roll400.params` (S52 lead1 set with ACT_TC 0.050), `--rate-hz 400`, hover_long, speed 4, AMP 0.001,
bins 1-60 Hz, TP 10, model-only path, MC_ROLL_P as S52 (P8 per S52 README, not in the params file: UNVERIFIED).
Logged rates checked (`roll400_s1_rates.txt`): vehicle_angular_velocity, actuator_motors, vehicle_torque_setpoint
400.0 Hz, dt p1/p99 2.5 ms; gyro 800 Hz. Margins with `m3a_margins_pretest.py csv 1 60 10 400` (fs arg added S56).

| seed | pre-inj gate (--delay 4 --length 15) | bins | f_c [Hz] | PM [deg] | GM [dB] | DM [ms] | Ms [dB] |
|---|---|---|---|---|---|---|---|
| 1 | PASS (RMS 0.0027/0.0029/0.0004) | 18/18 | 4.01 | 84.4 | 10.6 | 58 | 3.8 |
| 2 | PASS (RMS 0.0027/0.0035/0.0004) | 18/18 | 4.00 | 84.4 | 10.4 | 59 | 3.9 |

`roll400_s*_gate.md` say FAIL: they were run over the whole flight, injection included (roll RMS 0.19); the same
artefact is in S52 `lead1_s1_gate.md`. The pre-injection files are the gate.
Reference 800 Hz, same ACT_TC 0.05 (S53 act_tc_sweep x1.5): PM 86 / GM 11.3. At 400 Hz GM drops ~0.8 dB, PM ~2 deg.
G2 thresholds (GM 6 dB, PM 45 deg) met on this break; DM 58 ms vs 2 periods + telemetry latency (5 ms + latency) met.
Single key: the FRF script is the S40-keyed one, only the sample-rate argument is new.
